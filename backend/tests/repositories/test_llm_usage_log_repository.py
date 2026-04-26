from datetime import datetime, timedelta

from sqlmodel import Session

from backend.database.repositories import LlmUsageLogRepository


def test_list_by_user_returns_only_that_users_logs(UserFactory, LlmUsageLogFactory, session: Session):
    user_a = UserFactory(email="a@example.com")
    user_b = UserFactory(email="b@example.com")
    LlmUsageLogFactory(user_id=user_a.id)
    LlmUsageLogFactory(user_id=user_a.id)
    LlmUsageLogFactory(user_id=user_b.id)

    repo = LlmUsageLogRepository(session)
    results = repo.list_by_user(user_a.id)

    assert len(results) == 2
    assert all(log.user_id == user_a.id for log in results)


def test_list_by_application(UserFactory, ApplicationFactory, LlmUsageLogFactory, session: Session):
    user = UserFactory()
    app = ApplicationFactory(user_id=user.id)
    LlmUsageLogFactory(user_id=user.id, application_id=app.id)
    LlmUsageLogFactory(user_id=user.id, application_id=app.id)
    LlmUsageLogFactory(user_id=user.id)  # no application

    repo = LlmUsageLogRepository(session)
    results = repo.list_by_application(app.id)

    assert len(results) == 2
    assert all(log.application_id == app.id for log in results)


def test_get_monthly_token_totals_sums_correctly(UserFactory, LlmUsageLogFactory, session: Session):
    user = UserFactory()
    LlmUsageLogFactory(user_id=user.id, input_tokens=100, output_tokens=50)
    LlmUsageLogFactory(user_id=user.id, input_tokens=200, output_tokens=75)

    repo = LlmUsageLogRepository(session)
    input_total, output_total = repo.get_monthly_token_totals(
        user.id, since=datetime.utcnow() - timedelta(hours=1)
    )

    assert input_total == 300
    assert output_total == 125


def test_get_monthly_token_totals_returns_zeros_when_no_logs(UserFactory, session: Session):
    user = UserFactory()

    repo = LlmUsageLogRepository(session)
    input_total, output_total = repo.get_monthly_token_totals(
        user.id, since=datetime.utcnow() - timedelta(hours=1)
    )

    assert input_total == 0
    assert output_total == 0


def test_get_monthly_token_totals_excludes_logs_before_since(UserFactory, LlmUsageLogFactory, session: Session):
    user = UserFactory()
    old_time = datetime.utcnow() - timedelta(days=40)
    LlmUsageLogFactory(user_id=user.id, input_tokens=999, created_at=old_time)

    repo = LlmUsageLogRepository(session)
    input_total, output_total = repo.get_monthly_token_totals(
        user.id, since=datetime.utcnow() - timedelta(days=30)
    )

    assert input_total == 0
    assert output_total == 0
