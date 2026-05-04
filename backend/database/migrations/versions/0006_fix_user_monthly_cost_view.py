"""fix user_monthly_cost view pricing

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-03

The original view used Claude-era per-token prices ($0.000003 input / $0.000015 output).
This migration recreates it with Gemini 2.5 Flash pricing as a reasonable default.
Note: the view is for introspection only — application code uses per-model pricing logic.
"""
from typing import Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None

# Gemini 2.5 Flash: $0.15 / 1M input, $0.60 / 1M output
_INPUT_RATE = 0.15 / 1_000_000
_OUTPUT_RATE = 0.60 / 1_000_000


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS user_monthly_cost")
    op.execute(f"""
        CREATE VIEW user_monthly_cost AS
        SELECT
            user_id,
            DATE_TRUNC('month', created_at) AS month,
            SUM((input_tokens * {_INPUT_RATE}) + (output_tokens * {_OUTPUT_RATE})) AS cost_usd
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
            SUM((input_tokens * 0.000003) + (output_tokens * 0.000015)) AS cost_usd
        FROM llm_usage_logs
        GROUP BY user_id, DATE_TRUNC('month', created_at)
    """)
