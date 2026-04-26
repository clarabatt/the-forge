from sqlmodel import Session

from backend.database.models import ChatRole
from backend.database.repositories import ChatMessageRepository


def test_list_by_application_ordered_by_created_at(UserFactory, ApplicationFactory, ChatMessageFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    msg1 = ChatMessageFactory(application_id=app.id, content="First")
    msg2 = ChatMessageFactory(application_id=app.id, content="Second")
    msg3 = ChatMessageFactory(application_id=app.id, content="Third")

    repo = ChatMessageRepository(session)
    results = repo.list_by_application(app.id)

    assert len(results) == 3
    assert [m.id for m in results] == [msg1.id, msg2.id, msg3.id]


def test_list_by_application_excludes_other_applications(UserFactory, ApplicationFactory, ChatMessageFactory, session: Session):
    user = UserFactory()
    app_a = ApplicationFactory(user_id=user.id, job_title="Backend")
    app_b = ApplicationFactory(user_id=user.id, job_title="Frontend")
    ChatMessageFactory(application_id=app_a.id)
    ChatMessageFactory(application_id=app_b.id)

    repo = ChatMessageRepository(session)
    assert len(repo.list_by_application(app_a.id)) == 1


def test_list_by_role_returns_only_matching_role(UserFactory, ApplicationFactory, ChatMessageFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    ChatMessageFactory(application_id=app.id, role=ChatRole.user)
    ChatMessageFactory(application_id=app.id, role=ChatRole.user)
    ChatMessageFactory(application_id=app.id, role=ChatRole.assistant)

    repo = ChatMessageRepository(session)
    user_msgs = repo.list_by_role(app.id, ChatRole.user)
    assistant_msgs = repo.list_by_role(app.id, ChatRole.assistant)

    assert len(user_msgs) == 2
    assert len(assistant_msgs) == 1
