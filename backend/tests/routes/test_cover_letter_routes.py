import json
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.database.models import PipelineStatus


def test_get_cover_letter_unauthenticated_returns_401(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}/cover-letter")

    assert resp.status_code == 401


def test_get_cover_letter_returns_404_when_application_not_found(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.get(
        f"/api/applications/{uuid.uuid4()}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Application not found"


def test_get_cover_letter_returns_404_when_not_yet_generated(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)

    resp = client.get(
        f"/api/applications/{app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Cover letter not yet available"


def test_get_cover_letter_returns_content(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    CoverLetterFactory(application_id=app.id, content="I am the right person for this role.")

    resp = client.get(
        f"/api/applications/{app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == "I am the right person for this role."
    assert "created_at" in body


def test_get_cover_letter_returns_404_for_other_users_application(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    user = UserFactory()
    other_app = ApplicationFactory()  # belongs to a different user
    CoverLetterFactory(application_id=other_app.id)

    resp = client.get(
        f"/api/applications/{other_app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


# --- generate endpoint ---

_MOCK_CL_RESULT = {
    "content": "Generated cover letter content.",
    "questions": [
        "Which project at Acme best demonstrates your Python skills?",
        "Can you quantify an outcome from your last role?",
    ],
    "usage": {"input_tokens": 100, "output_tokens": 200},
}

_FEEDBACK = json.dumps({
    "overall_assessment": "Good fit.",
    "strong_points": ["Strong Python skills"],
    "weak_points": [],
    "recommended_changes": [],
})


def test_generate_cover_letter_unauthenticated_returns_401(client: TestClient):
    resp = client.post(f"/api/applications/{uuid.uuid4()}/cover-letter/generate")

    assert resp.status_code == 401


def test_generate_cover_letter_returns_404_when_application_not_found(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.post(
        f"/api/applications/{uuid.uuid4()}/cover-letter/generate",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_generate_cover_letter_returns_409_when_pipeline_not_complete(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id, status=PipelineStatus.ANALYZING)

    resp = client.post(
        f"/api/applications/{app.id}/cover-letter/generate",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 409


def test_generate_cover_letter_creates_and_returns_content(
    client: TestClient, UserFactory, ApplicationFactory, SkillFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(
        user_id=user.id,
        status=PipelineStatus.PENDING_APPROVAL,
        analysis_feedback=_FEEDBACK,
    )
    SkillFactory(application_id=app.id)

    with patch("backend.routers.applications.cover_letter_agent.run", return_value=_MOCK_CL_RESULT):
        resp = client.post(
            f"/api/applications/{app.id}/cover-letter/generate",
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == "Generated cover letter content."
    assert "created_at" in body


def test_generate_cover_letter_replaces_existing(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(
        user_id=user.id,
        status=PipelineStatus.READY,
        analysis_feedback=_FEEDBACK,
    )
    CoverLetterFactory(application_id=app.id, content="Old content.")

    with patch("backend.routers.applications.cover_letter_agent.run", return_value=_MOCK_CL_RESULT):
        resp = client.post(
            f"/api/applications/{app.id}/cover-letter/generate",
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200
    assert resp.json()["content"] == "Generated cover letter content."


def test_generate_cover_letter_returns_404_for_other_users_application(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    other_app = ApplicationFactory(analysis_feedback=_FEEDBACK)

    resp = client.post(
        f"/api/applications/{other_app.id}/cover-letter/generate",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


# --- questions field ---

def test_generate_cover_letter_returns_questions(
    client: TestClient, UserFactory, ApplicationFactory, SkillFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(
        user_id=user.id,
        status=PipelineStatus.PENDING_APPROVAL,
        analysis_feedback=_FEEDBACK,
    )
    SkillFactory(application_id=app.id)

    with patch("backend.routers.applications.cover_letter_agent.run", return_value=_MOCK_CL_RESULT):
        resp = client.post(
            f"/api/applications/{app.id}/cover-letter/generate",
            cookies={"session": session_cookie(str(user.id))},
        )

    body = resp.json()
    assert resp.status_code == 200
    assert body["questions"] == _MOCK_CL_RESULT["questions"]


def test_get_cover_letter_returns_questions(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    import json as _json
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    questions = ["Which project best shows your Python skills?", "Can you add a metric?"]
    CoverLetterFactory(application_id=app.id, questions=_json.dumps(questions))

    resp = client.get(
        f"/api/applications/{app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.json()["questions"] == questions


def test_get_cover_letter_returns_empty_questions_when_none_stored(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    CoverLetterFactory(application_id=app.id, questions=None)

    resp = client.get(
        f"/api/applications/{app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.json()["questions"] == []


def test_generate_cover_letter_updates_questions_on_regenerate(
    client: TestClient, UserFactory, ApplicationFactory, CoverLetterFactory, session_cookie
):
    import json as _json
    user = UserFactory()
    app = ApplicationFactory(
        user_id=user.id,
        status=PipelineStatus.READY,
        analysis_feedback=_FEEDBACK,
    )
    CoverLetterFactory(
        application_id=app.id,
        content="Old content.",
        questions=_json.dumps(["Old question?"]),
    )

    with patch("backend.routers.applications.cover_letter_agent.run", return_value=_MOCK_CL_RESULT):
        resp = client.post(
            f"/api/applications/{app.id}/cover-letter/generate",
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == "Generated cover letter content."
    assert body["questions"] == _MOCK_CL_RESULT["questions"]
