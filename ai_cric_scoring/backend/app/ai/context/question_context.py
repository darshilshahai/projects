from __future__ import annotations

from uuid import UUID

from app.ai.context.fact_package import FactItem, MatchFactPackage
from app.ai.schemas.match_chat import ContextMode, QuestionIntent


def select_facts(
    package: MatchFactPackage,
    intent: QuestionIntent,
    *,
    player_ids: list[UUID],
    team_ids: list[UUID],
    innings_number: int | None,
) -> list[FactItem]:
    mode = intent.context_mode
    if mode == ContextMode.NONE:
        return []
    if mode == ContextMode.RESULT_ONLY:
        return _of_types(package, {"match", "result", "innings", "team"})
    if mode == ContextMode.EXTRAS:
        return _of_types(package, {"match", "result", "innings", "team"})
    if mode == ContextMode.PARTNERSHIPS:
        return _of_types(package, {"result", "innings", "partnership", "team"})
    if mode == ContextMode.FIELDING:
        return _of_types(package, {"result", "batting"})
    if mode == ContextMode.OVER_RANGE:
        return _over_range_facts(package, intent, innings_number)
    if mode in {ContextMode.PLAYER_BATTING, ContextMode.PLAYER_BOWLING, ContextMode.PLAYER_FULL}:
        return _player_facts(package, player_ids, mode)
    if mode == ContextMode.COMPARISON:
        return _player_facts(package, player_ids, ContextMode.PLAYER_FULL)
    if mode == ContextMode.TEAM_INNINGS:
        return _team_facts(package, team_ids)
    return _analytical_facts(package, team_ids)


def compact_context(facts: list[FactItem], package: MatchFactPackage) -> dict:
    return {
        "match": package.match.model_dump(mode="json"),
        "result": package.result.model_dump(mode="json"),
        "facts": [
            {
                "id": item.id,
                "type": item.type,
                "label": item.label,
                "summary": item.summary,
                "innings_number": item.innings_number,
                "over_number": item.over_number,
                "match_player_id": str(item.match_player_id) if item.match_player_id else None,
                "match_team_id": str(item.match_team_id) if item.match_team_id else None,
            }
            for item in facts
        ],
        "fact_index": [{"id": item.id, "type": item.type, "label": item.label} for item in facts],
    }


def _of_types(package: MatchFactPackage, types: set[str]) -> list[FactItem]:
    return [item for item in package.facts if item.type in types]


def _player_facts(package: MatchFactPackage, player_ids: list[UUID], mode: ContextMode) -> list[FactItem]:
    types = {"player", "result", "innings"}
    if mode in {ContextMode.PLAYER_BATTING, ContextMode.PLAYER_FULL}:
        types.update({"batting", "partnership", "fall_of_wicket"})
    if mode in {ContextMode.PLAYER_BOWLING, ContextMode.PLAYER_FULL}:
        types.add("bowling")
    selected: list[FactItem] = []
    names = {item.label for item in package.facts if item.match_player_id in player_ids}
    for item in package.facts:
        if item.type == "result" or item.type == "innings":
            selected.append(item)
            continue
        if item.match_player_id in player_ids and item.type in types:
            selected.append(item)
            continue
        if item.type == "partnership" and any(name in item.label for name in names):
            selected.append(item)
    return selected


def _team_facts(package: MatchFactPackage, team_ids: list[UUID]) -> list[FactItem]:
    return [
        item
        for item in package.facts
        if item.type in {"result", "innings", "team", "partnership", "fall_of_wicket", "phase", "key_event"}
        and (item.match_team_id in team_ids or item.type in {"result", "partnership", "fall_of_wicket", "key_event"})
    ]


def _analytical_facts(package: MatchFactPackage, team_ids: list[UUID]) -> list[FactItem]:
    allowed = {
        "match",
        "result",
        "team",
        "innings",
        "batting",
        "bowling",
        "partnership",
        "fall_of_wicket",
        "phase",
        "key_event",
        "run_rate",
    }
    facts = [item for item in package.facts if item.type in allowed]
    if team_ids:
        batting = [
            item
            for item in facts
            if item.type == "batting" and (not team_ids or item.match_team_id in team_ids or item.match_team_id is None)
        ]
        bowling = [
            item
            for item in facts
            if item.type == "bowling" and (not team_ids or item.match_team_id in team_ids or item.match_team_id is None)
        ]
        others = [item for item in facts if item.type not in {"batting", "bowling"}]
        return others + batting[:8] + bowling[:8]
    batting = sorted(
        [item for item in facts if item.type == "batting"],
        key=lambda item: int(item.values.get("runs") or 0),
        reverse=True,
    )[:6]
    bowling = sorted(
        [item for item in facts if item.type == "bowling"],
        key=lambda item: int(item.values.get("wickets") or 0),
        reverse=True,
    )[:6]
    others = [item for item in facts if item.type not in {"batting", "bowling", "over"}]
    return others + batting + bowling


def _over_range_facts(
    package: MatchFactPackage,
    intent: QuestionIntent,
    innings_number: int | None,
) -> list[FactItem]:
    overs = [item for item in package.facts if item.type == "over"]
    if innings_number is not None:
        overs = [item for item in overs if item.innings_number == innings_number]
    start, end = resolve_over_window(overs, intent)
    window = [
        item
        for item in overs
        if item.over_number is not None and start is not None and end is not None and start <= item.over_number <= end
    ]
    related = [
        item
        for item in package.facts
        if item.type in {"result", "innings", "fall_of_wicket", "key_event", "phase"}
        and (innings_number is None or item.innings_number == innings_number or item.type == "result")
    ]
    return related + window


def resolve_over_window(overs: list[FactItem], intent: QuestionIntent) -> tuple[int | None, int | None]:
    if intent.over_start is not None and intent.over_end is not None:
        return intent.over_start, intent.over_end
    numbers = sorted(item.over_number for item in overs if item.over_number is not None)
    if not numbers:
        return None, None
    if intent.last_n_overs:
        start = numbers[-1] - intent.last_n_overs + 1
        return max(numbers[0], start), numbers[-1]
    return numbers[0], numbers[-1]
