from datetime import datetime, timedelta

from sqlmodel import Session

from backend.database.repositories import OAuthStateRepository


def test_is_valid_true_for_unexpired_state(OAuthStateFactory, session: Session):
    state = OAuthStateFactory(expires_at=datetime.utcnow() + timedelta(minutes=10))

    repo = OAuthStateRepository(session)
    assert repo.is_valid(state.state) is True


def test_is_valid_false_for_expired_state(OAuthStateFactory, session: Session):
    state = OAuthStateFactory(expires_at=datetime.utcnow() - timedelta(seconds=1))

    repo = OAuthStateRepository(session)
    assert repo.is_valid(state.state) is False


def test_is_valid_false_for_unknown_state(session: Session):
    repo = OAuthStateRepository(session)
    assert repo.is_valid("completely-unknown-state") is False


def test_get_valid_returns_state_when_valid(OAuthStateFactory, session: Session):
    state = OAuthStateFactory()

    repo = OAuthStateRepository(session)
    result = repo.get_valid(state.state)

    assert result is not None
    assert result.state == state.state


def test_get_valid_returns_none_when_expired(OAuthStateFactory, session: Session):
    state = OAuthStateFactory(expires_at=datetime.utcnow() - timedelta(seconds=1))

    repo = OAuthStateRepository(session)
    assert repo.get_valid(state.state) is None


def test_delete_expired_removes_only_expired(OAuthStateFactory, session: Session):
    valid = OAuthStateFactory(expires_at=datetime.utcnow() + timedelta(minutes=5))
    OAuthStateFactory(expires_at=datetime.utcnow() - timedelta(minutes=1))
    OAuthStateFactory(expires_at=datetime.utcnow() - timedelta(minutes=2))

    repo = OAuthStateRepository(session)
    count = repo.delete_expired()

    assert count == 2
    assert repo.get_by_id(valid.state) is not None
