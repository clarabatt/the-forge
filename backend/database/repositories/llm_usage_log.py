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

    def get_monthly_tokens_by_model(
        self, user_id: uuid.UUID, since: datetime
    ) -> list[tuple[str, int, int]]:
        """Returns [(model, input_tokens, output_tokens)] grouped by model since `since`."""
        rows = self.session.exec(
            select(
                LlmUsageLog.model,
                func.coalesce(func.sum(LlmUsageLog.input_tokens), 0),
                func.coalesce(func.sum(LlmUsageLog.output_tokens), 0),
            ).where(
                LlmUsageLog.user_id == user_id,
                LlmUsageLog.created_at >= since,
            ).group_by(LlmUsageLog.model)
        ).all()
        return [(row[0], int(row[1]), int(row[2])) for row in rows]

    def get_monthly_cost_totals(
        self, user_id: uuid.UUID, since: datetime
    ) -> tuple[float, float, float, float]:
        """Returns (llm_cost, infra_cost, taxes_cost, total_cost) for a user since `since`."""
        row = self.session.exec(
            select(
                func.coalesce(func.sum(LlmUsageLog.llm_cost_usd), 0),
                func.coalesce(func.sum(LlmUsageLog.infra_cost_usd), 0),
                func.coalesce(func.sum(LlmUsageLog.taxes_cost_usd), 0),
                func.coalesce(func.sum(LlmUsageLog.total_cost_usd), 0),
            ).where(
                LlmUsageLog.user_id == user_id,
                LlmUsageLog.created_at >= since,
            )
        ).one()
        return float(row[0]), float(row[1]), float(row[2]), float(row[3])
