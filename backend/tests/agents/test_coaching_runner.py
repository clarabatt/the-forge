import json
from unittest.mock import MagicMock, patch

from sqlmodel import select

from backend.agents.coaching_runner import run_coaching
from backend.database.models import AgentName, LlmUsageLog

_RESUME_RESULT = {
    "blocks": [
        {"type": "accomplishment", "text": "Built things.", "employer": "Acme", "date_range": "2022–2024", "skills_detected": []}
    ],
    "usage": {"input_tokens": 20, "output_tokens": 10},
}

_COACHING_RESULT = {
    "overall_score": "decent",
    "global_issues": ["No metrics"],
    "summary_feedback": {"detected_text": None, "issues": ["Missing summary"], "coaching_questions": []},
    "skills_feedback": {"detected_skills": [], "issues": [], "coaching_questions": []},
    "experience_blocks": [],
    "usage": {"input_tokens": 30, "output_tokens": 15},
}


def _mock_session_ctx(test_session):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=test_session)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def test_run_coaching_transitions_to_done(session, ResumeFactory):
    resume = ResumeFactory(raw_text="Built things at Acme.")

    with (
        patch("backend.agents.coaching_runner.Session") as MockSession,
        patch("backend.agents.coaching_runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.coaching_runner.resume_coaching_agent.run", return_value=_COACHING_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_coaching(resume.id)

    session.refresh(resume)
    assert resume.coaching_status == "done"
    assert resume.coaching_analysis is not None
    analysis = json.loads(resume.coaching_analysis)
    assert analysis["overall_score"] == "decent"
    assert analysis["global_issues"] == ["No metrics"]


def test_run_coaching_saves_all_sections(session, ResumeFactory):
    resume = ResumeFactory(raw_text="Some resume text.")

    with (
        patch("backend.agents.coaching_runner.Session") as MockSession,
        patch("backend.agents.coaching_runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.coaching_runner.resume_coaching_agent.run", return_value=_COACHING_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_coaching(resume.id)

    session.refresh(resume)
    analysis = json.loads(resume.coaching_analysis)
    assert "summary_feedback" in analysis
    assert "skills_feedback" in analysis
    assert "experience_blocks" in analysis


def test_run_coaching_logs_llm_usage(session, ResumeFactory):
    resume = ResumeFactory(raw_text="Some resume text.")

    with (
        patch("backend.agents.coaching_runner.Session") as MockSession,
        patch("backend.agents.coaching_runner.resume_agent.run", return_value=_RESUME_RESULT),
        patch("backend.agents.coaching_runner.resume_coaching_agent.run", return_value=_COACHING_RESULT),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_coaching(resume.id)

    logs = session.exec(
        select(LlmUsageLog).where(LlmUsageLog.user_id == resume.user_id)
    ).all()
    assert len(logs) == 1
    assert logs[0].agent_name == AgentName.RESUME_COACHING
    assert logs[0].input_tokens == 50   # 20 + 30
    assert logs[0].output_tokens == 25  # 10 + 15


def test_run_coaching_transitions_to_failed_on_exception(session, ResumeFactory):
    resume = ResumeFactory(raw_text="Some resume text.")

    with (
        patch("backend.agents.coaching_runner.Session") as MockSession,
        patch("backend.agents.coaching_runner.resume_agent.run", side_effect=Exception("Gemini down")),
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_coaching(resume.id)

    session.refresh(resume)
    assert resume.coaching_status == "failed"
    assert resume.coaching_analysis is None


def test_run_coaching_noop_for_missing_resume(session):
    import uuid
    with (
        patch("backend.agents.coaching_runner.Session") as MockSession,
        patch("backend.agents.coaching_runner.resume_agent.run") as mock_agent,
    ):
        MockSession.return_value = _mock_session_ctx(session)
        run_coaching(uuid.uuid4())

    mock_agent.assert_not_called()
