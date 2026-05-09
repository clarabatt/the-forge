import json
from unittest.mock import MagicMock, patch

from sqlmodel import select

from backend.agents.runner import run_pipeline
from backend.database.models import CoverLetter, LlmUsageLog, PipelineStatus, Skill, SkillMatchStatus

_JD_RESULT = {
    "company_name": "Test Corp",
    "job_title": "Software Engineer",
    "skills": [
        {"name": "Python", "category": "Hard Skill", "confidence": 0.9, "rank": 1, "required": True}
    ],
    "usage": {"input_tokens": 10, "output_tokens": 5},
}
_RESUME_RESULT = {
    "blocks": [
        # No skills_detected so the confidence-matching path marks skills as missing
        # and the skill verifier is skipped (no SKILL_VERIFIER enum insert needed)
        {"type": "accomplishment", "text": "Built backend services", "skills_detected": []}
    ],
    "usage": {"input_tokens": 20, "output_tokens": 10},
}
_VERIFY_RESULT = {
    "verifications": [{"skill_name": "Python", "verified": True, "reason": "Explicitly listed"}],
    "usage": {"input_tokens": 5, "output_tokens": 3},
}
_FEEDBACK_RESULT = {
    "overall_assessment": "Strong candidate.",
    "strong_points": ["Python expertise"],
    "weak_points": [],
    "recommended_changes": [],
    "usage": {"input_tokens": 15, "output_tokens": 8},
}
_CL_RESULT = {
    "content": "Opening paragraph. Body. Closing.",
    "questions": ["What metrics can you add?"],
    "usage": {"input_tokens": 25, "output_tokens": 50},
}


def _mock_session_ctx(test_session):
    """Wrap test_session so `with Session(engine) as s` uses it."""
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=test_session)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def test_run_pipeline_transitions_to_ready(session, ApplicationFactory, ResumeFactory):
    resume = ResumeFactory(raw_text="Python developer")
    app = ApplicationFactory(user_id=resume.user_id, base_resume_id=resume.id)

    with (
        patch("backend.agents.runner.Session") as MockSession,
        patch("backend.agents.runner.jd_agent.run", return_value=_JD_RESULT),
        patch("backend.agents.runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.runner.skill_verifier_agent.run", return_value=_VERIFY_RESULT),
        patch("backend.agents.runner.feedback_agent.run", return_value=_FEEDBACK_RESULT),
        patch("backend.agents.runner.cover_letter_agent.run", return_value=_CL_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_pipeline(app.id)

    session.refresh(app)
    assert app.status == PipelineStatus.READY
    assert app.company_name == "Test Corp"
    assert app.job_title == "Software Engineer"
    assert app.analysis_feedback is not None
    feedback = json.loads(app.analysis_feedback)
    assert feedback["overall_assessment"] == "Strong candidate."


def test_run_pipeline_saves_skills_and_cover_letter(session, ApplicationFactory, ResumeFactory):
    resume = ResumeFactory(raw_text="Python developer")
    app = ApplicationFactory(user_id=resume.user_id, base_resume_id=resume.id)

    with (
        patch("backend.agents.runner.Session") as MockSession,
        patch("backend.agents.runner.jd_agent.run", return_value=_JD_RESULT),
        patch("backend.agents.runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.runner.skill_verifier_agent.run", return_value=_VERIFY_RESULT),
        patch("backend.agents.runner.feedback_agent.run", return_value=_FEEDBACK_RESULT),
        patch("backend.agents.runner.cover_letter_agent.run", return_value=_CL_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_pipeline(app.id)

    skills = session.exec(select(Skill).where(Skill.application_id == app.id)).all()
    assert len(skills) == 1
    assert skills[0].skill_name == "Python"
    assert skills[0].match_status == SkillMatchStatus.missing  # no detected skills in blocks

    cl = session.exec(select(CoverLetter).where(CoverLetter.application_id == app.id)).first()
    assert cl is not None
    assert cl.content == "Opening paragraph. Body. Closing."
    assert cl.questions is not None


def test_run_pipeline_logs_llm_usage(session, ApplicationFactory, ResumeFactory):
    resume = ResumeFactory(raw_text="Python developer")
    app = ApplicationFactory(user_id=resume.user_id, base_resume_id=resume.id)

    with (
        patch("backend.agents.runner.Session") as MockSession,
        patch("backend.agents.runner.jd_agent.run", return_value=_JD_RESULT),
        patch("backend.agents.runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.runner.skill_verifier_agent.run", return_value=_VERIFY_RESULT),
        patch("backend.agents.runner.feedback_agent.run", return_value=_FEEDBACK_RESULT),
        patch("backend.agents.runner.cover_letter_agent.run", return_value=_CL_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_pipeline(app.id)

    logs = session.exec(select(LlmUsageLog).where(LlmUsageLog.application_id == app.id)).all()
    agent_names = {log.agent_name for log in logs}
    from backend.database.models import AgentName
    # JD, Resume, Feedback, CoverLetter are always logged (verifier skipped when no matches)
    assert AgentName.JD in agent_names
    assert AgentName.RESUME in agent_names
    assert AgentName.COVER_LETTER in agent_names


def test_run_pipeline_transitions_to_failed_on_exception(session, ApplicationFactory, ResumeFactory):
    resume = ResumeFactory(raw_text="Python developer")
    app = ApplicationFactory(user_id=resume.user_id, base_resume_id=resume.id)

    with (
        patch("backend.agents.runner.Session") as MockSession,
        patch("backend.agents.runner.jd_agent.run", side_effect=Exception("Gemini is down")),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_pipeline(app.id)

    session.refresh(app)
    assert app.status == PipelineStatus.FAILED
    assert "Gemini is down" in app.error_message
