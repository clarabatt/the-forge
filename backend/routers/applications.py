import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from backend.database.models import Application
from backend.database.session import get_session

router = APIRouter()


@router.get("/")
def list_applications(session: Session = Depends(get_session)):
    # TODO: filter by authenticated user
    return session.exec(select(Application)).all()


@router.get("/{application_id}")
def get_application(application_id: uuid.UUID, session: Session = Depends(get_session)):
    app = session.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.get("/{application_id}/stream")
async def stream_application(application_id: uuid.UUID):
    async def event_generator() -> AsyncGenerator[str, None]:
        # TODO: implement real SSE from DB state changes
        yield f"event: status_changed\ndata: {{\"status\": \"UPLOADED\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
