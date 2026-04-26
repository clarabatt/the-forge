import uuid
from datetime import datetime, timedelta

from sqlmodel import Session

from backend.database.models import PipelineStatus
from backend.database.repositories import ApplicationRepository


def test_list_by_user_returns_only_that_users_applications(UserFactory, ApplicationFactory, session: Session):
    user_a = UserFactory(email="a@example.com")
    user_b = UserFactory(email="b@example.com")
    ApplicationFactory(user_id=user_a.id)
    ApplicationFactory(user_id=user_a.id)
    ApplicationFactory(user_id=user_b.id)

    repo = ApplicationRepository(session)
    results = repo.list_by_user(user_a.id)

    assert len(results) == 2
    assert all(a.user_id == user_a.id for a in results)


def test_list_by_user_returns_empty_when_no_applications(UserFactory, session: Session):
    user = UserFactory()

    repo = ApplicationRepository(session)
    assert repo.list_by_user(user.id) == []


def test_get_by_user_and_id_found(UserFactory, ApplicationFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)

    repo = ApplicationRepository(session)
    result = repo.get_by_user_and_id(user.id, app.id)

    assert result is not None
    assert result.id == app.id


def test_get_by_user_and_id_wrong_user_returns_none(UserFactory, ApplicationFactory, session: Session):
    owner = UserFactory(email="owner@example.com")
    other = UserFactory(email="other@example.com")
    app = ApplicationFactory(user_id=owner.id)

    repo = ApplicationRepository(session)
    assert repo.get_by_user_and_id(other.id, app.id) is None


def test_get_by_user_and_id_not_found(UserFactory, session: Session):
    user = UserFactory()

    repo = ApplicationRepository(session)
    assert repo.get_by_user_and_id(user.id, uuid.uuid4()) is None


def test_list_by_pipeline_status(UserFactory, ApplicationFactory, session: Session):
    user = UserFactory()
    ApplicationFactory(user_id=user.id, status=PipelineStatus.ANALYZING)
    ApplicationFactory(user_id=user.id, status=PipelineStatus.ANALYZING)
    ApplicationFactory(user_id=user.id, status=PipelineStatus.READY)

    repo = ApplicationRepository(session)
    results = repo.list_by_pipeline_status(PipelineStatus.ANALYZING)

    assert len(results) == 2
    assert all(a.status == PipelineStatus.ANALYZING for a in results)


def test_count_recent_by_user(UserFactory, ApplicationFactory, session: Session):
    user = UserFactory()
    ApplicationFactory(user_id=user.id)
    ApplicationFactory(user_id=user.id)

    repo = ApplicationRepository(session)
    count = repo.count_recent_by_user(user.id, since=datetime.utcnow() - timedelta(hours=1))

    assert count == 2


def test_count_recent_by_user_excludes_old_applications(UserFactory, ApplicationFactory, session: Session):
    user = UserFactory()
    ApplicationFactory(user_id=user.id)

    repo = ApplicationRepository(session)
    count = repo.count_recent_by_user(user.id, since=datetime.utcnow() + timedelta(hours=1))

    assert count == 0
