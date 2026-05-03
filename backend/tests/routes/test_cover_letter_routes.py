import uuid

from fastapi.testclient import TestClient


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
