import uuid
from typing import Optional

from sqlmodel import Session, select

from backend.database.models import CoverLetter
from backend.database.repositories.base import BaseRepository


class CoverLetterRepository(BaseRepository[CoverLetter, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CoverLetter)

    def get_by_application(self, application_id: uuid.UUID) -> Optional[CoverLetter]:
        return self.session.exec(
            select(CoverLetter).where(CoverLetter.application_id == application_id)
        ).first()
