import uuid

from fastapi.testclient import TestClient


def test_list_applications_unauthenticated_returns_401(client: TestClient):
    resp = client.get("/api/applications/")

    assert resp.status_code == 401


def test_list_applications_returns_empty_when_none(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.get("/api/applications/", cookies={"session": session_cookie(str(user.id))})

    assert resp.status_code == 200
    assert resp.json() == []


def test_list_applications_returns_only_current_users_applications(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    ApplicationFactory(user_id=user.id, company_name="Alpha")
    ApplicationFactory(user_id=user.id, company_name="Beta")
    ApplicationFactory()  # another user's application

    resp = client.get("/api/applications/", cookies={"session": session_cookie(str(user.id))})

    assert resp.status_code == 200
    companies = {a["company_name"] for a in resp.json()}
    assert companies == {"Alpha", "Beta"}


def test_get_application_unauthenticated_returns_401(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}")

    assert resp.status_code == 401


def test_get_application_returns_404_when_not_found(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.get(
        f"/api/applications/{uuid.uuid4()}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Application not found"


def test_get_application_returns_application(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id, company_name="Acme")

    resp = client.get(
        f"/api/applications/{app.id}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(app.id)
    assert body["company_name"] == "Acme"


def test_get_application_returns_404_for_other_users_application(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    other_app = ApplicationFactory()  # belongs to a different user

    resp = client.get(
        f"/api/applications/{other_app.id}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_stream_application_returns_sse_response(client: TestClient, ApplicationFactory):
    app = ApplicationFactory()

    resp = client.get(f"/api/applications/{app.id}/stream")

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
