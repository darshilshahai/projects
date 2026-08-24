from __future__ import annotations

import uuid

from app.ai.context.fact_package import MatchFactPackage, assemble_fact_package
from app.core.exceptions import MatchNotCompletedError
from app.models.enums import MatchStatus
from app.services.match import MatchService
from app.services.scorecard import ScorecardService


class MatchContextBuilder:
    def __init__(self, matches: MatchService, scorecards: ScorecardService) -> None:
        self._matches = matches
        self._scorecards = scorecards

    async def build(self, match_id: uuid.UUID, user_id: uuid.UUID) -> MatchFactPackage:
        match = await self._matches.get_owned_detail(match_id, user_id)
        if match.status is not MatchStatus.COMPLETED:
            raise MatchNotCompletedError()
        scorecard = await self._scorecards.get_match_scorecard(match_id, user_id)
        return assemble_fact_package(
            scorecard,
            toss_winner_match_team_id=match.toss_winner_match_team_id,
            toss_decision=match.toss_decision,
        )
