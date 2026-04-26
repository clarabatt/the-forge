import uuid

from fastapi.testclient import TestClient


def test_list_applications_returns_empty_when_none(client: TestClient):
    resp = client.get("/api/applications/")

    assert resp.status_code == 200
    assert resp.json() == []


def test_list_applications_returns_all_applications(client: TestClient, UserFactory, ApplicationFactory):
    user = UserFactory()
    ApplicationFactory(user_id=user.id, company_name="Alpha")
    ApplicationFactory(user_id=user.id, company_name="Beta")

    resp = client.get("/api/applications/")

    assert resp.status_code == 200
    companies = {a["company_name"] for a in resp.json()}
    assert companies == {"Alpha", "Beta"}


def test_get_application_returns_404_when_not_found(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Application not found"


def test_get_application_returns_application(client: TestClient, ApplicationFactory):
    app = ApplicationFactory(company_name="Acme")

    resp = client.get(f"/api/applications/{app.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(app.id)
    assert body["company_name"] == "Acme"


def test_stream_application_returns_sse_response(client: TestClient, ApplicationFactory):
    app = ApplicationFactory()

    resp = client.get(f"/api/applications/{app.id}/stream")

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
