import uuid

from sqlmodel import Session

from backend.database.repositories import CoverLetterRepository


def test_get_by_application_returns_cover_letter(
    UserFactory, ApplicationFactory, CoverLetterFactory, session: Session
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    cl = CoverLetterFactory(application_id=app.id, content="My cover letter.")

    repo = CoverLetterRepository(session)
    result = repo.get_by_application(app.id)

    assert result is not None
    assert result.id == cl.id
    assert result.content == "My cover letter."


def test_get_by_application_returns_none_when_missing(
    UserFactory, ApplicationFactory, session: Session
):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)

    repo = CoverLetterRepository(session)
    result = repo.get_by_application(app.id)

    assert result is None


def test_get_by_application_excludes_other_applications(
    UserFactory, ApplicationFactory, CoverLetterFactory, session: Session
):
    user = UserFactory()
    app_a = ApplicationFactory(user_id=user.id)
    app_b = ApplicationFactory(user_id=user.id)
    CoverLetterFactory(application_id=app_b.id)

    repo = CoverLetterRepository(session)
    assert repo.get_by_application(app_a.id) is None


def test_get_by_application_returns_none_for_unknown_id(session: Session):
    repo = CoverLetterRepository(session)
    assert repo.get_by_application(uuid.uuid4()) is None
