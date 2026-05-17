"""add llm_cost_usd to llm_usage_logs

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-17

Stores the token cost at write time via pricing.token_cost().
Infra overhead is applied as a configurable markup percentage at query time.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in ("llm_cost_usd", "infra_cost_usd", "taxes_cost_usd", "total_cost_usd"):
        op.add_column("llm_usage_logs", sa.Column(col, sa.Float(), nullable=False, server_default="0.0"))

    op.execute("DROP VIEW IF EXISTS user_monthly_cost")
    op.execute("""
        CREATE VIEW user_monthly_cost AS
        SELECT
            user_id,
            DATE_TRUNC('month', created_at) AS month,
            SUM(llm_cost_usd)    AS llm_cost_usd,
            SUM(infra_cost_usd)  AS infra_cost_usd,
            SUM(taxes_cost_usd)  AS taxes_cost_usd,
            SUM(total_cost_usd)  AS total_cost_usd
        FROM llm_usage_logs
        GROUP BY user_id, DATE_TRUNC('month', created_at)
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS user_monthly_cost")
    op.execute("""
        CREATE VIEW user_monthly_cost AS
        SELECT
            user_id,
            DATE_TRUNC('month', created_at) AS month,
            SUM((input_tokens * 0.00000015) + (output_tokens * 0.0000006)) AS cost_usd
        FROM llm_usage_logs
        GROUP BY user_id, DATE_TRUNC('month', created_at)
    """)

    for col in ("total_cost_usd", "taxes_cost_usd", "infra_cost_usd", "llm_cost_usd"):
        op.drop_column("llm_usage_logs", col)
