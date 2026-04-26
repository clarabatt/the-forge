import uuid
from typing import Optional

from sqlmodel import Session, select

from backend.database.models import Resume, ResumeType
from backend.database.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Resume)

    def list_by_user(self, user_id: uuid.UUID) -> list[Resume]:
        return list(
            self.session.exec(select(Resume).where(Resume.user_id == user_id)).all()
        )

    def list_by_application(self, application_id: uuid.UUID) -> list[Resume]:
        return list(
            self.session.exec(
                select(Resume).where(Resume.application_id == application_id)
            ).all()
        )

    def get_latest_base_by_user(self, user_id: uuid.UUID) -> Optional[Resume]:
        return self.session.exec(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.resume_type == ResumeType.BASE,
                Resume.is_latest == True,
            )
        ).first()

    def mark_previous_not_latest(
        self, user_id: uuid.UUID, resume_type: ResumeType
    ) -> None:
        resumes = self.session.exec(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.resume_type == resume_type,
                Resume.is_latest == True,
            )
        ).all()
        for resume in resumes:
            resume.is_latest = False
            self.session.add(resume)
        self.session.commit()
