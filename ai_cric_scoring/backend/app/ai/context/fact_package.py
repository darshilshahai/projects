from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.ai import FACTS_VERSION
from app.analytics.key_events import detect_key_events
from app.analytics.phases import summarize_phases
from app.cricket.formatters import format_result, run_rate, scorecard_rate
from app.models.enums import MatchFormat, TossDecision
from app.schemas.scorecard import InningsScorecard, MatchScorecardResponse


class FactItem(BaseModel):
    id: str
    type: str
    label: str
    summary: str
    values: dict[str, Any] = Field(default_factory=dict)
    innings_number: int | None = None
    match_player_id: uuid.UUID | None = None
    match_team_id: uuid.UUID | None = None
    over_number: int | None = None


class TossFacts(BaseModel):
    winner_match_team_id: uuid.UUID | None = None
    winner_name: str | None = None
    decision: TossDecision | None = None


class ResultFacts(BaseModel):
    result_type: str | None = None
    winner_match_team_id: uuid.UUID | None = None
    winner_name: str | None = None
    margin_runs: int | None = None
    margin_wickets: int | None = None
    summary: str | None = None


class MatchMetaFacts(BaseModel):
    id: uuid.UUID
    name: str | None
    format: MatchFormat
    venue_name: str | None
    overs_per_innings: int
    balls_per_over: int
    players_per_team: int
    team_a_id: uuid.UUID | None = None
    team_a_name: str | None = None
    team_b_id: uuid.UUID | None = None
    team_b_name: str | None = None


class PotmCandidate(BaseModel):
    match_player_id: uuid.UUID
    name: str
    fact_ids: list[str]
    runs: int = 0
    balls: int = 0
    wickets: int = 0
    runs_conceded: int = 0


class MatchFactPackage(BaseModel):
    facts_version: str = FACTS_VERSION
    match: MatchMetaFacts
    toss: TossFacts
    result: ResultFacts
    facts: list[FactItem] = Field(default_factory=list)
    potm_candidates: list[PotmCandidate] = Field(default_factory=list)

    def fact_by_id(self) -> dict[str, FactItem]:
        return {item.id: item for item in self.facts}

    def fact_ids(self) -> set[str]:
        return {item.id for item in self.facts}

    def player_ids(self) -> set[uuid.UUID]:
        return {item.match_player_id for item in self.facts if item.match_player_id is not None}

    def team_ids(self) -> set[uuid.UUID]:
        ids = {item.match_team_id for item in self.facts if item.match_team_id is not None}
        if self.match.team_a_id is not None:
            ids.add(self.match.team_a_id)
        if self.match.team_b_id is not None:
            ids.add(self.match.team_b_id)
        return ids

    def player_name(self, player_id: uuid.UUID) -> str | None:
        for item in self.facts:
            if item.match_player_id == player_id and item.type in {"player", "batting", "bowling", "potm_candidate"}:
                return item.label
        return None

    def team_name(self, team_id: uuid.UUID) -> str | None:
        if self.match.team_a_id == team_id:
            return self.match.team_a_name
        if self.match.team_b_id == team_id:
            return self.match.team_b_name
        for item in self.facts:
            if item.match_team_id == team_id and item.type == "team":
                return item.label
        return None

    def allowed_numbers(self) -> set[str]:
        allowed: set[str] = {"0", "1", "2"}
        for item in self.facts:
            _collect_numbers(item.values, allowed)
            _collect_numbers_from_text(item.summary, allowed)
        _collect_numbers(self.result.model_dump(), allowed)
        _collect_numbers(
            {
                "overs": self.match.overs_per_innings,
                "balls": self.match.balls_per_over,
                "players": self.match.players_per_team,
            },
            allowed,
        )
        return allowed

    def to_prompt_context(self) -> dict[str, Any]:
        batting = [item.model_dump(mode="json") for item in self.facts if item.type == "batting"]
        bowling = [item.model_dump(mode="json") for item in self.facts if item.type == "bowling"]
        partnerships = [item.model_dump(mode="json") for item in self.facts if item.type == "partnership"]
        fow = [item.model_dump(mode="json") for item in self.facts if item.type == "fall_of_wicket"]
        overs = [
            {
                "id": item.id,
                "innings_number": item.innings_number,
                "over": item.over_number,
                "runs": item.values.get("runs"),
                "wickets": item.values.get("wickets"),
            }
            for item in self.facts
            if item.type == "over"
        ]
        return {
            "match": self.match.model_dump(mode="json"),
            "toss": self.toss.model_dump(mode="json"),
            "result": self.result.model_dump(mode="json"),
            "innings": [item.model_dump(mode="json") for item in self.facts if item.type == "innings"],
            "batting": batting,
            "bowling": bowling,
            "partnerships": partnerships,
            "fall_of_wickets": fow,
            "over_summaries": overs,
            "phases": [item.model_dump(mode="json") for item in self.facts if item.type == "phase"],
            "key_events": [item.model_dump(mode="json") for item in self.facts if item.type == "key_event"],
            "potm_candidates": [item.model_dump(mode="json") for item in self.potm_candidates],
            "fact_index": [{"id": item.id, "type": item.type, "label": item.label} for item in self.facts],
        }


def assemble_fact_package(
    scorecard: MatchScorecardResponse,
    *,
    toss_winner_match_team_id: uuid.UUID | None = None,
    toss_decision: TossDecision | None = None,
) -> MatchFactPackage:
    header = scorecard.match
    team_names = {team.match_team_id: team.name for team in (header.team_a, header.team_b) if team is not None}
    toss_name = team_names.get(toss_winner_match_team_id) if toss_winner_match_team_id else None
    result_summary = format_result(
        result_type=header.result_type,
        winner_name=header.winner_name,
        margin_runs=header.margin_runs,
        margin_wickets=header.margin_wickets,
    )
    facts: list[FactItem] = [
        FactItem(
            id="match",
            type="match",
            label=header.name
            or (
                f"{header.team_a.name if header.team_a else 'Team A'} vs "
                f"{header.team_b.name if header.team_b else 'Team B'}"
            ),
            summary=(
                f"{header.format.value} · {header.overs_per_innings} overs · "
                f"{header.balls_per_over} balls/over · venue {header.venue_name or 'unspecified'}"
            ),
            values={
                "format": header.format.value,
                "overs_per_innings": header.overs_per_innings,
                "balls_per_over": header.balls_per_over,
                "players_per_team": header.players_per_team,
            },
        ),
        FactItem(
            id="result",
            type="result",
            label=result_summary or "No result",
            summary=result_summary or "No result recorded.",
            values={
                "result_type": header.result_type.value if header.result_type else None,
                "winner_match_team_id": str(header.winner_match_team_id) if header.winner_match_team_id else None,
                "winner_name": header.winner_name,
                "margin_runs": header.margin_runs,
                "margin_wickets": header.margin_wickets,
            },
            match_team_id=header.winner_match_team_id,
        ),
    ]
    for team in (header.team_a, header.team_b):
        if team is None:
            continue
        facts.append(
            FactItem(
                id=f"team_{team.match_team_id}",
                type="team",
                label=team.name,
                summary=team.name,
                match_team_id=team.match_team_id,
            )
        )

    player_names: dict[uuid.UUID, str] = {}
    batting_totals: dict[uuid.UUID, dict[str, int]] = {}
    bowling_totals: dict[uuid.UUID, dict[str, int]] = {}

    for innings in scorecard.innings:
        facts.extend(
            _innings_facts(
                innings,
                match_format=header.format,
                overs_per_innings=header.overs_per_innings,
                balls_per_over=header.balls_per_over,
            )
        )
        for batter in innings.batting:
            player_names[batter.match_player_id] = batter.name
            totals = batting_totals.setdefault(batter.match_player_id, {"runs": 0, "balls": 0})
            totals["runs"] += batter.runs
            totals["balls"] += batter.balls
            facts.append(
                FactItem(
                    id=f"player_{batter.match_player_id}",
                    type="player",
                    label=batter.name,
                    summary=batter.name,
                    match_player_id=batter.match_player_id,
                    match_team_id=innings.batting_team.match_team_id,
                )
            )
        for bowler in innings.bowling:
            player_names[bowler.match_player_id] = bowler.name
            totals = bowling_totals.setdefault(bowler.match_player_id, {"wickets": 0, "runs_conceded": 0})
            totals["wickets"] += bowler.wickets
            totals["runs_conceded"] += bowler.runs_conceded
            facts.append(
                FactItem(
                    id=f"player_{bowler.match_player_id}",
                    type="player",
                    label=bowler.name,
                    summary=bowler.name,
                    match_player_id=bowler.match_player_id,
                    match_team_id=innings.bowling_team.match_team_id,
                )
            )
        for waiting in innings.yet_to_bat:
            player_names[waiting.match_player_id] = waiting.name
            facts.append(
                FactItem(
                    id=f"player_{waiting.match_player_id}",
                    type="player",
                    label=waiting.name,
                    summary=waiting.name,
                    match_player_id=waiting.match_player_id,
                    match_team_id=innings.batting_team.match_team_id,
                )
            )

    facts = _dedupe_facts(facts)
    potm = _potm_candidates(player_names, batting_totals, bowling_totals, facts)
    for candidate in potm:
        potm_id = f"potm_{candidate.match_player_id}"
        facts.append(
            FactItem(
                id=potm_id,
                type="potm_candidate",
                label=candidate.name,
                summary=(
                    f"{candidate.name}: {candidate.runs} runs from {candidate.balls} balls, "
                    f"{candidate.wickets} wickets for {candidate.runs_conceded}."
                ),
                values={
                    "runs": candidate.runs,
                    "balls": candidate.balls,
                    "wickets": candidate.wickets,
                    "runs_conceded": candidate.runs_conceded,
                },
                match_player_id=candidate.match_player_id,
            )
        )
        candidate.fact_ids = [potm_id, *candidate.fact_ids]

    return MatchFactPackage(
        match=MatchMetaFacts(
            id=header.id,
            name=header.name,
            format=header.format,
            venue_name=header.venue_name,
            overs_per_innings=header.overs_per_innings,
            balls_per_over=header.balls_per_over,
            players_per_team=header.players_per_team,
            team_a_id=header.team_a.match_team_id if header.team_a else None,
            team_a_name=header.team_a.name if header.team_a else None,
            team_b_id=header.team_b.match_team_id if header.team_b else None,
            team_b_name=header.team_b.name if header.team_b else None,
        ),
        toss=TossFacts(
            winner_match_team_id=toss_winner_match_team_id,
            winner_name=toss_name,
            decision=toss_decision,
        ),
        result=ResultFacts(
            result_type=header.result_type.value if header.result_type else None,
            winner_match_team_id=header.winner_match_team_id,
            winner_name=header.winner_name,
            margin_runs=header.margin_runs,
            margin_wickets=header.margin_wickets,
            summary=result_summary,
        ),
        facts=facts,
        potm_candidates=potm,
    )


def _innings_facts(
    innings: InningsScorecard,
    *,
    match_format: MatchFormat,
    overs_per_innings: int,
    balls_per_over: int,
) -> list[FactItem]:
    number = innings.number
    facts: list[FactItem] = [
        FactItem(
            id=f"inn_{number}",
            type="innings",
            label=f"Innings {number} {innings.batting_team.name}",
            summary=(
                f"{innings.batting_team.name} {innings.runs}/{innings.wickets} in {innings.overs} "
                f"(RR {innings.run_rate})" + (f", target {innings.target}" if innings.target is not None else "")
            ),
            values={
                "runs": innings.runs,
                "wickets": innings.wickets,
                "legal_balls": innings.legal_balls,
                "overs": innings.overs,
                "run_rate": innings.run_rate,
                "target": innings.target,
                "extras": innings.extras.total,
            },
            innings_number=number,
            match_team_id=innings.batting_team.match_team_id,
        )
    ]
    for batter in innings.batting:
        facts.append(
            FactItem(
                id=f"bat_{number}_{batter.match_player_id}",
                type="batting",
                label=batter.name,
                summary=(
                    f"{batter.name} {batter.runs} ({batter.balls}), 4s {batter.fours}, 6s {batter.sixes}, "
                    f"SR {batter.strike_rate}, {batter.dismissal_text}"
                ),
                values={
                    "runs": batter.runs,
                    "balls": batter.balls,
                    "fours": batter.fours,
                    "sixes": batter.sixes,
                    "strike_rate": batter.strike_rate,
                    "dismissal": batter.dismissal_text,
                    "position": batter.batting_position,
                },
                innings_number=number,
                match_player_id=batter.match_player_id,
                match_team_id=innings.batting_team.match_team_id,
            )
        )
    for bowler in innings.bowling:
        facts.append(
            FactItem(
                id=f"bowl_{number}_{bowler.match_player_id}",
                type="bowling",
                label=bowler.name,
                summary=(
                    f"{bowler.name} {bowler.overs}-{bowler.maidens}-{bowler.runs_conceded}-{bowler.wickets}, "
                    f"econ {bowler.economy}, wides {bowler.wides}, nb {bowler.no_balls}"
                ),
                values={
                    "overs": bowler.overs,
                    "maidens": bowler.maidens,
                    "runs_conceded": bowler.runs_conceded,
                    "wickets": bowler.wickets,
                    "economy": bowler.economy,
                    "wides": bowler.wides,
                    "no_balls": bowler.no_balls,
                    "legal_balls": bowler.legal_balls,
                },
                innings_number=number,
                match_player_id=bowler.match_player_id,
                match_team_id=innings.bowling_team.match_team_id,
            )
        )
    for index, stand in enumerate(innings.partnerships, start=1):
        facts.append(
            FactItem(
                id=f"pship_{number}_{index}",
                type="partnership",
                label=f"{stand.batter_1_name} / {stand.batter_2_name}",
                summary=(
                    f"{stand.batter_1_name} and {stand.batter_2_name} added {stand.runs} runs "
                    f"from {stand.legal_balls} legal balls ({stand.start_score}-{stand.end_score})."
                ),
                values={
                    "runs": stand.runs,
                    "legal_balls": stand.legal_balls,
                    "start_score": stand.start_score,
                    "end_score": stand.end_score,
                    "batter_1_runs": stand.batter_1_runs,
                    "batter_2_runs": stand.batter_2_runs,
                    "order": index,
                },
                innings_number=number,
            )
        )
    for wicket in innings.fall_of_wickets:
        facts.append(
            FactItem(
                id=f"fow_{number}_{wicket.wicket_number}",
                type="fall_of_wicket",
                label=f"{wicket.wicket_number}-{wicket.score} {wicket.player_name}",
                summary=(
                    f"Wicket {wicket.wicket_number}: {wicket.player_name} at {wicket.score} in over {wicket.overs}."
                ),
                values={
                    "wicket": wicket.wicket_number,
                    "score": wicket.score,
                    "over": wicket.overs,
                    "legal_balls": wicket.legal_balls,
                },
                innings_number=number,
                match_player_id=wicket.player_id,
            )
        )
    for over in innings.overs_summary:
        facts.append(
            FactItem(
                id=f"over_{number}_{over.over_number}",
                type="over",
                label=f"Over {over.over_number}",
                summary=f"Over {over.over_number}: {over.runs} runs, {over.wickets} wickets.",
                values={
                    "over": over.over_number,
                    "runs": over.runs,
                    "wickets": over.wickets,
                    "legal_balls": over.legal_balls,
                },
                innings_number=number,
                over_number=over.over_number,
            )
        )
    for phase in summarize_phases(
        innings.overs_summary,
        match_format=match_format,
        overs_per_innings=overs_per_innings,
        balls_per_over=balls_per_over,
    ):
        facts.append(
            FactItem(
                id=f"phase_{number}_{phase.key}",
                type="phase",
                label=phase.label,
                summary=(
                    f"{phase.label} (overs {phase.start_over}-{phase.end_over}): "
                    f"{phase.runs}/{phase.wickets}, RR {phase.run_rate}, "
                    f"{phase.boundaries} boundaries, {phase.dots} dots."
                ),
                values={
                    "runs": phase.runs,
                    "wickets": phase.wickets,
                    "legal_balls": phase.legal_balls,
                    "run_rate": phase.run_rate,
                    "boundaries": phase.boundaries,
                    "dots": phase.dots,
                    "start_over": phase.start_over,
                    "end_over": phase.end_over,
                },
                innings_number=number,
                match_team_id=innings.batting_team.match_team_id,
            )
        )
    for index, event in enumerate(
        detect_key_events(
            innings_number=number,
            overs=innings.overs_summary,
            fall_of_wickets=innings.fall_of_wickets,
            partnerships=innings.partnerships,
            balls_per_over=balls_per_over,
            target=innings.target,
        ),
        start=1,
    ):
        facts.append(
            FactItem(
                id=f"event_{number}_{event.event_type.lower()}_{index}",
                type="key_event",
                label=event.label,
                summary=event.summary,
                values={"event_type": event.event_type, **event.values},
                innings_number=number,
                over_number=event.over_number,
            )
        )
    mid_over = max(1, overs_per_innings // 2)
    late_over = max(mid_over + 1, (overs_per_innings * 3) // 4)
    facts.extend(_run_rate_markers(innings, mid_over, late_over, balls_per_over))
    return facts


def _run_rate_markers(
    innings: InningsScorecard,
    mid_over: int,
    late_over: int,
    balls_per_over: int,
) -> list[FactItem]:
    facts: list[FactItem] = []
    for checkpoint, over_number in (("mid", mid_over), ("late", late_over)):
        selected = [item for item in innings.overs_summary if item.over_number <= over_number]
        if not selected:
            continue
        runs = sum(item.runs for item in selected)
        balls = sum(item.legal_balls for item in selected)
        rate = scorecard_rate(run_rate(runs, balls, balls_per_over))
        facts.append(
            FactItem(
                id=f"rr_{innings.number}_{checkpoint}",
                type="run_rate",
                label=f"RR after over {over_number}",
                summary=f"Innings {innings.number} run rate after over {over_number}: {rate} ({runs} runs).",
                values={"over": over_number, "runs": runs, "legal_balls": balls, "run_rate": rate},
                innings_number=innings.number,
                over_number=over_number,
            )
        )
    return facts


def _potm_candidates(
    names: dict[uuid.UUID, str],
    batting: dict[uuid.UUID, dict[str, int]],
    bowling: dict[uuid.UUID, dict[str, int]],
    facts: list[FactItem],
) -> list[PotmCandidate]:
    scored = sorted(batting.items(), key=lambda item: (-item[1]["runs"], item[1]["balls"]))
    taken = sorted(bowling.items(), key=lambda item: (-item[1]["wickets"], item[1]["runs_conceded"]))
    selected: dict[uuid.UUID, PotmCandidate] = {}
    related: dict[uuid.UUID, list[str]] = {}
    for item in facts:
        if item.match_player_id is None or item.type not in {"batting", "bowling"}:
            continue
        related.setdefault(item.match_player_id, []).append(item.id)

    def add(player_id: uuid.UUID) -> None:
        bat = batting.get(player_id, {"runs": 0, "balls": 0})
        bowl = bowling.get(player_id, {"wickets": 0, "runs_conceded": 0})
        selected[player_id] = PotmCandidate(
            match_player_id=player_id,
            name=names.get(player_id, "Unknown"),
            fact_ids=list(dict.fromkeys(related.get(player_id, []))),
            runs=bat["runs"],
            balls=bat["balls"],
            wickets=bowl["wickets"],
            runs_conceded=bowl["runs_conceded"],
        )

    for player_id, stats in scored[:3]:
        if stats["balls"] > 0 or stats["runs"] > 0:
            add(player_id)
    for player_id, stats in taken[:3]:
        if stats["wickets"] > 0 or stats["runs_conceded"] > 0:
            add(player_id)
    for player_id in set(batting) & set(bowling):
        if batting[player_id]["runs"] > 0 and bowling[player_id]["wickets"] > 0:
            add(player_id)
    return list(selected.values())


def _dedupe_facts(facts: list[FactItem]) -> list[FactItem]:
    seen: dict[str, FactItem] = {}
    for item in facts:
        seen.setdefault(item.id, item)
    return list(seen.values())


def _collect_numbers(payload: Any, allowed: set[str]) -> None:
    if isinstance(payload, dict):
        for value in payload.values():
            _collect_numbers(value, allowed)
        return
    if isinstance(payload, list | tuple):
        for value in payload:
            _collect_numbers(value, allowed)
        return
    if isinstance(payload, bool):
        return
    if isinstance(payload, int):
        allowed.add(str(payload))
        return
    if isinstance(payload, float):
        allowed.add(_normalize_number(payload))
        if payload == int(payload):
            allowed.add(str(int(payload)))
        return
    if isinstance(payload, str):
        _collect_numbers_from_text(payload, allowed)


def _collect_numbers_from_text(text: str, allowed: set[str]) -> None:
    current = ""
    for char in text:
        if char.isdigit() or (char == "." and current and "." not in current):
            current += char
        elif current:
            _add_token(current, allowed)
            current = ""
    if current:
        _add_token(current, allowed)


def _add_token(token: str, allowed: set[str]) -> None:
    if token.endswith("."):
        token = token[:-1]
    if not token:
        return
    allowed.add(token)
    if "." in token:
        allowed.add(_normalize_number(float(token)))


def _normalize_number(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"
