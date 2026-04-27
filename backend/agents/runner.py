"""Agent pipeline runner.

In production this runs as a Cloud Run Job triggered by Cloud Tasks.
In dev (DEV_MODE=true) it runs as a FastAPI BackgroundTask.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlmodel import Session

from backend.agents import jd_agent, resume_agent
from backend.config import settings
from backend.database.models import (
    AgentName,
    Application,
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


def _build_skills(
    app_id: uuid.UUID,
    jd_skills: list[dict],
    resume_blocks: list[dict],
) -> list[Skill]:
    detected_names = {
        s.lower()
        for block in resume_blocks
        for s in block.get("skills_detected", [])
    }

    skills = []
    for item in jd_skills:
        name = item.get("name", "")
        found = name.lower() in detected_names
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

            # log usage
            _log_usage(session, app, AgentName.JD, jd_result["usage"])
            _log_usage(session, app, AgentName.RESUME, resume_result["usage"])

            _transition(session, app, PipelineStatus.PENDING_APPROVAL)

        except Exception as exc:
            logger.exception("pipeline failed for application %s", application_id)
            _transition(
                session,
                app,
                PipelineStatus.FAILED,
                error_message=str(exc),
            )
