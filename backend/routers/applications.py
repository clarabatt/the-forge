import asyncio
import io
import json
import uuid
from datetime import datetime
from datetime import timezone
from typing import AsyncGenerator

import mammoth
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, delete

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import Application, ApplicationStatus, PipelineStatus, Resume, Skill, User
from backend.database.repositories import ApplicationRepository
from backend.database.session import get_session
from backend.gcs import download_bytes

router = APIRouter()


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


@router.get("/{application_id}/resume-html")
def get_resume_html(
    application_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ApplicationRepository(session)
    app = repo.get_by_user_and_id(user.id, application_id)
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

    result = mammoth.convert_to_html(io.BytesIO(data))
    return {"html": result.value}


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
