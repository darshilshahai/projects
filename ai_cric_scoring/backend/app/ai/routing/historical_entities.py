from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import UUID

from app.ai.schemas.historical import HistoricalIntent
from app.models.player import Player
from app.models.team import Team

_STOP = {
    "the",
    "a",
    "an",
    "how",
    "has",
    "have",
    "what",
    "who",
    "why",
    "in",
    "his",
    "her",
    "their",
    "last",
    "matches",
    "match",
    "average",
    "compare",
    "and",
    "versus",
    "recently",
    "performed",
    "player",
    "team",
}


@dataclass
class NamedEntity:
    id: UUID
    name: str


@dataclass
class HistoricalResolution:
    players: list[NamedEntity] = field(default_factory=list)
    teams: list[NamedEntity] = field(default_factory=list)
    ambiguous_players: list[NamedEntity] = field(default_factory=list)
    ambiguous_teams: list[NamedEntity] = field(default_factory=list)
    needs_player_clarification: bool = False
    needs_team_clarification: bool = False
    missing_player: str | None = None
    missing_team: str | None = None


def resolve_historical_entities(
    question: str,
    intent: HistoricalIntent,
    players: list[Player],
    teams: list[Team],
) -> HistoricalResolution:
    text = _norm(question)
    player_hits = _match_names(text, [NamedEntity(item.id, item.name) for item in players])
    team_hits = _match_names(text, [NamedEntity(item.id, item.name) for item in teams])
    unique_players = _unique(player_hits)
    unique_teams = _unique(team_hits)

    resolution = HistoricalResolution()
    if _needs_players(intent) and len(unique_players) > 1 and _single_token_name(text, unique_players):
        resolution.ambiguous_players = unique_players
        resolution.needs_player_clarification = True
    elif _needs_players(intent) and not unique_players:
        guessed = _first_name_guess(text)
        resolution.missing_player = guessed
    else:
        resolution.players = unique_players

    if _needs_teams(intent) and len(unique_teams) > 1 and _single_token_name(text, unique_teams):
        resolution.ambiguous_teams = unique_teams
        resolution.needs_team_clarification = True
    elif _needs_teams(intent) and not unique_teams and _team_pronoun(text):
        resolution.needs_team_clarification = True
        resolution.ambiguous_teams = [NamedEntity(item.id, item.name) for item in teams[:8]]
    else:
        resolution.teams = unique_teams
    return resolution


def _needs_players(intent: HistoricalIntent) -> bool:
    return intent.type.value in {
        "PLAYER_STATS",
        "PLAYER_FORM",
        "PLAYER_COMPARISON",
        "HISTORICAL_TREND",
        "DIRECT_HISTORICAL_STAT",
    }


def _needs_teams(intent: HistoricalIntent) -> bool:
    return intent.type.value in {
        "TEAM_STATS",
        "TEAM_FORM",
        "TEAM_COMPARISON",
        "HEAD_TO_HEAD",
    }


def _match_names(text: str, catalog: list[NamedEntity]) -> list[NamedEntity]:
    exact: list[NamedEntity] = []
    initials: list[NamedEntity] = []
    first_token: list[NamedEntity] = []
    for item in catalog:
        full = _norm(item.name)
        if not full:
            continue
        if re.search(rf"\b{re.escape(full)}\b", text):
            exact.append(item)
            continue
        parts = full.split()
        if len(parts) >= 2:
            initial = f"{parts[0][0]} {parts[-1]}"
            if re.search(rf"\b{re.escape(initial)}\b", text):
                initials.append(item)
                continue
        if parts and parts[0] not in _STOP and re.search(rf"\b{re.escape(parts[0])}\b", text):
            first_token.append(item)
    if exact:
        return _prefer_longest(exact)
    if initials:
        return initials
    return first_token


def _prefer_longest(hits: list[NamedEntity]) -> list[NamedEntity]:
    names = [_norm(item.name) for item in hits]
    kept: list[NamedEntity] = []
    for item in hits:
        full = _norm(item.name)
        if any(other != full and other.startswith(full + " ") for other in names):
            continue
        kept.append(item)
    return kept


def _unique(items: list[NamedEntity]) -> list[NamedEntity]:
    seen: dict[UUID, NamedEntity] = {}
    for item in items:
        seen[item.id] = item
    return list(seen.values())


def _single_token_name(text: str, items: list[NamedEntity]) -> bool:
    firsts = {_norm(item.name).split()[0] for item in items if _norm(item.name).split()}
    return len(firsts) == 1 and any(re.search(rf"\b{re.escape(name)}\b", text) for name in firsts)


def _first_name_guess(text: str) -> str | None:
    for token in text.split():
        if token not in _STOP and len(token) >= 3:
            return token
    return None


def _team_pronoun(text: str) -> bool:
    return bool(re.search(r"\b(we|our|us)\b", text))


def _norm(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()
