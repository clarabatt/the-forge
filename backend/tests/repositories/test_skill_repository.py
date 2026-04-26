from sqlmodel import Session

from backend.database.models import Skill, SkillMatchStatus
from backend.database.repositories import SkillRepository


def test_list_by_application_ordered_by_rank(UserFactory, ApplicationFactory, SkillFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    SkillFactory(application_id=app.id, skill_name="Docker", rank=3)
    SkillFactory(application_id=app.id, skill_name="Python", rank=1)
    SkillFactory(application_id=app.id, skill_name="SQL", rank=2)

    repo = SkillRepository(session)
    results = repo.list_by_application(app.id)

    assert [s.rank for s in results] == [1, 2, 3]


def test_list_by_application_excludes_other_applications(UserFactory, ApplicationFactory, SkillFactory, session: Session):
    user = UserFactory()
    app_a = ApplicationFactory(user_id=user.id, job_title="Backend")
    app_b = ApplicationFactory(user_id=user.id, job_title="Frontend")
    SkillFactory(application_id=app_a.id)
    SkillFactory(application_id=app_b.id)

    repo = SkillRepository(session)
    assert len(repo.list_by_application(app_a.id)) == 1


def test_list_missing_returns_only_missing_skills(UserFactory, ApplicationFactory, SkillFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    SkillFactory(application_id=app.id, match_status=SkillMatchStatus.found_in_resume, rank=1)
    SkillFactory(application_id=app.id, match_status=SkillMatchStatus.missing, rank=2)
    SkillFactory(application_id=app.id, match_status=SkillMatchStatus.missing, rank=3)

    repo = SkillRepository(session)
    results = repo.list_missing(app.id)

    assert len(results) == 2
    assert all(s.match_status == SkillMatchStatus.missing for s in results)


def test_bulk_replace_removes_old_and_inserts_new(UserFactory, ApplicationFactory, SkillFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    SkillFactory(application_id=app.id, skill_name="Old Skill", rank=1)

    new_skills = [
        Skill(
            application_id=app.id,
            skill_name="New Skill A",
            category="Engineering",
            match_status=SkillMatchStatus.found_in_resume,
            ai_confidence=0.8,
            rank=1,
        ),
        Skill(
            application_id=app.id,
            skill_name="New Skill B",
            category="Engineering",
            match_status=SkillMatchStatus.missing,
            ai_confidence=0.6,
            rank=2,
        ),
    ]

    repo = SkillRepository(session)
    result = repo.bulk_replace(app.id, new_skills)

    assert len(result) == 2
    remaining = repo.list_by_application(app.id)
    assert len(remaining) == 2
    assert {s.skill_name for s in remaining} == {"New Skill A", "New Skill B"}
