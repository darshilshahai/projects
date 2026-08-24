"""create_core_domain_models

Revision ID: c8e4a1f0b2d3
Revises:
Create Date: 2026-08-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c8e4a1f0b2d3"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLAYER_ROLE = ("BATTER", "BOWLER", "ALL_ROUNDER", "WICKET_KEEPER", "WICKET_KEEPER_BATTER")
BATTING_STYLE = ("RIGHT_HANDED", "LEFT_HANDED", "UNKNOWN")
BOWLING_STYLE = (
    "RIGHT_ARM_FAST",
    "RIGHT_ARM_MEDIUM",
    "RIGHT_ARM_OFF_SPIN",
    "RIGHT_ARM_LEG_SPIN",
    "LEFT_ARM_FAST",
    "LEFT_ARM_MEDIUM",
    "LEFT_ARM_ORTHODOX",
    "LEFT_ARM_WRIST_SPIN",
    "OTHER",
    "UNKNOWN",
)
MATCH_FORMAT = ("T10", "T20", "ODI", "TEST", "CUSTOM")
MATCH_STATUS = ("DRAFT", "LIVE", "COMPLETED", "ABANDONED", "CANCELLED")
MATCH_SIDE = ("TEAM_A", "TEAM_B")


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    enums = (
        ("player_role", PLAYER_ROLE),
        ("batting_style", BATTING_STYLE),
        ("bowling_style", BOWLING_STYLE),
        ("match_format", MATCH_FORMAT),
        ("match_status", MATCH_STATUS),
        ("match_side", MATCH_SIDE),
    )
    for name, values in enums:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(btrim(email)) > 0", name="ck_users_email_not_empty"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("short_name", sa.String(length=16), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_teams_name_not_empty"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "name", name="uq_teams_owner_name"),
    )

    op.create_table(
        "players",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("player_role", _enum("player_role", PLAYER_ROLE), nullable=False),
        sa.Column("batting_style", _enum("batting_style", BATTING_STYLE), nullable=False),
        sa.Column("bowling_style", _enum("bowling_style", BOWLING_STYLE), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_players_name_not_empty"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_players_owner_user_id", "players", ["owner_user_id"])

    op.create_table(
        "team_players",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "player_id", name="uq_team_players_team_player"),
    )
    op.create_index("ix_team_players_player_id", "team_players", ["player_id"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("format", _enum("match_format", MATCH_FORMAT), nullable=False),
        sa.Column("status", _enum("match_status", MATCH_STATUS), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("venue_name", sa.String(length=200), nullable=True),
        sa.Column("overs_per_innings", sa.Integer(), nullable=False),
        sa.Column("balls_per_over", sa.Integer(), server_default="6", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("overs_per_innings > 0", name="ck_matches_overs_per_innings_positive"),
        sa.CheckConstraint("balls_per_over > 0", name="ck_matches_balls_per_over_positive"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_matches_created_by_created_at",
        "matches",
        ["created_by_user_id", "created_at"],
    )

    op.create_table(
        "match_teams",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("team_name_snapshot", sa.String(length=120), nullable=False),
        sa.Column("side", _enum("match_side", MATCH_SIDE), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "side", name="uq_match_teams_match_side"),
        sa.UniqueConstraint("match_id", "team_id", name="uq_match_teams_match_team"),
    )
    op.create_index("ix_match_teams_team_id", "match_teams", ["team_id"])

    op.create_table(
        "match_players",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("match_team_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("display_name_snapshot", sa.String(length=160), nullable=False),
        sa.Column("is_playing", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_captain", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_wicket_keeper", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("batting_position", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_team_id"], ["match_teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "player_id", name="uq_match_players_match_player"),
    )
    op.create_index("ix_match_players_player_id", "match_players", ["player_id"])
    op.create_index("ix_match_players_match_team_id", "match_players", ["match_team_id"])


def downgrade() -> None:
    op.drop_index("ix_match_players_match_team_id", table_name="match_players")
    op.drop_index("ix_match_players_player_id", table_name="match_players")
    op.drop_table("match_players")
    op.drop_index("ix_match_teams_team_id", table_name="match_teams")
    op.drop_table("match_teams")
    op.drop_index("ix_matches_created_by_created_at", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_team_players_player_id", table_name="team_players")
    op.drop_table("team_players")
    op.drop_index("ix_players_owner_user_id", table_name="players")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    for name in (
        "match_side",
        "match_status",
        "match_format",
        "bowling_style",
        "batting_style",
        "player_role",
    ):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
