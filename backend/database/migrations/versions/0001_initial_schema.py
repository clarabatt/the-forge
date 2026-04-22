"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("google_sub", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("picture_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)

    op.create_table(
        "oauth_states",
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("state"),
    )

    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("bucket_key", sa.String(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("resume_type", sa.String(), nullable=False),
        sa.Column("parent_resume_id", sa.Uuid(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("template_version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["parent_resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_is_latest", "resumes", ["is_latest"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("job_title", sa.String(), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("application_status", sa.String(), nullable=False),
        sa.Column("base_resume_id", sa.Uuid(), nullable=True),
        sa.Column("template_version", sa.String(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["base_resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("match_status", sa.String(), nullable=False),
        sa.Column("user_action", sa.String(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "llm_usage_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("""
        CREATE VIEW user_monthly_cost AS
        SELECT
            user_id,
            DATE_TRUNC('month', created_at) AS month,
            SUM((input_tokens * 0.000003) + (output_tokens * 0.000015)) AS cost_usd
        FROM llm_usage_logs
        GROUP BY user_id, DATE_TRUNC('month', created_at)
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS user_monthly_cost")
    op.drop_table("chat_messages")
    op.drop_table("llm_usage_logs")
    op.drop_table("skills")
    op.drop_table("applications")
    op.drop_index("ix_resumes_is_latest", "resumes")
    op.drop_table("resumes")
    op.drop_table("oauth_states")
    op.drop_index("ix_users_google_sub", "users")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
