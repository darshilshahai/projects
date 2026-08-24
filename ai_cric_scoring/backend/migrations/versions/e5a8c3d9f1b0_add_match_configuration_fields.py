"""add match configuration fields

Revision ID: e5a8c3d9f1b0
Revises: d4f7b2c1e8a9
Create Date: 2026-08-14

Adds READY match status, players_per_team, toss fields, and team short-name snapshots.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5a8c3d9f1b0"
down_revision: str | Sequence[str] | None = "d4f7b2c1e8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("BAT", "BOWL", name="toss_decision").create(bind, checkfirst=True)

    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'READY'"))

    op.add_column(
        "matches",
        sa.Column("players_per_team", sa.Integer(), server_default="11", nullable=False),
    )
    op.add_column(
        "matches",
        sa.Column("toss_winner_match_team_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column(
            "toss_decision",
            postgresql.ENUM("BAT", "BOWL", name="toss_decision", create_type=False),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_matches_players_per_team_range",
        "matches",
        "players_per_team >= 2 AND players_per_team <= 11",
    )

    op.add_column("match_teams", sa.Column("team_short_name_snapshot", sa.String(length=16), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE match_teams AS mt
            SET team_short_name_snapshot = t.short_name
            FROM teams AS t
            WHERE t.id = mt.team_id
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE matches SET status = 'DRAFT' WHERE status = 'READY'"))
    op.drop_constraint("ck_matches_players_per_team_range", "matches", type_="check")
    op.drop_column("matches", "toss_decision")
    op.drop_column("matches", "toss_winner_match_team_id")
    op.drop_column("matches", "players_per_team")
    op.drop_column("match_teams", "team_short_name_snapshot")
    postgresql.ENUM(name="toss_decision").drop(op.get_bind(), checkfirst=True)
