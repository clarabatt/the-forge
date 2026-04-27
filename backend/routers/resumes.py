import uuid

import mammoth
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import Resume, ResumeType, User
from backend.database.repositories import ResumeRepository
from backend.database.session import get_session
from backend.gcs import upload_bytes

router = APIRouter()

_DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _extract_text(data: bytes) -> str:
    import io
    result = mammoth.extract_raw_text(io.BytesIO(data))
    return result.value.strip()


@router.get("/")
def list_resumes(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ResumeRepository(session)
    return repo.list_by_user(user.id)


@router.post("/", status_code=201)
async def upload_resume(
    file: UploadFile,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=422, detail="Only .docx files are accepted")

    data = await file.read()
    if len(data) > _MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    repo = ResumeRepository(session)

    # bump version number
    existing = repo.get_latest_base_by_user(user.id)
    next_version = (existing.version_number + 1) if existing else 1

    # mark previous latest as not-latest
    repo.mark_previous_not_latest(user.id, ResumeType.BASE)

    bucket_key = f"resumes/{user.id}/{uuid.uuid4()}.docx"
    upload_bytes(bucket_key, data, _DOCX_CONTENT_TYPE)

    try:
        raw_text = _extract_text(data)
    except Exception:
        raw_text = None

    resume = Resume(
        user_id=user.id,
        file_name=file.filename,
        bucket_key=bucket_key,
        resume_type=ResumeType.BASE,
        is_latest=True,
        version_number=next_version,
        raw_text=raw_text,
        template_version=settings.current_template_version,
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume
