import pytest
from fastapi.testclient import TestClient

from backend.config import settings

pytestmark = pytest.mark.skipif(not settings.dev_mode, reason="DEV_MODE not enabled")

DEV_EMAIL = "dev@theforge.local"


def test_dev_login_returns_404_when_seed_user_missing(client: TestClient):
    resp = client.post("/api/dev/login")

    assert resp.status_code == 404
    assert "seed" in resp.json()["detail"].lower()


def test_dev_login_returns_200_and_sets_cookie(client: TestClient, UserFactory):
    UserFactory(email=DEV_EMAIL)

    resp = client.post("/api/dev/login")

    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "user": DEV_EMAIL}
    assert "session" in resp.cookies


def test_dev_login_cookie_authenticates_as_dev_user(client: TestClient, UserFactory):
    UserFactory(email=DEV_EMAIL, full_name="Dev User")

    login = client.post("/api/dev/login")
    assert login.status_code == 200

    me = client.get("/api/users/me", cookies={"session": login.cookies["session"]})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == DEV_EMAIL
