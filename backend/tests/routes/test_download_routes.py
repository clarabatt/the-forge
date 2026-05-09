import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

_FAKE_DOCX = b"PK\x03\x04fake-docx-content"
_FAKE_HTML = "<p>Resume content</p>"
_FAKE_PDF = b"%PDF-fake"


# --- Application DOCX download ---

def test_download_app_docx_unauthenticated_returns_401(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}/download/docx")

    assert resp.status_code == 401


def test_download_app_docx_application_not_found_returns_404(
    client: TestClient, UserFactory, session_cookie
):
    user = UserFactory()

    resp = client.get(
        f"/api/applications/{uuid.uuid4()}/download/docx",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


def test_download_app_docx_no_resume_attached_returns_404(
    client: TestClient, UserFactory, ApplicationFactory, session_cookie
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)  # base_resume_id is None by default

    resp = client.get(
        f"/api/applications/{app.id}/download/docx",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


@patch("backend.routers.applications.download_bytes", return_value=_FAKE_DOCX)
def test_download_app_docx_returns_file_bytes(
    mock_dl, client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id, file_name="my_resume.docx")
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)

    resp = client.get(
        f"/api/applications/{app.id}/download/docx",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.content == _FAKE_DOCX
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]
    assert "my_resume.docx" in resp.headers["content-disposition"]
    mock_dl.assert_called_once_with(resume.bucket_key)


@patch("backend.routers.applications.download_bytes", side_effect=FileNotFoundError)
def test_download_app_docx_returns_404_when_file_missing(
    mock_dl, client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)

    resp = client.get(
        f"/api/applications/{app.id}/download/docx",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 404


# --- Application PDF download ---

def test_download_app_pdf_unauthenticated_returns_401(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}/download/pdf")

    assert resp.status_code == 401


@patch("backend.routers.applications.weasyprint.HTML")
@patch("backend.routers.applications.mammoth.convert_to_html")
@patch("backend.routers.applications.download_bytes", return_value=_FAKE_DOCX)
def test_download_app_pdf_returns_pdf_bytes(
    mock_dl, mock_mammoth, mock_weasy,
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    mock_mammoth.return_value.value = _FAKE_HTML
    mock_weasy.return_value.write_pdf.return_value = _FAKE_PDF
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id, file_name="cv.docx")
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)

    resp = client.get(
        f"/api/applications/{app.id}/download/pdf",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.content == _FAKE_PDF
    assert resp.headers["content-type"] == "application/pdf"
    assert "cv.pdf" in resp.headers["content-disposition"]


# --- Application resume-html ---

def test_get_resume_html_unauthenticated_returns_401(client: TestClient):
    resp = client.get(f"/api/applications/{uuid.uuid4()}/resume-html")

    assert resp.status_code == 401


@patch("backend.routers.applications.mammoth.convert_to_html")
@patch("backend.routers.applications.download_bytes", return_value=_FAKE_DOCX)
def test_get_resume_html_returns_html_string(
    mock_dl, mock_mammoth,
    client: TestClient, UserFactory, ApplicationFactory, ResumeFactory, session_cookie
):
    mock_mammoth.return_value.value = _FAKE_HTML
    user = UserFactory()
    resume = ResumeFactory(user_id=user.id)
    app = ApplicationFactory(user_id=user.id, base_resume_id=resume.id)

    resp = client.get(
        f"/api/applications/{app.id}/resume-html",
        cookies={"session": session_cookie(str(user.id))},
    )

    assert resp.status_code == 200
    assert resp.json()["html"] == _FAKE_HTML
