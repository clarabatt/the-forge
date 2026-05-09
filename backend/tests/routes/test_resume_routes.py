import io
from unittest.mock import patch

from fastapi.testclient import TestClient

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

# Minimal valid .docx bytes (a real docx is a zip; for unit tests we mock GCS
# and text extraction, so any bytes are fine as long as the filename ends in .docx)
_FAKE_DOCX = b"PK\x03\x04fake-docx-content"


def _docx_file(filename: str = "my_resume.docx") -> tuple:
    return (filename, io.BytesIO(_FAKE_DOCX), DOCX_CONTENT_TYPE)


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


def test_upload_resume_unauthenticated_returns_401(client: TestClient):
    resp = client.post("/api/resumes/", files={"file": _docx_file()})

    assert resp.status_code == 401


def test_upload_resume_rejects_non_docx(client: TestClient, UserFactory, session_cookie):
    user = UserFactory()

    resp = client.post(
        "/api/resumes/",
        files={"file": ("resume.pdf", io.BytesIO(b"pdf content"), "application/pdf")},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 422
    assert "docx" in resp.json()["detail"].lower()


@patch("backend.routers.resumes.upload_bytes", return_value="resumes/fake/key.docx")
@patch("backend.routers.resumes._extract_text", return_value="Extracted resume text")
def test_upload_resume_creates_db_row(mock_extract, mock_upload, client: TestClient, UserFactory, session_cookie):
    user = UserFactory()

    resp = client.post(
        "/api/resumes/",
        files={"file": _docx_file("cv.docx")},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["file_name"] == "cv.docx"
    assert body["resume_type"] == "BASE"
    assert body["is_latest"] is True
    assert body["version_number"] == 1
    assert body["raw_text"] == "Extracted resume text"
    mock_upload.assert_called_once()


@patch("backend.routers.resumes.upload_bytes", return_value="resumes/fake/key.docx")
@patch("backend.routers.resumes._extract_text", return_value="New text")
def test_upload_resume_increments_version_and_demotes_previous(
    mock_extract, mock_upload, client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    ResumeFactory(user_id=user.id, is_latest=True, version_number=1)

    resp = client.post(
        "/api/resumes/",
        files={"file": _docx_file("cv_v2.docx")},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["version_number"] == 2
    assert body["is_latest"] is True

    # previous resume must no longer be latest
    list_resp = client.get(
        "/api/resumes/",
        cookies={"session": session_cookie(str(user.id))},
    )
    resumes = list_resp.json()
    assert len(resumes) == 2
    latest_count = sum(1 for r in resumes if r["is_latest"])
    assert latest_count == 1


# --- PATCH (rename) ---

def test_rename_resume_unauthenticated_returns_401(client: TestClient, UserFactory, ResumeFactory):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.patch(f"/api/resumes/{resume.id}", json={"file_name": "new_name.docx"})

    assert resp.status_code == 401


def test_rename_resume_updates_file_name(client: TestClient, UserFactory, ResumeFactory, session_cookie):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id, file_name="old.docx")

    resp = client.patch(
        f"/api/resumes/{resume.id}",
        json={"file_name": "new.docx"},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.json()["file_name"] == "new.docx"


def test_rename_resume_not_found_returns_404(client: TestClient, UserFactory, session_cookie):
    import uuid
    user = UserFactory()

    resp = client.patch(
        f"/api/resumes/{uuid.uuid4()}",
        json={"file_name": "x.docx"},
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_rename_resume_of_other_user_returns_404(
    client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    owner = UserFactory()
    other = UserFactory()
    resume = ResumeFactory(user_id=owner.id)

    resp = client.patch(
        f"/api/resumes/{resume.id}",
        json={"file_name": "hacked.docx"},
        cookies={"session": session_cookie(str(other.id))},
    )

    assert resp.status_code == 404


# --- DELETE ---

def test_delete_resume_unauthenticated_returns_401(client: TestClient, UserFactory, ResumeFactory):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.delete(f"/api/resumes/{resume.id}")

    assert resp.status_code == 401


def test_delete_resume_removes_it(client: TestClient, UserFactory, ResumeFactory, session_cookie):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.delete(
        f"/api/resumes/{resume.id}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 204

    list_resp = client.get("/api/resumes/", cookies={"session": session_cookie(str(user.id))})
    assert list_resp.json() == []


def test_delete_resume_not_found_returns_404(client: TestClient, UserFactory, session_cookie):
    import uuid
    user = UserFactory()

    resp = client.delete(
        f"/api/resumes/{uuid.uuid4()}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_delete_resume_of_other_user_returns_404(
    client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    owner = UserFactory()
    other = UserFactory()
    resume = ResumeFactory(user_id=owner.id)

    resp = client.delete(
        f"/api/resumes/{resume.id}",
        cookies={"session": session_cookie(str(other.id))},
    )

    assert resp.status_code == 404
    # resume must still exist
    list_resp = client.get("/api/resumes/", cookies={"session": session_cookie(str(owner.id))})
    assert len(list_resp.json()) == 1


# --- GET /{resume_id}/download ---

def test_download_resume_unauthenticated_returns_401(client: TestClient):
    import uuid
    resp = client.get(f"/api/resumes/{uuid.uuid4()}/download")

    assert resp.status_code == 401


def test_download_resume_not_found_returns_404(
    client: TestClient, UserFactory, session_cookie
):
    import uuid
    user = UserFactory()

    resp = client.get(
        f"/api/resumes/{uuid.uuid4()}/download",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_download_resume_other_user_returns_404(
    client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    other_resume = ResumeFactory()  # belongs to a different user

    resp = client.get(
        f"/api/resumes/{other_resume.id}/download",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


@patch("backend.routers.resumes.download_bytes", return_value=_FAKE_DOCX)
def test_download_resume_returns_file_bytes(
    mock_dl, client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id, file_name="cv.docx")

    resp = client.get(
        f"/api/resumes/{resume.id}/download",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.content == _FAKE_DOCX
    assert "cv.docx" in resp.headers["content-disposition"]
    mock_dl.assert_called_once_with(resume.bucket_key)


@patch("backend.routers.resumes.download_bytes", side_effect=FileNotFoundError)
def test_download_resume_returns_404_when_file_missing(
    mock_dl, client: TestClient, UserFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)

    resp = client.get(
        f"/api/resumes/{resume.id}/download",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_delete_resume_nulls_base_resume_id_on_applications(
    client: TestClient, UserFactory, ResumeFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)
    ApplicationFactory(user_id=user.id, base_resume_id=resume.id)

    resp = client.delete(
        f"/api/resumes/{resume.id}",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 204
    # resume should be gone
    list_resp = client.get("/api/resumes/", cookies={"session": session_cookie(str(user.id))})
    assert list_resp.json() == []
