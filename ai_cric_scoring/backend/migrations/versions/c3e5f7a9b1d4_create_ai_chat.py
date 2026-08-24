"""create ai conversations and messages

Revision ID: c3e5f7a9b1d4
Revises: b2d4e6f8a0c3
Create Date: 2026-08-16

One conversation per user+match. Messages are ordered by created_at, id.
client_message_id makes chat submissions retry-safe.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3e5f7a9b1d4"
down_revision: str | Sequence[str] | None = "b2d4e6f8a0c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("pending_question", sa.String(length=1000), nullable=True),
        sa.Column("last_player_id", sa.Uuid(), nullable=True),
        sa.Column("last_team_id", sa.Uuid(), nullable=True),
        sa.Column("last_innings_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "match_id", name="uq_ai_conversations_user_match"),
    )
    op.create_index("ix_ai_conversations_user_id_match_id", "ai_conversations", ["user_id", "match_id"])
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("client_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_type", sa.String(length=32), nullable=True),
        sa.Column("answer_type", sa.String(length=32), nullable=True),
        sa.Column("fact_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("follow_up_suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("clarification_options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("used_ai", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "client_message_id", name="uq_ai_messages_conversation_client"),
    )
    op.create_index(
        "ix_ai_messages_conversation_created_at",
        "ai_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_messages_conversation_created_at", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_user_id_match_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
