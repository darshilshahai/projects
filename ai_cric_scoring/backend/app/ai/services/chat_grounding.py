from __future__ import annotations

from app.ai.context.fact_package import MatchFactPackage
from app.ai.schemas.match_chat import StructuredChatAnswer
from app.ai.services.grounding import unallowed_numbers
from app.core.exceptions import AIGroundingFailedError

_SMALL_ALLOWED = {str(value) for value in range(0, 21)}


class ChatGroundingValidator:
    def validate(self, answer: StructuredChatAnswer, package: MatchFactPackage) -> None:
        errors: list[str] = []
        known_facts = package.fact_ids()
        known_players = package.player_ids()
        known_teams = package.team_ids()
        allowed = package.allowed_numbers() | _SMALL_ALLOWED
        for fact_id in answer.fact_ids:
            if fact_id not in known_facts:
                errors.append(f"Unknown fact_id: {fact_id}")
        for player_id in answer.match_player_ids:
            if player_id not in known_players:
                errors.append(f"Unknown match_player_id: {player_id}")
        for team_id in answer.match_team_ids:
            if team_id not in known_teams:
                errors.append(f"Unknown match_team_id: {team_id}")
        errors.extend(unallowed_numbers(answer.content, allowed))
        if errors:
            raise AIGroundingFailedError("The chat answer could not be grounded in match facts.")
