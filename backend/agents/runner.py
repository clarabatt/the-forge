"""Agent pipeline runner.

In production this runs as a Cloud Run Job triggered by Cloud Tasks.
In dev (DEV_MODE=true) it runs as a FastAPI BackgroundTask.
"""

import asyncio
import json
import logging
import re
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from sqlmodel import Session

from backend.agents import cover_letter_agent, feedback_agent, jd_agent, resume_agent
from backend.config import settings
from backend.database.models import (
    AgentName,
    Application,
    CoverLetter,
    LlmUsageLog,
    PipelineStatus,
    Skill,
    SkillMatchStatus,
)
from backend.database.session import engine

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


def _transition(session: Session, app: Application, status: PipelineStatus, **kwargs) -> None:
    app.status = status
    for k, v in kwargs.items():
        setattr(app, k, v)
    session.add(app)
    session.commit()
    session.refresh(app)
    logger.info("application %s → %s", app.id, status)


def _log_usage(
    session: Session,
    app: Application,
    agent_name: AgentName,
    usage: dict,
) -> None:
    log = LlmUsageLog(
        user_id=app.user_id,
        application_id=app.id,
        agent_name=agent_name,
        model=settings.gemini_model,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
    )
    session.add(log)
    session.commit()


MATCH_CONFIDENCE_THRESHOLD = 0.65


def _skill_confidence(jd_name: str, detected_counts: dict[str, int]) -> float:
    """Confidence score [0, 1] that jd_name is genuinely present in the resume.

    Combines match quality (exact > token > substring) with frequency across
    resume blocks. Short/generic substring hits need multiple occurrences to
    cross the threshold; exact and token-level matches pass with a single mention.
    """
    lower = jd_name.lower()

    if lower in detected_counts:
        return min(1.0, 0.85 + 0.05 * (detected_counts[lower] - 1))

    jd_tokens = {t for t in re.split(r"[\s/()\-,./&]+", lower) if len(t) > 2}
    best = 0.0

    for d, freq in detected_counts.items():
        if not d or d not in lower:
            continue
        freq_boost = min(0.15, 0.05 * (freq - 1))
        if d in jd_tokens:
            base = 0.72  # standalone token inside JD name — solid evidence
        elif len(d) >= 5:
            base = 0.62  # long substring not a standalone token — decent evidence
        else:
            base = 0.42  # short substring, likely coincidental without frequency
        best = max(best, min(1.0, base + freq_boost))

    # Multi-token collective coverage: several JD tokens all appear in resume
    if jd_tokens:
        matched = {t: detected_counts[t] for t in jd_tokens if t in detected_counts}
        if matched:
            ratio = len(matched) / len(jd_tokens)
            max_freq = max(matched.values())
            freq_boost = min(0.15, 0.05 * (max_freq - 1))
            base = 0.48 + 0.32 * ratio  # all tokens → 0.80, half → 0.64, one-third → 0.59
            best = max(best, min(1.0, base + freq_boost))

    return best


def _skill_matched(jd_name: str, detected: set[str]) -> bool:
    """Return True if jd_name matches the detected skill set with sufficient confidence."""
    return _skill_confidence(jd_name, {s: 1 for s in detected}) >= MATCH_CONFIDENCE_THRESHOLD


def _build_skills(
    app_id: uuid.UUID,
    jd_skills: list[dict],
    resume_blocks: list[dict],
) -> list[Skill]:
    # Count how many distinct blocks mention each skill — more blocks = higher confidence
    detected_counts: Counter = Counter(
        s.lower()
        for block in resume_blocks
        for s in block.get("skills_detected", [])
    )

    skills = []
    for item in jd_skills:
        name = item.get("name", "")
        found = _skill_confidence(name, detected_counts) >= MATCH_CONFIDENCE_THRESHOLD
        skills.append(
            Skill(
                application_id=app_id,
                skill_name=name,
                category=item.get("category", "Hard Skill"),
                match_status=SkillMatchStatus.found_in_resume if found else SkillMatchStatus.missing,
                ai_confidence=float(item.get("confidence", 0.5)),
                rank=int(item.get("rank", 99)),
            )
        )
    return skills


def run_pipeline(application_id: uuid.UUID) -> None:
    """Entry point — run JD + Resume agents then transition to PENDING_APPROVAL."""
    with Session(engine) as session:
        app = session.get(Application, application_id)
        if not app:
            logger.error("application %s not found", application_id)
            return

        resume = session.get(
            __import__("backend.database.models", fromlist=["Resume"]).Resume,
            app.base_resume_id,
        )
        raw_text = (resume.raw_text or "") if resume else ""
        job_description = app.job_description or ""

        try:
            _transition(session, app, PipelineStatus.ANALYZING)

            # run both agents in parallel via threads (Gemini SDK is sync)
            loop = asyncio.new_event_loop()
            jd_future = _executor.submit(jd_agent.run, job_description)
            resume_future = _executor.submit(resume_agent.run, raw_text)

            jd_result = jd_future.result(timeout=120)
            resume_result = resume_future.result(timeout=120)
            loop.close()

            # update application metadata extracted from JD
            app.company_name = jd_result["company_name"]
            app.job_title = jd_result["job_title"]

            # persist skills
            skills = _build_skills(app.id, jd_result["skills"], resume_result["blocks"])
            for skill in skills:
                session.add(skill)

            # feedback agent — runs after both, uses combined output
            feedback_result = feedback_agent.run(
                company_name=jd_result["company_name"],
                job_title=jd_result["job_title"],
                skills=jd_result["skills"],
                resume_blocks=resume_result["blocks"],
            )
            app.analysis_feedback = json.dumps({
                "overall_assessment": feedback_result["overall_assessment"],
                "strong_points": feedback_result["strong_points"],
                "weak_points": feedback_result["weak_points"],
                "recommended_changes": feedback_result["recommended_changes"],
            })

            # cover letter agent — uses feedback strong points + skills + resume blocks
            cl_result = cover_letter_agent.run(
                company_name=jd_result["company_name"],
                job_title=jd_result["job_title"],
                skills=jd_result["skills"],
                resume_blocks=resume_result["blocks"],
                feedback=feedback_result,
            )
            cover_letter = CoverLetter(
                application_id=app.id,
                content=cl_result["content"],
                questions=json.dumps(cl_result["questions"]),
            )
            session.add(cover_letter)

            # log usage
            _log_usage(session, app, AgentName.JD, jd_result["usage"])
            _log_usage(session, app, AgentName.RESUME, resume_result["usage"])
            _log_usage(session, app, AgentName.DIFF, feedback_result["usage"])
            _log_usage(session, app, AgentName.COVER_LETTER, cl_result["usage"])

            _transition(session, app, PipelineStatus.PENDING_APPROVAL)

        except Exception as exc:
            logger.exception("pipeline failed for application %s", application_id)
            _transition(
                session,
                app,
                PipelineStatus.FAILED,
                error_message=str(exc),
            )
