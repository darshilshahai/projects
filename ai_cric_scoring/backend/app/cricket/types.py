from enum import StrEnum


class DismissalType(StrEnum):
    BOWLED = "BOWLED"
    CAUGHT = "CAUGHT"
    LBW = "LBW"
    RUN_OUT = "RUN_OUT"
    STUMPED = "STUMPED"
    HIT_WICKET = "HIT_WICKET"
    RETIRED_OUT = "RETIRED_OUT"
    OBSTRUCTING_THE_FIELD = "OBSTRUCTING_THE_FIELD"
    HIT_THE_BALL_TWICE = "HIT_THE_BALL_TWICE"


class InningsStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class MatchPlayStatus(StrEnum):
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class ScoringEventType(StrEnum):
    INNINGS_STARTED = "INNINGS_STARTED"
    DELIVERY_RECORDED = "DELIVERY_RECORDED"
    BATTER_SELECTED = "BATTER_SELECTED"
    BOWLER_SELECTED = "BOWLER_SELECTED"
    BATTER_RETIRED = "BATTER_RETIRED"
    DELIVERY_VOIDED = "DELIVERY_VOIDED"
    INNINGS_COMPLETED = "INNINGS_COMPLETED"
    MATCH_COMPLETED = "MATCH_COMPLETED"


class ResultType(StrEnum):
    WON = "WON"
    TIED = "TIED"


class BatterStatus(StrEnum):
    BATTING = "BATTING"
    NOT_OUT = "NOT_OUT"
    OUT = "OUT"
    RETIRED_HURT = "RETIRED_HURT"
    RETIRED_OUT = "RETIRED_OUT"


BOWLER_CREDITED_DISMISSALS = {
    DismissalType.BOWLED,
    DismissalType.CAUGHT,
    DismissalType.LBW,
    DismissalType.STUMPED,
    DismissalType.HIT_WICKET,
}

NO_BALL_ALLOWED_DISMISSALS = {
    DismissalType.RUN_OUT,
    DismissalType.OBSTRUCTING_THE_FIELD,
    DismissalType.HIT_THE_BALL_TWICE,
}

WIDE_FORBIDDEN_DISMISSALS = {
    DismissalType.BOWLED,
    DismissalType.LBW,
    DismissalType.CAUGHT,
    DismissalType.HIT_THE_BALL_TWICE,
}

STRIKER_ONLY_DISMISSALS = {
    DismissalType.BOWLED,
    DismissalType.CAUGHT,
    DismissalType.LBW,
    DismissalType.STUMPED,
    DismissalType.HIT_WICKET,
    DismissalType.HIT_THE_BALL_TWICE,
}
