import asyncio
import io
import json
import uuid
from datetime import datetime
from datetime import timezone
from typing import AsyncGenerator

import mammoth
import weasyprint
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, delete

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import Application, ApplicationStatus, PipelineStatus, Resume, Skill, User
from backend.database.repositories import ApplicationRepository, SkillRepository
from backend.database.session import get_session
from backend.gcs import download_bytes

router = APIRouter()

_RESUME_CSS = """
@page {
  size: Letter;
  margin: 2.5cm 2.8cm;
}
body {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 11pt;
  color: #111;
  line-height: 1.5;
}
p { margin: 0 0 4px; }
p:first-child strong { font-size: 20pt; font-weight: 700; letter-spacing: -0.01em; }
p:nth-child(2) strong { font-size: 12pt; font-weight: 400; color: #444; }
p:nth-child(3) { font-size: 10pt; color: #555; margin-bottom: 18px; }
p > strong:only-child {
  display: block;
  font-size: 10pt;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-bottom: 1.5px solid #111;
  padding-bottom: 2px;
  margin-top: 16px;
  margin-bottom: 6px;
}
h1 { font-size: 11pt; font-weight: 600; margin: 12px 0 0; }
h2 { font-size: 10.5pt; font-weight: 400; margin: 0 0 8px; }
h3 { font-size: 10pt; font-weight: 400; font-style: italic; color: #555; margin: 0 0 4px; }
ul { margin: 4px 0 10px; padding-left: 18px; }
li { font-size: 10.5pt; line-height: 1.55; margin-bottom: 3px; }
"""


class CreateApplicationRequest(BaseModel):
    job_description: str
    base_resume_id: uuid.UUID


@router.get("/")
def list_applications(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ApplicationRepository(session)
    return repo.list_by_user(user.id)


@router.post("/", status_code=201)
def create_application(
    body: CreateApplicationRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    app = Application(
        user_id=user.id,
        job_description=body.job_description,
        # placeholders — JD Agent fills these in
        company_name="Analyzing…",
        job_title="Analyzing…",
        status=PipelineStatus.UPLOADED,
        application_status=ApplicationStatus.applied,
        base_resume_id=body.base_resume_id,
        template_version=settings.current_template_version,
    )
    session.add(app)
    session.commit()
    session.refresh(app)

    background_tasks.add_task(_run_pipeline, app.id)

    return app


def _run_pipeline(application_id: uuid.UUID) -> None:
    from backend.agents.runner import run_pipeline
    run_pipeline(application_id)


@router.get("/{application_id}")
def get_application(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ApplicationRepository(session)
    app = repo.get_by_user_and_id(user.id, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/{application_id}/retry", status_code=200)
def retry_application(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ApplicationRepository(session)
    app = repo.get_by_user_and_id(user.id, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != PipelineStatus.FAILED:
        raise HTTPException(status_code=409, detail="Only failed applications can be retried")

    session.exec(delete(Skill).where(Skill.application_id == application_id))
    app.status = PipelineStatus.UPLOADED
    app.company_name = "Analyzing…"
    app.job_title = "Analyzing…"
    app.error_message = None
    session.add(app)
    session.commit()
    session.refresh(app)

    background_tasks.add_task(_run_pipeline, app.id)
    return app


def _get_resume_bytes(application_id: uuid.UUID, user_id: uuid.UUID, session: Session) -> tuple[bytes, str]:
    """Shared helper: fetch app + resume, return (bytes, file_name). Raises HTTPException on errors."""
    repo = ApplicationRepository(session)
    app = repo.get_by_user_and_id(user_id, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not app.base_resume_id:
        raise HTTPException(status_code=404, detail="No resume attached to this application")
    resume = session.get(Resume, app.base_resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    try:
        data = download_bytes(resume.bucket_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Resume file not found in storage")
    return data, resume.file_name


@router.get("/{application_id}/skills")
def list_skills(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ApplicationRepository(session)
    app = repo.get_by_user_and_id(user.id, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return SkillRepository(session).list_by_application(application_id)


@router.get("/{application_id}/download/docx")
def download_docx(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    data, file_name = _get_resume_bytes(application_id, user.id, session)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/{application_id}/download/pdf")
def download_pdf(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    data, file_name = _get_resume_bytes(application_id, user.id, session)
    html = mammoth.convert_to_html(io.BytesIO(data)).value
    pdf_bytes = weasyprint.HTML(string=html).write_pdf(
        stylesheets=[weasyprint.CSS(string=_RESUME_CSS)]
    )
    pdf_name = file_name.rsplit(".", 1)[0] + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
    )


@router.get("/{application_id}/resume-html")
def get_resume_html(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    data, _ = _get_resume_bytes(application_id, user.id, session)
    return {"html": mammoth.convert_to_html(io.BytesIO(data)).value}


@router.get("/{application_id}/stream")
async def stream_application(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    async def event_generator() -> AsyncGenerator[str, None]:
        last_status = None
        terminal = {PipelineStatus.READY, PipelineStatus.FAILED, PipelineStatus.PENDING_APPROVAL}

        for _ in range(150):  # max ~5 min
            session.expire_all()
            app = session.get(Application, application_id)

            if app and app.status != last_status:
                last_status = app.status
                payload: dict = {
                    "status": app.status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                if app.company_name and app.company_name != "Analyzing…":
                    payload["company_name"] = app.company_name
                    payload["job_title"] = app.job_title
                if app.status == PipelineStatus.FAILED and app.error_message:
                    payload["error"] = app.error_message
                yield f"event: status_changed\ndata: {json.dumps(payload)}\n\n"

                if last_status in terminal:
                    break

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
