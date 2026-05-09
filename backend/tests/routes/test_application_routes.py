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


def test_retry_application_unauthenticated_returns_401(client: TestClient):
    resp = client.post(f"/api/applications/{uuid.uuid4()}/retry")

    assert resp.status_code == 401


def test_retry_application_not_found_returns_404(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.post(
        f"/api/applications/{uuid.uuid4()}/retry",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_retry_application_non_failed_returns_409(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    from backend.database.models import PipelineStatus

    user = UserFactory()
    app = ApplicationFactory(user_id=user.id, status=PipelineStatus.READY)

    resp = client.post(
        f"/api/applications/{app.id}/retry",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 409


# --- Reanalyze ---

def test_reanalyze_unauthenticated_returns_401(client: TestClient):
    resp = client.post(
        f"/api/applications/{uuid.uuid4()}/reanalyze",
        json={"base_resume_id": str(uuid.uuid4())},
    )

    assert resp.status_code == 401


def test_reanalyze_application_not_found_returns_404(
    client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.post(
        f"/api/applications/{uuid.uuid4()}/reanalyze",
        json={"base_resume_id": str(resume.id)},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_reanalyze_other_users_application_returns_404(
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    other_app = ApplicationFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.post(
        f"/api/applications/{other_app.id}/reanalyze",
        json={"base_resume_id": str(resume.id)},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_reanalyze_resume_not_found_returns_404(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)

    resp = client.post(
        f"/api/applications/{app.id}/reanalyze",
        json={"base_resume_id": str(uuid.uuid4())},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_reanalyze_other_users_resume_returns_404(
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    other_resume = ResumeFactory()  # belongs to a different user

    resp = client.post(
        f"/api/applications/{app.id}/reanalyze",
        json={"base_resume_id": str(other_resume.id)},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_reanalyze_resets_pipeline_state(
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    from unittest.mock import patch
    from backend.database.models import PipelineStatus

    user = UserFactory()
    old_resume = ResumeFactory(user_id=user.id)
    new_resume = ResumeFactory(user_id=user.id)
    app = ApplicationFactory(
        user_id=user.id,
        status=PipelineStatus.READY,
        base_resume_id=old_resume.id,
        company_name="Acme",
        job_title="Engineer",
    )

    with patch("backend.routers.applications._run_pipeline"):
        resp = client.post(
            f"/api/applications/{app.id}/reanalyze",
            json={"base_resume_id": str(new_resume.id)},
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == PipelineStatus.UPLOADED
    assert body["base_resume_id"] == str(new_resume.id)
    assert body["company_name"] == "Analyzing…"
    assert body["job_title"] == "Analyzing…"
    assert body["analysis_feedback"] is None


def test_reanalyze_clears_skills(
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, SkillFactory, session_cookie
):
    from unittest.mock import patch

    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)
    SkillFactory(application_id=app.id)
    SkillFactory(application_id=app.id)

    with patch("backend.routers.applications._run_pipeline"):
        resp = client.post(
            f"/api/applications/{app.id}/reanalyze",
            json={"base_resume_id": str(resume.id)},
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200

    skills_resp = client.get(
        f"/api/applications/{app.id}/skills",
        cookies={"session": session_cookie(str(user.id))},
    )
    assert skills_resp.json() == []


def test_reanalyze_clears_cover_letter(
    client: TestClient,
    UserFactory,
    ApplicationFactory,
    ResumeFactory,
    CoverLetterFactory,
    session_cookie,
):
    from unittest.mock import patch

    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)
    CoverLetterFactory(application_id=app.id)

    with patch("backend.routers.applications._run_pipeline"):
        resp = client.post(
            f"/api/applications/{app.id}/reanalyze",
            json={"base_resume_id": str(resume.id)},
            cookies={"session": session_cookie(str(user.id))},
        )

    assert resp.status_code == 200

    cl_resp = client.get(
        f"/api/applications/{app.id}/cover-letter",
        cookies={"session": session_cookie(str(user.id))},
    )
    assert cl_resp.status_code == 404


def test_stream_application_returns_sse_response(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    from backend.database.models import PipelineStatus

    user = UserFactory()
    # terminal status so the generator emits once and closes immediately
    app = ApplicationFactory(user_id=user.id, status=PipelineStatus.READY)

    resp = client.get(
        f"/api/applications/{app.id}/stream",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "status_changed" in resp.text
