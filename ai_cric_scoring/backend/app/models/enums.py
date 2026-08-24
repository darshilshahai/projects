from enum import StrEnum

from sqlalchemy import Enum as SAEnum

from app.cricket.types import DismissalType, InningsStatus, ResultType, ScoringEventType

__all__ = [
    "BattingStyle",
    "BowlingStyle",
    "DismissalType",
    "InningsStatus",
    "MatchFormat",
    "MatchSide",
    "MatchStatus",
    "PlayerRole",
    "ResultType",
    "ScoringEventType",
    "TossDecision",
    "pg_enum",
]


class PlayerRole(StrEnum):
    BATTER = "BATTER"
    BOWLER = "BOWLER"
    ALL_ROUNDER = "ALL_ROUNDER"
    WICKET_KEEPER = "WICKET_KEEPER"
    WICKET_KEEPER_BATTER = "WICKET_KEEPER_BATTER"


class BattingStyle(StrEnum):
    RIGHT_HANDED = "RIGHT_HANDED"
    LEFT_HANDED = "LEFT_HANDED"
    UNKNOWN = "UNKNOWN"


class BowlingStyle(StrEnum):
    RIGHT_ARM_FAST = "RIGHT_ARM_FAST"
    RIGHT_ARM_MEDIUM = "RIGHT_ARM_MEDIUM"
    RIGHT_ARM_OFF_SPIN = "RIGHT_ARM_OFF_SPIN"
    RIGHT_ARM_LEG_SPIN = "RIGHT_ARM_LEG_SPIN"
    LEFT_ARM_FAST = "LEFT_ARM_FAST"
    LEFT_ARM_MEDIUM = "LEFT_ARM_MEDIUM"
    LEFT_ARM_ORTHODOX = "LEFT_ARM_ORTHODOX"
    LEFT_ARM_WRIST_SPIN = "LEFT_ARM_WRIST_SPIN"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class MatchFormat(StrEnum):
    T10 = "T10"
    T20 = "T20"
    ODI = "ODI"
    TEST = "TEST"
    CUSTOM = "CUSTOM"


class MatchStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    CANCELLED = "CANCELLED"


class TossDecision(StrEnum):
    BAT = "BAT"
    BOWL = "BOWL"


class MatchSide(StrEnum):
    TEAM_A = "TEAM_A"
    TEAM_B = "TEAM_B"


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        native_enum=True,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
