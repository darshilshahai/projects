"""add cricket scoring persistence

Revision ID: f6b9d4e0a2c1
Revises: e5a8c3d9f1b0
Create Date: 2026-08-15

Adds innings, scoring events, delivery projections, dismissals, score snapshots,
batting/bowling stats, and match result fields.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6b9d4e0a2c1"
down_revision: str | Sequence[str] | None = "e5a8c3d9f1b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INNINGS_STATUS = ("NOT_STARTED", "LIVE", "COMPLETED")
DISMISSAL_TYPE = (
    "BOWLED",
    "CAUGHT",
    "LBW",
    "RUN_OUT",
    "STUMPED",
    "HIT_WICKET",
    "RETIRED_OUT",
    "OBSTRUCTING_THE_FIELD",
    "HIT_THE_BALL_TWICE",
)
SCORING_EVENT_TYPE = (
    "INNINGS_STARTED",
    "DELIVERY_RECORDED",
    "BATTER_SELECTED",
    "BOWLER_SELECTED",
    "BATTER_RETIRED",
    "DELIVERY_VOIDED",
    "INNINGS_COMPLETED",
    "MATCH_COMPLETED",
)
RESULT_TYPE = ("WON", "TIED")


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(*INNINGS_STATUS, name="innings_status").create(bind, checkfirst=True)
    postgresql.ENUM(*DISMISSAL_TYPE, name="dismissal_type").create(bind, checkfirst=True)
    postgresql.ENUM(*SCORING_EVENT_TYPE, name="scoring_event_type").create(bind, checkfirst=True)
    postgresql.ENUM(*RESULT_TYPE, name="result_type").create(bind, checkfirst=True)

    op.add_column("matches", sa.Column("result_type", postgresql.ENUM(*RESULT_TYPE, name="result_type", create_type=False)))
    op.add_column("matches", sa.Column("winner_match_team_id", sa.Uuid(), nullable=True))
    op.add_column("matches", sa.Column("margin_runs", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("margin_wickets", sa.Integer(), nullable=True))

    op.create_table(
        "innings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("innings_number", sa.Integer(), nullable=False),
        sa.Column("batting_match_team_id", sa.Uuid(), nullable=False),
        sa.Column("bowling_match_team_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(*INNINGS_STATUS, name="innings_status", create_type=False),
            nullable=False,
        ),
        sa.Column("target_runs", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batting_match_team_id"], ["match_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["bowling_match_team_id"], ["match_teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "innings_number", name="uq_innings_match_number"),
    )

    op.create_table(
        "scoring_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("innings_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("client_event_id", sa.Uuid(), nullable=True),
        sa.Column("base_revision", sa.Integer(), nullable=True),
        sa.Column(
            "event_type",
            postgresql.ENUM(*SCORING_EVENT_TYPE, name="scoring_event_type", create_type=False),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_voided", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["innings_id"], ["innings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("innings_id", "sequence_number", name="uq_scoring_events_innings_sequence"),
    )
    op.create_index(
        "uq_scoring_events_match_client_event",
        "scoring_events",
        ["match_id", "client_event_id"],
        unique=True,
        postgresql_where=sa.text("client_event_id IS NOT NULL"),
    )

    op.create_table(
        "score_snapshots",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("innings_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("total_runs", sa.Integer(), nullable=False),
        sa.Column("wickets", sa.Integer(), nullable=False),
        sa.Column("legal_balls", sa.Integer(), nullable=False),
        sa.Column("striker_id", sa.Uuid(), nullable=True),
        sa.Column("non_striker_id", sa.Uuid(), nullable=True),
        sa.Column("current_bowler_id", sa.Uuid(), nullable=True),
        sa.Column("previous_bowler_id", sa.Uuid(), nullable=True),
        sa.Column("needs_new_batter", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("needs_new_bowler", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("target_runs", sa.Integer(), nullable=True),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["innings_id"], ["innings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["striker_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["non_striker_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["current_bowler_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous_bowler_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("innings_id", name="uq_score_snapshots_innings"),
    )

    op.create_table(
        "deliveries",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("innings_id", sa.Uuid(), nullable=False),
        sa.Column("scoring_event_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("over_number", sa.Integer(), nullable=False),
        sa.Column("ball_in_over", sa.Integer(), nullable=False),
        sa.Column("striker_id", sa.Uuid(), nullable=False),
        sa.Column("non_striker_id", sa.Uuid(), nullable=False),
        sa.Column("bowler_id", sa.Uuid(), nullable=False),
        sa.Column("runs_off_bat", sa.Integer(), nullable=False),
        sa.Column("wides", sa.Integer(), nullable=False),
        sa.Column("no_balls", sa.Integer(), nullable=False),
        sa.Column("byes", sa.Integer(), nullable=False),
        sa.Column("leg_byes", sa.Integer(), nullable=False),
        sa.Column("penalty_runs", sa.Integer(), nullable=False),
        sa.Column("is_legal", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_voided", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["innings_id"], ["innings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scoring_event_id"], ["scoring_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["striker_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["non_striker_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bowler_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("innings_id", "sequence_number", name="uq_deliveries_innings_sequence"),
    )

    op.create_table(
        "dismissals",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("dismissed_player_id", sa.Uuid(), nullable=False),
        sa.Column(
            "dismissal_type",
            postgresql.ENUM(*DISMISSAL_TYPE, name="dismissal_type", create_type=False),
            nullable=False,
        ),
        sa.Column("fielder_id", sa.Uuid(), nullable=True),
        sa.Column("credited_to_bowler", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["delivery_id"], ["deliveries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dismissed_player_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fielder_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("delivery_id", name="uq_dismissals_delivery"),
    )

    op.create_table(
        "innings_batting_stats",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("innings_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("batting_position", sa.Integer(), nullable=False),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.Column("balls_faced", sa.Integer(), nullable=False),
        sa.Column("fours", sa.Integer(), nullable=False),
        sa.Column("sixes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dismissal_type", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["innings_id"], ["innings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("innings_id", "player_id", name="uq_innings_batting_stats_player"),
    )

    op.create_table(
        "innings_bowling_stats",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("innings_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("legal_balls", sa.Integer(), nullable=False),
        sa.Column("runs_conceded", sa.Integer(), nullable=False),
        sa.Column("wickets", sa.Integer(), nullable=False),
        sa.Column("wides", sa.Integer(), nullable=False),
        sa.Column("no_balls", sa.Integer(), nullable=False),
        sa.Column("maidens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["innings_id"], ["innings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["match_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("innings_id", "player_id", name="uq_innings_bowling_stats_player"),
    )


def downgrade() -> None:
    op.drop_table("innings_bowling_stats")
    op.drop_table("innings_batting_stats")
    op.drop_table("dismissals")
    op.drop_table("deliveries")
    op.drop_table("score_snapshots")
    op.drop_index("uq_scoring_events_match_client_event", table_name="scoring_events")
    op.drop_table("scoring_events")
    op.drop_table("innings")
    op.drop_column("matches", "margin_wickets")
    op.drop_column("matches", "margin_runs")
    op.drop_column("matches", "winner_match_team_id")
    op.drop_column("matches", "result_type")
    bind = op.get_bind()
    postgresql.ENUM(name="result_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="scoring_event_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="dismissal_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="innings_status").drop(bind, checkfirst=True)
