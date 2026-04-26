from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.auth import get_current_user
from backend.database.models import User
from backend.database.repositories import ResumeRepository
from backend.database.session import get_session

router = APIRouter()


@router.get("/")
def list_resumes(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    repo = ResumeRepository(session)
    return repo.list_by_user(user.id)
