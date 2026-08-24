"""add match history indexes

Revision ID: a1c3e5f7b9d2
Revises: f6b9d4e0a2c1
Create Date: 2026-08-15

Adds (created_by_user_id, status, completed_at) for paginated completed-match history.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1c3e5f7b9d2"
down_revision: str | Sequence[str] | None = "f6b9d4e0a2c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_matches_created_by_status_completed_at",
        "matches",
        ["created_by_user_id", "status", "completed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_matches_created_by_status_completed_at", table_name="matches")
