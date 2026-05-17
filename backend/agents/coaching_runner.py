"""Coaching runner — runs resume parsing + coaching agent for a single base resume."""

import json
import logging
import time
import uuid

from sqlmodel import Session

from backend.agents import resume_agent, resume_coaching_agent
from backend.config import INFRA_MARKUP_PCT, TAX_RATE, settings
from backend.database.models import AgentName, LlmUsageLog, Resume
from backend.database.session import engine
from backend.pricing import full_cost_breakdown

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3


def _run_with_retry(fn, *args, **kwargs):
    last_exc = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            logger.warning("attempt %d/%d failed: %s", attempt, _MAX_ATTEMPTS, exc)
            if attempt < _MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
    raise last_exc


def run_coaching(resume_id: uuid.UUID) -> None:
    with Session(engine) as session:
        resume = session.get(Resume, resume_id)
        if not resume:
            logger.error("resume %s not found for coaching", resume_id)
            return

        resume.coaching_status = "analyzing"
        session.add(resume)
        session.commit()
        session.refresh(resume)

        try:
            resume_result = _run_with_retry(resume_agent.run, resume.raw_text or "")
            coaching_result = _run_with_retry(resume_coaching_agent.run, resume_result["blocks"])

            resume.coaching_analysis = json.dumps({
                "overall_score": coaching_result["overall_score"],
                "global_issues": coaching_result["global_issues"],
                "summary_feedback": coaching_result["summary_feedback"],
                "skills_feedback": coaching_result["skills_feedback"],
                "experience_blocks": coaching_result["experience_blocks"],
            })
            resume.coaching_status = "done"

            _inp = (
                resume_result["usage"].get("input_tokens", 0)
                + coaching_result["usage"].get("input_tokens", 0)
            )
            _out = (
                resume_result["usage"].get("output_tokens", 0)
                + coaching_result["usage"].get("output_tokens", 0)
            )
            _llm, _infra, _taxes, _total = full_cost_breakdown(
                settings.gemini_model, _inp, _out, INFRA_MARKUP_PCT, TAX_RATE
            )
            session.add(LlmUsageLog(
                user_id=resume.user_id,
                agent_name=AgentName.RESUME_COACHING,
                model=settings.gemini_model,
                input_tokens=_inp,
                output_tokens=_out,
                llm_cost_usd=_llm,
                infra_cost_usd=_infra,
                taxes_cost_usd=_taxes,
                total_cost_usd=_total,
            ))

        except Exception:
            logger.exception("coaching failed for resume %s", resume_id)
            resume.coaching_status = "failed"

        session.add(resume)
        session.commit()
