import uuid

from sqlmodel import Session, select

from backend.database.models import Skill, SkillMatchStatus
from backend.database.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill, uuid.UUID]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Skill)

    def list_by_application(self, application_id: uuid.UUID) -> list[Skill]:
        return list(
            self.session.exec(
                select(Skill)
                .where(Skill.application_id == application_id)
                .order_by(Skill.rank)
            ).all()
        )

    def list_missing(self, application_id: uuid.UUID) -> list[Skill]:
        return list(
            self.session.exec(
                select(Skill).where(
                    Skill.application_id == application_id,
                    Skill.match_status == SkillMatchStatus.missing,
                )
            ).all()
        )

    def bulk_replace(self, application_id: uuid.UUID, skills: list[Skill]) -> list[Skill]:
        existing = self.session.exec(
            select(Skill).where(Skill.application_id == application_id)
        ).all()
        for skill in existing:
            self.session.delete(skill)

        for skill in skills:
            self.session.add(skill)

        self.session.commit()
        for skill in skills:
            self.session.refresh(skill)
        return skills
