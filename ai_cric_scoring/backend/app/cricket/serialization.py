from __future__ import annotations

from typing import Any
from uuid import UUID

from app.cricket.state import (
    BatterState,
    BowlerState,
    FallOfWicket,
    InningsState,
    OverBall,
    PartnershipState,
)
from app.cricket.types import DismissalType, InningsStatus


def _uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _uuid_or_none(value: object | None) -> UUID | None:
    if value is None:
        return None
    return _uuid(value)


def innings_to_dict(innings: InningsState) -> dict[str, Any]:
    partnership = innings.current_partnership
    return {
        "innings_number": innings.innings_number,
        "batting_team_id": str(innings.batting_team_id),
        "bowling_team_id": str(innings.bowling_team_id),
        "batting_player_ids": [str(item) for item in innings.batting_player_ids],
        "bowling_player_ids": [str(item) for item in innings.bowling_player_ids],
        "status": innings.status.value,
        "total_runs": innings.total_runs,
        "wickets": innings.wickets,
        "legal_balls": innings.legal_balls,
        "target_runs": innings.target_runs,
        "striker_id": str(innings.striker_id) if innings.striker_id else None,
        "non_striker_id": str(innings.non_striker_id) if innings.non_striker_id else None,
        "current_bowler_id": str(innings.current_bowler_id) if innings.current_bowler_id else None,
        "previous_bowler_id": str(innings.previous_bowler_id) if innings.previous_bowler_id else None,
        "needs_new_batter": innings.needs_new_batter,
        "needs_new_bowler": innings.needs_new_bowler,
        "vacant_end": innings.vacant_end,
        "next_batting_position": innings.next_batting_position,
        "batters": {
            str(player_id): {
                "player_id": str(batter.player_id),
                "batting_position": batter.batting_position,
                "runs": batter.runs,
                "balls_faced": batter.balls_faced,
                "fours": batter.fours,
                "sixes": batter.sixes,
                "is_out": batter.is_out,
                "dismissal_type": batter.dismissal_type.value if batter.dismissal_type else None,
                "is_retired_hurt": batter.is_retired_hurt,
                "is_retired_out": batter.is_retired_out,
            }
            for player_id, batter in innings.batters.items()
        },
        "bowlers": {
            str(player_id): {
                "player_id": str(bowler.player_id),
                "legal_balls": bowler.legal_balls,
                "runs_conceded": bowler.runs_conceded,
                "wickets": bowler.wickets,
                "wides": bowler.wides,
                "no_balls": bowler.no_balls,
                "maidens": bowler.maidens,
                "current_over_conceded": bowler.current_over_conceded,
            }
            for player_id, bowler in innings.bowlers.items()
        },
        "current_partnership": None
        if partnership is None
        else {
            "batter_1_id": str(partnership.batter_1_id),
            "batter_2_id": str(partnership.batter_2_id),
            "runs": partnership.runs,
            "legal_balls": partnership.legal_balls,
            "start_score": partnership.start_score,
        },
        "fall_of_wickets": [
            {
                "wicket_number": item.wicket_number,
                "team_score": item.team_score,
                "player_id": str(item.player_id),
                "legal_balls": item.legal_balls,
            }
            for item in innings.fall_of_wickets
        ],
        "current_over": [
            {"label": item.label, "runs": item.runs, "wicket": item.wicket, "legal": item.legal}
            for item in innings.current_over
        ],
    }


def innings_from_dict(data: dict[str, Any]) -> InningsState:
    partnership = data.get("current_partnership")
    return InningsState(
        innings_number=int(data["innings_number"]),
        batting_team_id=_uuid(data["batting_team_id"]),
        bowling_team_id=_uuid(data["bowling_team_id"]),
        batting_player_ids=tuple(_uuid(item) for item in data["batting_player_ids"]),
        bowling_player_ids=tuple(_uuid(item) for item in data["bowling_player_ids"]),
        status=InningsStatus(str(data["status"])),
        total_runs=int(data["total_runs"]),
        wickets=int(data["wickets"]),
        legal_balls=int(data["legal_balls"]),
        target_runs=data.get("target_runs"),
        striker_id=_uuid_or_none(data.get("striker_id")),
        non_striker_id=_uuid_or_none(data.get("non_striker_id")),
        current_bowler_id=_uuid_or_none(data.get("current_bowler_id")),
        previous_bowler_id=_uuid_or_none(data.get("previous_bowler_id")),
        needs_new_batter=bool(data.get("needs_new_batter", False)),
        needs_new_bowler=bool(data.get("needs_new_bowler", False)),
        vacant_end=data.get("vacant_end"),
        next_batting_position=int(data.get("next_batting_position", 3)),
        batters={
            _uuid(player_id): BatterState(
                player_id=_uuid(row["player_id"]),
                batting_position=int(row["batting_position"]),
                runs=int(row["runs"]),
                balls_faced=int(row["balls_faced"]),
                fours=int(row["fours"]),
                sixes=int(row["sixes"]),
                is_out=bool(row["is_out"]),
                dismissal_type=DismissalType(row["dismissal_type"]) if row.get("dismissal_type") else None,
                is_retired_hurt=bool(row.get("is_retired_hurt", False)),
                is_retired_out=bool(row.get("is_retired_out", False)),
            )
            for player_id, row in data.get("batters", {}).items()
        },
        bowlers={
            _uuid(player_id): BowlerState(
                player_id=_uuid(row["player_id"]),
                legal_balls=int(row["legal_balls"]),
                runs_conceded=int(row["runs_conceded"]),
                wickets=int(row["wickets"]),
                wides=int(row["wides"]),
                no_balls=int(row["no_balls"]),
                maidens=int(row["maidens"]),
                current_over_conceded=int(row.get("current_over_conceded", 0)),
            )
            for player_id, row in data.get("bowlers", {}).items()
        },
        current_partnership=None
        if not partnership
        else PartnershipState(
            batter_1_id=_uuid(partnership["batter_1_id"]),
            batter_2_id=_uuid(partnership["batter_2_id"]),
            runs=int(partnership["runs"]),
            legal_balls=int(partnership["legal_balls"]),
            start_score=int(partnership["start_score"]),
        ),
        fall_of_wickets=[
            FallOfWicket(
                wicket_number=int(item["wicket_number"]),
                team_score=int(item["team_score"]),
                player_id=_uuid(item["player_id"]),
                legal_balls=int(item["legal_balls"]),
            )
            for item in data.get("fall_of_wickets", [])
        ],
        current_over=[
            OverBall(
                label=str(item["label"]),
                runs=int(item["runs"]),
                wicket=bool(item["wicket"]),
                legal=bool(item["legal"]),
            )
            for item in data.get("current_over", [])
        ],
    )
