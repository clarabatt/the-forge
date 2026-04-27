from fastapi.testclient import TestClient


def test_list_resumes_unauthenticated_returns_401(client: TestClient):
    resp = client.get("/api/resumes/")

    assert resp.status_code == 401


def test_list_resumes_returns_empty_when_none(client: TestClient, UserFactory, session_cookie):
    user = UserFactory()

    resp = client.get("/api/resumes/", cookies={"session": session_cookie(str(user.id))})

    assert resp.status_code == 200
    assert resp.json() == []


def test_list_resumes_returns_only_current_users_resumes(
    client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    ResumeFactory(user_id=user.id)
    ResumeFactory(user_id=user.id)
    ResumeFactory()  # another user's resume

    resp = client.get("/api/resumes/", cookies={"session": session_cookie(str(user.id))})

    assert resp.status_code == 200
    assert len(resp.json()) == 2
