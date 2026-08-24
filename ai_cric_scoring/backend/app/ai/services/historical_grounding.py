from __future__ import annotations

from app.ai.schemas.historical import StructuredHistoricalInsight
from app.ai.services.grounding import unallowed_numbers
from app.core.exceptions import AIGroundingFailedError

_SMALL = {str(value) for value in range(0, 21)}


class HistoricalGroundingValidator:
    def validate(self, answer: StructuredHistoricalInsight, package: dict) -> None:
        known = {item["id"] for item in package.get("fact_index", [])}
        player_ids = {item for item in package.get("player_ids", [])}
        team_ids = {item for item in package.get("team_ids", [])}
        allowed = set(package.get("allowed_numbers", [])) | _SMALL
        errors: list[str] = []
        for fact_id in answer.fact_ids:
            if fact_id not in known:
                errors.append(f"Unknown fact_id: {fact_id}")
        for player_id in answer.player_ids:
            if str(player_id) not in player_ids:
                errors.append("Unknown player_id")
        for team_id in answer.team_ids:
            if str(team_id) not in team_ids:
                errors.append("Unknown team_id")
        errors.extend(unallowed_numbers(answer.summary, allowed))
        if errors:
            raise AIGroundingFailedError("The historical answer could not be grounded in calculated facts.")
