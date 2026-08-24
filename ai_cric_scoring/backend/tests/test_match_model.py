import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MatchFormat, MatchSide, MatchStatus
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.services.match import MatchService
from app.services.team import TeamService


@pytest.mark.asyncio
async def test_match_custom_overs_and_enums_persist(
    db_session: AsyncSession,
    user: User,
    team: Team,
) -> None:
    opponent = await TeamService(db_session).create(owner_user_id=user.id, name="Red XI")
    created = await MatchService(db_session).create_skeleton(
        created_by_user_id=user.id,
        team_a=team,
        team_b=opponent,
        match_format=MatchFormat.CUSTOM,
        overs_per_innings=12,
        balls_per_over=6,
        venue_name="Local Ground",
    )
    loaded = await MatchService(db_session).get_with_participants(created.id)
    assert loaded.format is MatchFormat.CUSTOM
    assert loaded.status is MatchStatus.DRAFT
    assert loaded.overs_per_innings == 12
    assert loaded.balls_per_over == 6
    assert loaded.created_by_user_id == user.id
    assert loaded.venue_name == "Local Ground"
    assert {side.side for side in loaded.match_teams} == {MatchSide.TEAM_A, MatchSide.TEAM_B}


@pytest.mark.asyncio
async def test_match_team_snapshots_and_sides(
    db_session: AsyncSession,
    user: User,
    team: Team,
) -> None:
    opponent = await TeamService(db_session).create(owner_user_id=user.id, name="Red XI")
    created = await MatchService(db_session).create_skeleton(
        created_by_user_id=user.id,
        team_a=team,
        team_b=opponent,
        match_format=MatchFormat.T20,
        overs_per_innings=20,
    )
    loaded = await MatchService(db_session).get_with_participants(created.id)
    snapshots = {item.side: item.team_name_snapshot for item in loaded.match_teams}
    assert snapshots[MatchSide.TEAM_A] == "Blue XI"
    assert snapshots[MatchSide.TEAM_B] == "Red XI"
    assert all(item.team_id in {team.id, opponent.id} for item in loaded.match_teams)


@pytest.mark.asyncio
async def test_match_player_snapshot_and_participation(
    db_session: AsyncSession,
    user: User,
    team: Team,
    player: Player,
) -> None:
    opponent = await TeamService(db_session).create(owner_user_id=user.id, name="Red XI")
    service = MatchService(db_session)
    created = await service.create_skeleton(
        created_by_user_id=user.id,
        team_a=team,
        team_b=opponent,
        match_format=MatchFormat.T20,
        overs_per_innings=20,
    )
    loaded = await service.get_with_participants(created.id)
    home = next(item for item in loaded.match_teams if item.side is MatchSide.TEAM_A)
    participant = await service.add_player(
        match=loaded,
        match_team=home,
        player=player,
        is_captain=True,
        batting_position=1,
    )
    assert participant.display_name_snapshot == "Rohit Sharma"
    assert participant.is_playing is True
    assert participant.is_captain is True
    assert participant.batting_position == 1
    assert participant.match_id == loaded.id
    assert participant.match_team_id == home.id
    assert participant.player_id == player.id

    refreshed = await service.get_with_participants(loaded.id)
    assert len(refreshed.match_players) == 1
    assert refreshed.match_players[0].display_name_snapshot == player.name
