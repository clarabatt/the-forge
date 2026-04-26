from sqlmodel import Session

from backend.database.models import ResumeType
from backend.database.repositories import ResumeRepository


def test_list_by_user_returns_only_that_users_resumes(UserFactory, ResumeFactory, session: Session):
    user_a = UserFactory(email="a@example.com")
    user_b = UserFactory(email="b@example.com")
    ResumeFactory(user_id=user_a.id)
    ResumeFactory(user_id=user_b.id)

    repo = ResumeRepository(session)
    results = repo.list_by_user(user_a.id)

    assert len(results) == 1
    assert results[0].user_id == user_a.id


def test_list_by_application(UserFactory, ApplicationFactory, ResumeFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    ResumeFactory(user_id=user.id, application_id=app.id, resume_type=ResumeType.TAILORED)
    ResumeFactory(user_id=user.id, application_id=app.id, resume_type=ResumeType.TAILORED)
    ResumeFactory(user_id=user.id)  # base resume, no application

    repo = ResumeRepository(session)
    results = repo.list_by_application(app.id)

    assert len(results) == 2
    assert all(r.application_id == app.id for r in results)


def test_get_latest_base_by_user_returns_latest(UserFactory, ResumeFactory, session: Session):
    user = UserFactory()
    ResumeFactory(user_id=user.id, resume_type=ResumeType.BASE, is_latest=False, version_number=1)
    latest = ResumeFactory(user_id=user.id, resume_type=ResumeType.BASE, is_latest=True, version_number=2)

    repo = ResumeRepository(session)
    result = repo.get_latest_base_by_user(user.id)

    assert result is not None
    assert result.id == latest.id
    assert result.is_latest is True


def test_get_latest_base_by_user_returns_none_when_no_base(UserFactory, ApplicationFactory, ResumeFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    ResumeFactory(user_id=user.id, application_id=app.id, resume_type=ResumeType.TAILORED)

    repo = ResumeRepository(session)
    assert repo.get_latest_base_by_user(user.id) is None


def test_mark_previous_not_latest(UserFactory, ResumeFactory, session: Session):
    user = UserFactory()
    old_v1 = ResumeFactory(user_id=user.id, resume_type=ResumeType.BASE, is_latest=True, version_number=1)
    old_v2 = ResumeFactory(user_id=user.id, resume_type=ResumeType.BASE, is_latest=True, version_number=2)

    repo = ResumeRepository(session)
    repo.mark_previous_not_latest(user.id, ResumeType.BASE)

    session.expire_all()
    assert repo.get_by_id(old_v1.id).is_latest is False
    assert repo.get_by_id(old_v2.id).is_latest is False


def test_mark_previous_not_latest_does_not_affect_other_users(UserFactory, ResumeFactory, session: Session):
    user_a = UserFactory(email="a@example.com")
    user_b = UserFactory(email="b@example.com")
    resume_b = ResumeFactory(user_id=user_b.id, resume_type=ResumeType.BASE, is_latest=True)

    repo = ResumeRepository(session)
    repo.mark_previous_not_latest(user_a.id, ResumeType.BASE)

    session.expire_all()
    assert repo.get_by_id(resume_b.id).is_latest is True
