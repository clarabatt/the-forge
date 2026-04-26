import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, func, select

from backend.database.models import Application, PipelineStatus
from backend.database.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Application)

    def list_by_user(self, user_id: uuid.UUID) -> list[Application]:
        return list(
            self.session.exec(
                select(Application).where(Application.user_id == user_id)
            ).all()
        )

    def get_by_user_and_id(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> Optional[Application]:
        return self.session.exec(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        ).first()

    def list_by_pipeline_status(self, status: PipelineStatus) -> list[Application]:
        return list(
            self.session.exec(
                select(Application).where(Application.status == status)
            ).all()
        )

    def count_recent_by_user(self, user_id: uuid.UUID, since: datetime) -> int:
        result = self.session.exec(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= since,
            )
        ).one()
        return result
