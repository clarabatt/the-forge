import uuid
from datetime import datetime

from sqlmodel import Session, col, func, select

from backend.database.models import LlmUsageLog
from backend.database.repositories.base import BaseRepository


class LlmUsageLogRepository(BaseRepository[LlmUsageLog, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, LlmUsageLog)

    def list_by_user(self, user_id: uuid.UUID) -> list[LlmUsageLog]:
        return list(
            self.session.exec(
                select(LlmUsageLog).where(LlmUsageLog.user_id == user_id)
            ).all()
        )

    def list_by_application(self, application_id: uuid.UUID) -> list[LlmUsageLog]:
        return list(
            self.session.exec(
                select(LlmUsageLog).where(
                    LlmUsageLog.application_id == application_id
                )
            ).all()
        )

    def get_monthly_token_totals(
        self, user_id: uuid.UUID, since: datetime
    ) -> tuple[int, int]:
        """Returns (total_input_tokens, total_output_tokens) for a user since `since`."""
        result = self.session.exec(
            select(
                func.coalesce(func.sum(LlmUsageLog.input_tokens), 0),
                func.coalesce(func.sum(LlmUsageLog.output_tokens), 0),
            ).where(
                LlmUsageLog.user_id == user_id,
                LlmUsageLog.created_at >= since,
            )
        ).one()
        return result[0], result[1]
