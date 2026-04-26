import uuid

from sqlmodel import Session

from backend.database.repositories import UserRepository


def test_add_and_get_by_id(UserFactory, session: Session):
    user = UserFactory()

    repo = UserRepository(session)
    result = repo.get_by_id(user.id)

    assert result is not None
    assert result.id == user.id
    assert result.email == user.email


def test_get_by_id_not_found(session: Session):
    repo = UserRepository(session)
    assert repo.get_by_id(uuid.uuid4()) is None


def test_get_by_email_found(UserFactory, session: Session):
    UserFactory(email="alice@example.com")

    repo = UserRepository(session)
    result = repo.get_by_email("alice@example.com")

    assert result is not None
    assert result.email == "alice@example.com"


def test_get_by_email_not_found(session: Session):
    repo = UserRepository(session)
    assert repo.get_by_email("ghost@example.com") is None


def test_get_by_google_sub_found(UserFactory, session: Session):
    user = UserFactory(google_sub="google-abc-123")

    repo = UserRepository(session)
    result = repo.get_by_google_sub("google-abc-123")

    assert result is not None
    assert result.id == user.id


def test_get_by_google_sub_not_found(session: Session):
    repo = UserRepository(session)
    assert repo.get_by_google_sub("nobody") is None


def test_get_active_returns_user_when_active(UserFactory, session: Session):
    user = UserFactory(is_active=True)

    repo = UserRepository(session)
    result = repo.get_active(user.id)

    assert result is not None
    assert result.id == user.id


def test_get_active_returns_none_when_inactive(UserFactory, session: Session):
    user = UserFactory(is_active=False)

    repo = UserRepository(session)
    assert repo.get_active(user.id) is None


def test_update_persists_changes(UserFactory, session: Session):
    user = UserFactory()

    user.full_name = "Updated Name"
    repo = UserRepository(session)
    repo.update(user)

    result = repo.get_by_id(user.id)
    assert result.full_name == "Updated Name"


def test_delete_removes_user(UserFactory, session: Session):
    user = UserFactory()

    repo = UserRepository(session)
    repo.delete(user)

    assert repo.get_by_id(user.id) is None


def test_list_all_returns_all_users(UserFactory, session: Session):
    UserFactory(email="a@example.com")
    UserFactory(email="b@example.com")

    repo = UserRepository(session)
    results = repo.list_all()

    assert len(results) == 2
