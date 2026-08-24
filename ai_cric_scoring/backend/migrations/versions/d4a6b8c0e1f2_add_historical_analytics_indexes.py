"""add historical analytics indexes

Revision ID: d4a6b8c0e1f2
Revises: c3e5f7a9b1d4
Create Date: 2026-08-17

Supports completed-match team batting lookups without career materialization.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4a6b8c0e1f2"
down_revision: str | Sequence[str] | None = "c3e5f7a9b1d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_innings_batting_match_team_id_match_id",
        "innings",
        ["batting_match_team_id", "match_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_innings_batting_match_team_id_match_id", table_name="innings")
