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


# --- GET /me/usage ---

def test_get_usage_unauthenticated_returns_401(client: TestClient):
    resp = client.get("/api/users/me/usage")

    assert resp.status_code == 401


def test_get_usage_returns_zero_when_no_logs(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.get(
        "/api/users/me/usage",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["cost_usd"] == 0.0
    assert body["input_tokens"] == 0
    assert body["output_tokens"] == 0
    assert "monthly_cap_usd" in body


def test_get_usage_aggregates_token_counts(
    client: TestClient, UserFactory, LlmUsageLogFactory, session_cookie
):
    user = UserFactory()
    LlmUsageLogFactory(user_id=user.id, model="gemini-2.5-flash", input_tokens=100, output_tokens=50)
    LlmUsageLogFactory(user_id=user.id, model="gemini-2.5-flash", input_tokens=200, output_tokens=100)
    LlmUsageLogFactory()  # another user's log — must not appear in totals

    resp = client.get(
        "/api/users/me/usage",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["input_tokens"] == 300
    assert body["output_tokens"] == 150
    assert body["cost_usd"] > 0
