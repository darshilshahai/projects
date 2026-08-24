from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from app.ai.context.fact_package import FactItem, MatchFactPackage
from app.ai.schemas.match_chat import QuestionIntent


@dataclass(frozen=True)
class ResolvedPlayer:
    match_player_id: UUID
    name: str


@dataclass(frozen=True)
class ResolvedTeam:
    match_team_id: UUID
    name: str


@dataclass
class EntityResolution:
    players: list[ResolvedPlayer]
    teams: list[ResolvedTeam]
    innings_number: int | None
    ambiguous_players: list[ResolvedPlayer]
    ambiguous_teams: list[ResolvedTeam]
    needs_player_clarification: bool = False
    needs_team_clarification: bool = False
    needs_innings_clarification: bool = False


_STOP = {
    "the",
    "a",
    "an",
    "how",
    "many",
    "did",
    "does",
    "do",
    "what",
    "who",
    "why",
    "where",
    "when",
    "which",
    "was",
    "were",
    "is",
    "are",
    "in",
    "on",
    "of",
    "to",
    "and",
    "or",
    "for",
    "with",
    "this",
    "that",
    "match",
    "score",
    "runs",
    "run",
    "balls",
    "ball",
    "wickets",
    "wicket",
    "overs",
    "over",
    "team",
    "player",
    "best",
    "most",
    "top",
    "between",
    "last",
    "first",
    "second",
    "compare",
    "vs",
    "versus",
}

_PLAYER_PRONOUNS = re.compile(r"\b(he|him|his|she|her)\b", re.I)
_TEAM_PRONOUNS = re.compile(r"\b(we|our|us|they|them|their)\b", re.I)


def _norm(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_entities(
    question: str,
    intent: QuestionIntent,
    package: MatchFactPackage,
    *,
    last_player_id: UUID | None = None,
    last_team_id: UUID | None = None,
    last_innings_number: int | None = None,
) -> EntityResolution:
    players = _player_catalog(package)
    teams = _team_catalog(package)
    mentioned_players = _match_players(question, players, intent.player_names)
    mentioned_teams = _match_teams(question, teams, intent.team_names)

    ambiguous_players: list[ResolvedPlayer] = []
    if _PLAYER_PRONOUNS.search(question) and last_player_id and not mentioned_players:
        named = next((item for item in players if item.match_player_id == last_player_id), None)
        if named is not None:
            mentioned_players = [named]

    if _looks_like_player_query(intent) and not mentioned_players:
        first_name_hits = _first_name_collisions(question, players)
        if len(first_name_hits) > 1:
            ambiguous_players = first_name_hits
        elif len(first_name_hits) == 1:
            mentioned_players = first_name_hits

    unique_players = _unique_players(mentioned_players)
    if len(unique_players) > 1 and _single_name_query(question, unique_players):
        ambiguous_players = unique_players
        unique_players = []

    if _TEAM_PRONOUNS.search(question) and last_team_id and not mentioned_teams:
        named_team = next((item for item in teams if item.match_team_id == last_team_id), None)
        if named_team is not None:
            mentioned_teams = [named_team]

    innings = intent.innings_hint
    if intent.wants_chase:
        innings = _chase_innings(package)
    if innings is None and last_innings_number is not None and intent.type.value == "OVER_RANGE":
        innings = last_innings_number

    needs_innings = False
    if intent.type.value == "OVER_RANGE" and innings is None:
        innings_count = len({item.innings_number for item in package.facts if item.type == "innings"})
        needs_innings = innings_count > 1

    needs_team = False
    if intent.type.value == "WHY_RESULT" and _TEAM_PRONOUNS.search(question) and not mentioned_teams:
        needs_team = True

    return EntityResolution(
        players=unique_players,
        teams=mentioned_teams,
        innings_number=innings,
        ambiguous_players=ambiguous_players,
        ambiguous_teams=teams if needs_team else [],
        needs_player_clarification=bool(ambiguous_players),
        needs_team_clarification=needs_team,
        needs_innings_clarification=needs_innings,
    )


def _player_catalog(package: MatchFactPackage) -> list[ResolvedPlayer]:
    seen: dict[UUID, ResolvedPlayer] = {}
    for item in package.facts:
        if item.match_player_id is None or item.type not in {"player", "batting", "bowling"}:
            continue
        seen[item.match_player_id] = ResolvedPlayer(item.match_player_id, item.label)
    return list(seen.values())


def _team_catalog(package: MatchFactPackage) -> list[ResolvedTeam]:
    teams: list[ResolvedTeam] = []
    if package.match.team_a_id and package.match.team_a_name:
        teams.append(ResolvedTeam(package.match.team_a_id, package.match.team_a_name))
    if package.match.team_b_id and package.match.team_b_name:
        teams.append(ResolvedTeam(package.match.team_b_id, package.match.team_b_name))
    return teams


def _match_players(question: str, players: list[ResolvedPlayer], extra: list[str]) -> list[ResolvedPlayer]:
    text = _norm(question)
    hits: list[ResolvedPlayer] = []
    for player in players:
        if _name_in_text(player.name, text):
            hits.append(player)
    for name in extra:
        for player in players:
            if _name_in_text(player.name, _norm(name)) or _name_in_text(name, text):
                hits.append(player)
    if hits:
        return hits
    for player in players:
        parts = _norm(player.name).split()
        if not parts:
            continue
        first = parts[0]
        if not re.search(rf"\b{re.escape(first)}\b", text):
            continue
        same = [item for item in players if _norm(item.name).split()[:1] == [first]]
        if len(same) == 1:
            hits.append(player)
    return hits


def _match_teams(question: str, teams: list[ResolvedTeam], extra: list[str]) -> list[ResolvedTeam]:
    text = _norm(question)
    hits: list[ResolvedTeam] = []
    for team in teams:
        if _team_in_text(team.name, text):
            hits.append(team)
    for name in extra:
        for team in teams:
            if _team_in_text(team.name, _norm(name)) or _team_in_text(name, text):
                hits.append(team)
    return _unique_teams(hits)


def _name_in_text(name: str, text: str) -> bool:
    full = _norm(name)
    if not full:
        return False
    if re.search(rf"\b{re.escape(full)}\b", text):
        return True
    parts = full.split()
    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        if re.search(rf"\b{re.escape(full[0])} {re.escape(last)}\b", text):
            return True
        if re.search(rf"\b{re.escape(first)}\b", text) and re.search(rf"\b{re.escape(last)}\b", text):
            return True
    return False


def _team_in_text(name: str, text: str) -> bool:
    full = _norm(name)
    if not full:
        return False
    if re.search(rf"\b{re.escape(full)}\b", text):
        return True
    tokens = [token for token in full.split() if token not in {"cc", "xi", "club", "the"}]
    return any(len(token) >= 4 and re.search(rf"\b{re.escape(token)}\b", text) for token in tokens)


def _first_name_collisions(question: str, players: list[ResolvedPlayer]) -> list[ResolvedPlayer]:
    tokens = [token for token in _norm(question).split() if token not in _STOP and len(token) > 1]
    hits: list[ResolvedPlayer] = []
    for token in tokens:
        matched = [player for player in players if _norm(player.name).split()[:1] == [token]]
        if len(matched) > 1:
            return matched
        hits.extend(matched)
    return _unique_players(hits)


def _single_name_query(question: str, players: list[ResolvedPlayer]) -> bool:
    firsts = {_norm(player.name).split()[0] for player in players}
    if len(firsts) != 1:
        return False
    first = next(iter(firsts))
    return bool(re.search(rf"\b{re.escape(first)}\b", _norm(question))) and not any(
        re.search(rf"\b{re.escape(_norm(player.name))}\b", _norm(question)) for player in players
    )


def _looks_like_player_query(intent: QuestionIntent) -> bool:
    return intent.type.value in {
        "DIRECT_STAT",
        "PLAYER_PERFORMANCE",
        "COMPARISON",
        "BATTING",
        "BOWLING",
    }


def _unique_players(players: list[ResolvedPlayer]) -> list[ResolvedPlayer]:
    seen: dict[UUID, ResolvedPlayer] = {}
    for player in players:
        seen[player.match_player_id] = player
    return list(seen.values())


def _unique_teams(teams: list[ResolvedTeam]) -> list[ResolvedTeam]:
    seen: dict[UUID, ResolvedTeam] = {}
    for team in teams:
        seen[team.match_team_id] = team
    return list(seen.values())


def _chase_innings(package: MatchFactPackage) -> int | None:
    numbers = sorted({item.innings_number for item in package.facts if item.type == "innings" and item.innings_number})
    if not numbers:
        return None
    return numbers[-1]


def facts_for_player(package: MatchFactPackage, player_id: UUID, types: set[str] | None = None) -> list[FactItem]:
    return [
        item for item in package.facts if item.match_player_id == player_id and (types is None or item.type in types)
    ]
