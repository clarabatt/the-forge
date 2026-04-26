import uuid

from sqlmodel import Session, select

from backend.database.models import ChatMessage, ChatRole
from backend.database.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ChatMessage)

    def list_by_application(self, application_id: uuid.UUID) -> list[ChatMessage]:
        return list(
            self.session.exec(
                select(ChatMessage)
                .where(ChatMessage.application_id == application_id)
                .order_by(ChatMessage.created_at)
            ).all()
        )

    def list_by_role(
        self, application_id: uuid.UUID, role: ChatRole
    ) -> list[ChatMessage]:
        return list(
            self.session.exec(
                select(ChatMessage)
                .where(
                    ChatMessage.application_id == application_id,
                    ChatMessage.role == role,
                )
                .order_by(ChatMessage.created_at)
            ).all()
        )
