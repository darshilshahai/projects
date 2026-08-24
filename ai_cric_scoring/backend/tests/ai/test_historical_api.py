from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.ai.fakes import FakeAIProvider
from tests.api_helpers import bearer, register_user
from tests.match_helpers import complete_simple_match, create_draft, create_player

from app.ai.schemas.historical import StructuredHistoricalInsight
from app.core.dependencies import get_ai_provider
from app.db.session import get_db
from app.main import create_app


@pytest.fixture
async def analytics_env(db_session: AsyncSession) -> AsyncIterator[tuple[AsyncClient, FakeAIProvider]]:
    provider = FakeAIProvider()
    app = create_app()

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_ai_provider] = lambda: provider
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, provider
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_overview_and_player_stats_are_owner_scoped(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = analytics_env
    owner = await register_user(client, "hist-owner@example.com")
    other = await register_user(client, "hist-other@example.com")
    completed = await complete_simple_match(client, owner, label="HistA")
    global_player_id = completed["fixture"]["batting"]["players"][0]["player_id"]

    empty = await client.get("/api/v1/analytics/overview", headers=bearer(other))
    assert empty.status_code == 200
    assert empty.json()["completed_matches"] == 0
    assert empty.json()["top_runs"] is None

    overview = await client.get("/api/v1/analytics/overview", headers=completed["headers"])
    assert overview.status_code == 200
    assert overview.json()["completed_matches"] >= 1
    assert overview.json()["top_runs"] is not None

    stats = await client.get(f"/api/v1/analytics/players/{global_player_id}", headers=completed["headers"])
    assert stats.status_code == 200, stats.text
    batting = stats.json()["batting"]
    assert batting["innings"] >= 1
    assert batting["runs"] >= 0
    assert "batting_average" in batting

    forbidden = await client.get(f"/api/v1/analytics/players/{global_player_id}", headers=bearer(other))
    assert forbidden.status_code == 404

    draft = await create_draft(client, owner, name="Live-not-stats")
    assert draft["status"] != "COMPLETED"
    again = await client.get("/api/v1/analytics/overview", headers=completed["headers"])
    assert again.json()["completed_matches"] == overview.json()["completed_matches"]
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_last_n_and_format_filters(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, _provider = analytics_env
    owner = await register_user(client, "hist-filter@example.com")
    first = await complete_simple_match(client, owner, label="FilterA")
    await complete_simple_match(client, owner, label="FilterB")
    headers = first["headers"]

    all_time = await client.get("/api/v1/analytics/overview", headers=headers)
    assert all_time.json()["completed_matches"] == 2

    last_one = await client.get("/api/v1/analytics/overview", params={"last_n": 1}, headers=headers)
    assert last_one.json()["completed_matches"] == 1

    t20 = await client.get("/api/v1/analytics/overview", params={"format": "T20"}, headers=headers)
    assert t20.json()["completed_matches"] == 0

    custom = await client.get("/api/v1/analytics/overview", params={"format": "CUSTOM"}, headers=headers)
    assert custom.json()["completed_matches"] == 2


@pytest.mark.asyncio
async def test_leaderboard_qualification_and_ties(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, _provider = analytics_env
    owner = await register_user(client, "hist-rank@example.com")
    first = await complete_simple_match(client, owner, label="RankA", first_runs=4)
    await complete_simple_match(client, owner, label="RankB", first_runs=4)
    headers = first["headers"]

    economy = await client.get("/api/v1/analytics/leaderboards", params={"metric": "economy"}, headers=headers)
    assert economy.status_code == 200
    assert economy.json()["items"] == []

    runs = await client.get("/api/v1/analytics/leaderboards", params={"metric": "runs"}, headers=headers)
    assert runs.status_code == 200
    values = [item["value"] for item in runs.json()["items"] if item["value"] == 4]
    assert len(values) >= 2


@pytest.mark.asyncio
async def test_team_id_filter_rejects_foreign_team(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, _provider = analytics_env
    owner = await register_user(client, "hist-team-a@example.com")
    other = await register_user(client, "hist-team-b@example.com")
    owned = await complete_simple_match(client, owner, label="OwnSide")
    foreign = await complete_simple_match(client, other, label="OtherSide")
    foreign_team_id = foreign["detail"]["teams"][0]["team_id"]
    response = await client.get(
        "/api/v1/analytics/overview",
        params={"team_id": foreign_team_id},
        headers=owned["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_direct_query_does_not_call_provider(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = analytics_env
    owner = await register_user(client, "hist-q@example.com")
    completed = await complete_simple_match(client, owner, label="QueryA")
    name = completed["scorecard"]["innings"][0]["batting"][0]["name"]
    response = await client.post(
        "/api/v1/analytics/query",
        json={"question": f"What is {name}'s average?"},
        headers=completed["headers"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["used_ai"] is False
    assert response.json()["answer_type"] == "DIRECT_STAT"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_season_and_out_of_scope_skip_provider(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = analytics_env
    owner = await register_user(client, "hist-scope@example.com")
    await complete_simple_match(client, owner, label="ScopeA")
    season = await client.post(
        "/api/v1/analytics/query",
        json={"question": "How many wickets has Dev taken this season?"},
        headers=bearer(owner),
    )
    assert season.json()["answer_type"] == "CLARIFICATION"
    world = await client.post(
        "/api/v1/analytics/query",
        json={"question": "Who is the best player in the world?"},
        headers=bearer(owner),
    )
    assert world.json()["answer_type"] == "OUT_OF_SCOPE"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_two_rahuls_clarify(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = analytics_env
    owner = await register_user(client, "hist-rahul@example.com")
    await complete_simple_match(client, owner, label="RahulA")
    await create_player(client, owner, "Rahul Shah")
    await create_player(client, owner, "Rahul Patel")
    response = await client.post(
        "/api/v1/analytics/query",
        json={"question": "How has Rahul performed?"},
        headers=bearer(owner),
    )
    assert response.status_code == 200
    assert response.json()["answer_type"] == "CLARIFICATION"
    labels = {item["label"] for item in response.json()["clarification_options"]}
    assert "Rahul Shah" in labels
    assert "Rahul Patel" in labels
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_compare_rejects_foreign_player(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, _provider = analytics_env
    owner = await register_user(client, "hist-cmp-a@example.com")
    other = await register_user(client, "hist-cmp-b@example.com")
    a_match = await complete_simple_match(client, owner, label="CmpA")
    b_match = await complete_simple_match(client, other, label="CmpB")
    player_a = a_match["fixture"]["batting"]["players"][0]["player_id"]
    player_b = b_match["fixture"]["batting"]["players"][0]["player_id"]
    response = await client.post(
        "/api/v1/analytics/compare/players",
        json={"player_a_id": player_a, "player_b_id": player_b, "scope": {}},
        headers=a_match["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analytical_query_computes_facts_before_provider(
    analytics_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = analytics_env
    owner = await register_user(client, "hist-ai@example.com")
    completed = await complete_simple_match(client, owner, label="Warriors")
    team_name = completed["detail"]["teams"][0]["name"]
    provider.response = StructuredHistoricalInsight(
        summary="Recent results are mixed in a small sample.",
        insights=["Win rate in the latest window is still a small sample."],
        fact_ids=["empty"],
        caveats=["Sample is small."],
    )
    response = await client.post(
        "/api/v1/analytics/query",
        json={"question": f"Why have {team_name} been losing recently?"},
        headers=completed["headers"],
    )
    assert response.status_code == 200, response.text
    assert provider.calls >= 1
    assert "BEGIN HISTORICAL DATA" in provider.user_prompts[0]
    assert response.json()["used_ai"] is True
    assert response.json()["answer_type"] == "ANALYTICAL"
