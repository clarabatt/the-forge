from urllib.parse import parse_qs, urlparse

import httpx
import respx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database.models import OAuthState, User


def test_google_login_redirects_to_google(client: TestClient):
    resp = client.get("/auth/google/login", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert "accounts.google.com/o/oauth2/v2/auth" in resp.headers["location"]


def test_google_login_saves_state_to_db(client: TestClient, session: Session):
    resp = client.get("/auth/google/login", follow_redirects=False)

    location = resp.headers["location"]
    state_in_url = parse_qs(urlparse(location).query)["state"][0]

    session.expire_all()
    saved = session.exec(select(OAuthState).where(OAuthState.state == state_in_url)).first()
    assert saved is not None


@respx.mock
def test_google_callback_creates_new_user(client: TestClient, session: Session, OAuthStateFactory):
    oauth_state = OAuthStateFactory()

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "test-access-token"})
    )
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "sub": "google-sub-new-123",
                "email": "newuser@example.com",
                "name": "New User",
                "picture": "https://example.com/pic.jpg",
            },
        )
    )

    resp = client.get(
        f"/auth/google/callback?code=authcode&state={oauth_state.state}",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 307)
    assert "session" in resp.cookies

    session.expire_all()
    user = session.exec(select(User).where(User.email == "newuser@example.com")).first()
    assert user is not None
    assert user.google_sub == "google-sub-new-123"
    assert user.full_name == "New User"


@respx.mock
def test_google_callback_updates_existing_user(client: TestClient, session: Session, UserFactory, OAuthStateFactory):
    existing_user = UserFactory(google_sub="google-sub-existing", email="existing@example.com")
    oauth_state = OAuthStateFactory()

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "test-access-token"})
    )
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "sub": "google-sub-existing",
                "email": "existing@example.com",
                "name": "Updated Name",
            },
        )
    )

    resp = client.get(
        f"/auth/google/callback?code=authcode&state={oauth_state.state}",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 307)

    session.expire_all()
    users = session.exec(select(User)).all()
    assert len(users) == 1
    assert users[0].id == existing_user.id
    assert users[0].full_name == "Updated Name"


def test_google_callback_rejects_invalid_state(client: TestClient):
    resp = client.get(
        "/auth/google/callback?code=authcode&state=invalid-state",
        follow_redirects=False,
    )

    assert resp.status_code == 400
    assert "Invalid or expired" in resp.json()["detail"]


@respx.mock
def test_google_callback_deletes_state_after_use(client: TestClient, session: Session, OAuthStateFactory):
    oauth_state = OAuthStateFactory()

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(
            200,
            json={"sub": "sub-xyz", "email": "x@example.com", "name": "X"},
        )
    )

    client.get(
        f"/auth/google/callback?code=code&state={oauth_state.state}",
        follow_redirects=False,
    )

    session.expire_all()
    remaining = session.exec(select(OAuthState).where(OAuthState.state == oauth_state.state)).first()
    assert remaining is None


def test_logout_clears_session_cookie(client: TestClient):
    resp = client.post("/auth/logout", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert resp.cookies.get("session") is None or resp.headers.get("set-cookie", "").startswith("session=;")
