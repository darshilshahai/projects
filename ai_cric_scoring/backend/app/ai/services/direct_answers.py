from __future__ import annotations

from uuid import UUID

from app.ai.context.fact_package import FactItem, MatchFactPackage
from app.ai.context.question_context import resolve_over_window
from app.ai.routing.entity_resolver import ResolvedPlayer
from app.ai.schemas.match_chat import QuestionIntent
from app.schemas.chat import ChatClarificationOption, ChatEvidence


def evidence_for(facts: list[FactItem]) -> list[ChatEvidence]:
    return [ChatEvidence(fact_id=item.id, type=item.type, label=item.label, summary=item.summary) for item in facts[:6]]


def result_answer(package: MatchFactPackage) -> tuple[str, list[FactItem]]:
    facts = [item for item in package.facts if item.type in {"result", "innings"}]
    summary = package.result.summary or "No result is recorded for this match."
    innings = [item.summary for item in facts if item.type == "innings"]
    if innings:
        return f"{summary} Scores: {'; '.join(innings)}.", facts
    return summary, facts


def player_batting_answer(package: MatchFactPackage, player: ResolvedPlayer) -> tuple[str, list[FactItem]]:
    rows = [item for item in package.facts if item.type == "batting" and item.match_player_id == player.match_player_id]
    if not rows:
        return f"{player.name} did not bat in this match.", []
    parts: list[str] = []
    for row in rows:
        innings = f" in innings {row.innings_number}" if row.innings_number else ""
        dismissal = row.values.get("dismissal") or "not out"
        parts.append(
            f"{player.name} scored {row.values.get('runs')} runs from {row.values.get('balls')} balls"
            f"{innings} ({row.values.get('fours')} fours, {row.values.get('sixes')} sixes, {dismissal})."
        )
    return " ".join(parts), rows


def player_dismissal_answer(package: MatchFactPackage, player: ResolvedPlayer) -> tuple[str, list[FactItem]]:
    rows = [item for item in package.facts if item.type == "batting" and item.match_player_id == player.match_player_id]
    if not rows:
        return f"{player.name} did not bat in this match.", []
    texts = []
    for row in rows:
        dismissal = row.values.get("dismissal") or "not out"
        if dismissal != "not out":
            texts.append(f"{player.name} was dismissed: {dismissal}.")
        else:
            texts.append(f"{player.name} was not out.")
    return " ".join(texts), rows


def top_scorer_answer(package: MatchFactPackage) -> tuple[str, list[FactItem]]:
    batting = [item for item in package.facts if item.type == "batting"]
    if not batting:
        return "No batting figures are recorded for this match.", []
    best = max(batting, key=lambda item: (int(item.values.get("runs") or 0), -int(item.values.get("balls") or 0)))
    return (
        f"{best.label} was the top scorer with {best.values.get('runs')} runs from {best.values.get('balls')} balls.",
        [best],
    )


def best_strike_rate_answer(package: MatchFactPackage) -> tuple[str, list[FactItem]]:
    batting = [item for item in package.facts if item.type == "batting" and int(item.values.get("balls") or 0) > 0]
    if not batting:
        return "No batter faced a ball in this match.", []
    best = max(batting, key=lambda item: float(item.values.get("strike_rate") or 0))
    return (
        f"{best.label} had the highest strike rate among batters who faced a ball, "
        f"at {best.values.get('strike_rate')} from {best.values.get('balls')} balls.",
        [best],
    )


def most_wickets_answer(package: MatchFactPackage) -> tuple[str, list[FactItem]]:
    bowling = [item for item in package.facts if item.type == "bowling"]
    if not bowling:
        return "No bowling figures are recorded for this match.", []
    best = max(
        bowling,
        key=lambda item: (int(item.values.get("wickets") or 0), -int(item.values.get("runs_conceded") or 0)),
    )
    return (
        f"{best.label} took the most wickets, {best.values.get('wickets')} for "
        f"{best.values.get('runs_conceded')} in {best.values.get('overs')} overs.",
        [best],
    )


def extras_answer(package: MatchFactPackage, team_id: UUID | None = None) -> tuple[str, list[FactItem]]:
    innings = [item for item in package.facts if item.type == "innings"]
    if team_id is not None:
        conceded = [item for item in innings if item.match_team_id != team_id]
        if not conceded:
            conceded = innings
        total = sum(int(item.values.get("extras") or 0) for item in conceded)
        name = package.team_name(team_id) or "That team"
        return f"{name} conceded {total} extras in this match.", conceded or innings
    total = sum(int(item.values.get("extras") or 0) for item in innings)
    parts = [f"{item.label}: {item.values.get('extras')} extras" for item in innings]
    return f"The match had {total} extras in total. " + "; ".join(parts) + ".", innings


def largest_partnership_answer(package: MatchFactPackage, team_id: UUID | None = None) -> tuple[str, list[FactItem]]:
    stands = [item for item in package.facts if item.type == "partnership"]
    if team_id is not None:
        innings_for_team = {
            item.innings_number for item in package.facts if item.type == "innings" and item.match_team_id == team_id
        }
        stands = [item for item in stands if item.innings_number in innings_for_team]
    if not stands:
        return "No partnerships are recorded for this match.", []
    best = max(stands, key=lambda item: int(item.values.get("runs") or 0))
    return best.summary, [best]


def compare_runs_answer(package: MatchFactPackage, players: list[ResolvedPlayer]) -> tuple[str, list[FactItem]]:
    if len(players) < 2:
        return "I need two players from this match to compare.", []
    left, right = players[0], players[1]
    left_rows = [
        item for item in package.facts if item.type == "batting" and item.match_player_id == left.match_player_id
    ]
    right_rows = [
        item for item in package.facts if item.type == "batting" and item.match_player_id == right.match_player_id
    ]
    left_runs = sum(int(item.values.get("runs") or 0) for item in left_rows)
    right_runs = sum(int(item.values.get("runs") or 0) for item in right_rows)
    facts = left_rows + right_rows
    if left_runs == right_runs:
        return f"{left.name} and {right.name} both scored {left_runs} runs in this match.", facts
    leader = left if left_runs > right_runs else right
    trailer = right if leader is left else left
    leader_runs = left_runs if leader is left else right_runs
    trailer_runs = right_runs if leader is left else left_runs
    return f"{leader.name} scored more, {leader_runs} to {trailer.name}'s {trailer_runs}.", facts


def over_range_answer(
    package: MatchFactPackage,
    intent: QuestionIntent,
    innings_number: int | None,
) -> tuple[str, list[FactItem]]:
    overs = [item for item in package.facts if item.type == "over"]
    if innings_number is not None:
        overs = [item for item in overs if item.innings_number == innings_number]
    start, end = resolve_over_window(overs, intent)
    window = [
        item
        for item in overs
        if item.over_number is not None and start is not None and end is not None and start <= item.over_number <= end
    ]
    if not window:
        return "No over summaries are recorded for that range.", []
    runs = sum(int(item.values.get("runs") or 0) for item in window)
    wickets = sum(int(item.values.get("wickets") or 0) for item in window)
    innings_label = f" of innings {innings_number}" if innings_number else ""
    return (
        f"Overs {start}–{end}{innings_label} produced {runs} runs and {wickets} wickets.",
        window,
    )


def fielding_limitation_answer() -> tuple[str, list[FactItem]]:
    return (
        "I only have recorded dismissal contributions (catches, stumpings, and run-outs in the scorecard text), "
        "not dropped catches, misfields, or runs saved. I cannot rank fielding from this match data.",
        [],
    )


def catches_answer(package: MatchFactPackage) -> tuple[str, list[FactItem]]:
    batting = [item for item in package.facts if item.type == "batting"]
    caught = [item for item in batting if str(item.values.get("dismissal") or "").lower().startswith("c ")]
    if not caught:
        return "No catches are recorded in the dismissal text for this match.", batting[:1] if batting else []
    return "Recorded catch dismissals: " + "; ".join(item.summary for item in caught) + ".", caught


def out_of_scope_answer() -> tuple[str, list[str]]:
    return (
        "I can answer questions about this match. Ask me about the score, players, partnerships, bowling, "
        "turning points, or result.",
        [
            "Who won the match?",
            "Who was the top scorer?",
            "Which partnership mattered most?",
            "What happened in the last 5 overs?",
        ],
    )


def unavailable_answer(topic: str) -> str:
    if topic == "conditions":
        return "Pitch and weather were not recorded for this match, so I can't determine that from the match data."
    if topic in {"unrecorded fielding", "fielding detail"}:
        return fielding_limitation_answer()[0]
    return "That detail was not recorded for this match, so I can't determine it from the match data."


def player_clarification(players: list[ResolvedPlayer]) -> tuple[str, list[ChatClarificationOption]]:
    names = " or ".join(player.name for player in players)
    options = [ChatClarificationOption(label=player.name, message=f"I mean {player.name}.") for player in players]
    return f"Which player do you mean — {names}?", options


def team_clarification(package: MatchFactPackage) -> tuple[str, list[ChatClarificationOption]]:
    teams = [
        (package.match.team_a_name, package.match.team_a_id),
        (package.match.team_b_name, package.match.team_b_id),
    ]
    named = [(name, team_id) for name, team_id in teams if name]
    names = " or ".join(name for name, _ in named)
    options = [ChatClarificationOption(label=name, message=f"I mean {name}.") for name, _ in named]
    return f"Which team do you mean — {names}?", options


def innings_clarification() -> tuple[str, list[ChatClarificationOption]]:
    return (
        "Do you mean the first innings or the chase?",
        [
            ChatClarificationOption(label="First innings", message="The first innings."),
            ChatClarificationOption(label="The chase", message="The chase."),
        ],
    )


def suggestions_for(intent: QuestionIntent) -> list[str]:
    mapping = {
        "DIRECT_STAT": ["What was his strike rate?", "Who dismissed him?", "Which partnership was he part of?"],
        "PLAYER_PERFORMANCE": ["Who dismissed him?", "What was his strike rate?", "Did he bowl as well?"],
        "WHY_RESULT": [
            "What was their biggest partnership?",
            "What happened in the last 5 overs?",
            "Did extras matter?",
        ],
        "OVER_RANGE": ["Which wickets fell in that period?", "What was the run rate then?"],
        "PARTNERSHIP": ["Who was the top scorer?", "Where did the chase go wrong?"],
        "BOWLING": ["Who took the most wickets?", "Did extras make a difference?"],
        "BATTING": ["Who was the top scorer?", "Which partnership mattered most?"],
        "MATCH_SUMMARY": ["Who was the top scorer?", "Why did the losing team lose?"],
        "COMPARISON": ["Who took the most wickets?", "Which partnership mattered most?"],
        "EXTRAS": ["Who won the match?", "Why did the losing team lose?"],
        "TURNING_POINT": ["What happened in the last 5 overs?", "Which partnership mattered most?"],
    }
    return mapping.get(intent.type.value, mapping["MATCH_SUMMARY"])
