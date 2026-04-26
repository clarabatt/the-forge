from fastapi.testclient import TestClient


def test_get_me_unauthenticated_returns_401(client: TestClient):
    resp = client.get("/api/users/me")

    assert resp.status_code == 401


def test_get_me_with_invalid_token_returns_401(client: TestClient):
    resp = client.get("/api/users/me", cookies={"session": "not-a-valid-token"})

    assert resp.status_code == 401


def test_get_me_returns_current_user(client: TestClient, UserFactory, session_cookie):
    user = UserFactory(email="me@example.com", full_name="Clara Test")

    resp = client.get(
        "/api/users/me",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    data = resp.json()["user"]
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Clara Test"
    assert data["id"] == str(user.id)


def test_get_me_inactive_user_returns_401(client: TestClient, UserFactory, session_cookie):
    user = UserFactory(is_active=False)

    resp = client.get(
        "/api/users/me",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 401
