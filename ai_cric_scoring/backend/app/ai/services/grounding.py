from __future__ import annotations

import re

from app.ai.context.fact_package import MatchFactPackage
from app.ai.schemas.match_analysis import AnalysisSection, StructuredMatchAnalysis
from app.core.exceptions import AIGroundingFailedError

_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_SMALL_ALLOWED = {str(value) for value in range(0, 21)}


class GroundingValidator:
    def validate(self, analysis: StructuredMatchAnalysis, package: MatchFactPackage) -> None:
        errors: list[str] = []
        known_facts = package.fact_ids()
        known_players = package.player_ids()
        known_teams = package.team_ids()
        allowed_numbers = package.allowed_numbers() | _SMALL_ALLOWED

        for section in _all_sections(analysis):
            for fact_id in section.fact_ids:
                if fact_id not in known_facts:
                    errors.append(f"Unknown fact_id: {fact_id}")
            if section.match_player_id is not None and section.match_player_id not in known_players:
                errors.append(f"Unknown match_player_id: {section.match_player_id}")
            if section.match_team_id is not None and section.match_team_id not in known_teams:
                errors.append(f"Unknown match_team_id: {section.match_team_id}")
            errors.extend(_unallowed_numbers(section.insight, allowed_numbers))

        potm_id = analysis.player_of_match.match_player_id
        if potm_id not in known_players:
            errors.append(f"Unknown player_of_match match_player_id: {potm_id}")
        candidate_ids = {item.match_player_id for item in package.potm_candidates}
        if candidate_ids and potm_id not in candidate_ids:
            errors.append("player_of_match is not a supplied POTM candidate.")
        for fact_id in analysis.player_of_match.fact_ids:
            if fact_id not in known_facts:
                errors.append(f"Unknown fact_id: {fact_id}")
        errors.extend(_unallowed_numbers(analysis.player_of_match.reason, allowed_numbers))
        errors.extend(_unallowed_numbers(analysis.headline, allowed_numbers))
        errors.extend(_unallowed_numbers(analysis.summary, allowed_numbers))

        winner = analysis.winning_match_team_id
        if winner is not None and winner not in known_teams:
            errors.append(f"Unknown winning_match_team_id: {winner}")
        if package.result.result_type == "TIED" and winner is not None:
            errors.append("Tied matches cannot name a winning team.")
        expected = package.result.winner_match_team_id
        if expected is not None and winner is not None and winner != expected:
            errors.append("winning_match_team_id does not match the match result.")

        if errors:
            raise AIGroundingFailedError("The analysis could not be grounded in match facts.")


def _all_sections(analysis: StructuredMatchAnalysis) -> list[AnalysisSection]:
    return [
        *analysis.winning_factors,
        *analysis.losing_factors,
        *analysis.batting_analysis,
        *analysis.bowling_analysis,
        *analysis.partnership_analysis,
        *analysis.phase_analysis,
        *analysis.turning_points,
        *analysis.key_moments,
        *analysis.tactical_observations,
        *analysis.recommendations,
    ]


def unallowed_numbers(text: str, allowed: set[str]) -> list[str]:
    errors: list[str] = []
    for token in _NUMBER.findall(text):
        if token in allowed:
            continue
        if _normalize(token) in allowed:
            continue
        if "." in token and token.rstrip("0").rstrip(".") in allowed:
            continue
        errors.append(f"Ungrounded number: {token}")
    return errors


def _unallowed_numbers(text: str, allowed: set[str]) -> list[str]:
    return unallowed_numbers(text, allowed)


def _normalize(token: str) -> str:
    if "." not in token:
        return token
    return token.rstrip("0").rstrip(".")
