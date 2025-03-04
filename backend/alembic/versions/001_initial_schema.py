"""Initial schema: users, refresh_tokens, analysis_history

Revision ID: 001
Revises:
Create Date: 2026-02-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Users ───
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False, server_default="user"),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_oauth", "users", ["oauth_provider", "oauth_id"], unique=True)

    # ─── Refresh Tokens ───
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("device_info", sa.String(512), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reuse_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # ─── Analysis History ───
    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_type", sa.Enum("text", "image", "multimodal", name="contenttype"), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("input_preview", sa.Text(), nullable=True),
        sa.Column("prediction", sa.String(10), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("credibility_score", sa.Float(), nullable=False),
        sa.Column("model_scores", sa.JSON(), nullable=True),
        sa.Column("explainability_data", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(20), nullable=False),
        sa.Column("low_confidence_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analysis_history_content_hash", "analysis_history", ["content_hash"])
    op.create_index("ix_history_user_created", "analysis_history", ["user_id", "created_at"])
    op.create_index("ix_history_content_hash_user", "analysis_history", ["content_hash", "user_id"])


def downgrade() -> None:
    op.drop_table("analysis_history")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    # Drop enum types (PostgreSQL-specific)
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS userrole")
