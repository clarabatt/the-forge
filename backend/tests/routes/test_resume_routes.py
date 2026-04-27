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
