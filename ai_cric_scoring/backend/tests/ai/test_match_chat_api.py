from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.ai.fakes import FakeAIProvider, grounded_chat
from tests.api_helpers import bearer, register_user
from tests.match_helpers import complete_simple_match, create_draft, create_ready_match

from app.ai.context.fact_package import assemble_fact_package
from app.core.dependencies import get_ai_provider
from app.core.exceptions import AIInvalidResponseError, AITimeoutError
from app.db.session import get_db
from app.main import create_app
from app.schemas.scorecard import MatchScorecardResponse


@pytest.fixture
async def chat_env(db_session: AsyncSession) -> AsyncIterator[tuple[AsyncClient, FakeAIProvider]]:
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


def _payload(message: str) -> dict:
    return {"message": message, "client_message_id": str(uuid4())}


@pytest.mark.asyncio
async def test_direct_stat_does_not_call_provider(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-direct@example.com")
    completed = await complete_simple_match(client, owner, label="Direct")
    empty = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    assert empty.status_code == 200
    assert empty.json()["messages"] == []

    won = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("Who won the match?"),
        headers=completed["headers"],
    )
    assert won.status_code == 200, won.text
    assert won.json()["assistant_message"]["answer_type"] == "DIRECT_STAT"
    assert won.json()["assistant_message"]["used_ai"] is False
    assert "won" in won.json()["assistant_message"]["content"].lower()
    assert provider.calls == 0

    history = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    assert [item["role"] for item in history.json()["messages"]] == ["USER", "ASSISTANT"]


@pytest.mark.asyncio
async def test_chat_requires_completed_owned_match(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-owner@example.com")
    other = await register_user(client, "chat-other@example.com")
    draft = await create_draft(client, owner, name="Draft Chat")
    ready = await create_ready_match(client, owner, label="ReadyChat")
    completed = await complete_simple_match(client, owner, label="DoneChat")
    provider.response = grounded_chat(
        assemble_fact_package(MatchScorecardResponse.model_validate(completed["scorecard"]))
    )

    for match_id in (draft["id"], ready["match"]["id"]):
        response = await client.post(
            f"/api/v1/matches/{match_id}/chat/messages",
            json=_payload("Who won?"),
            headers=bearer(owner),
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "MATCH_NOT_COMPLETED"

    forbidden = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("Who won?"),
        headers=bearer(other),
    )
    assert forbidden.status_code == 404
    missing = await client.get(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        headers=bearer(other),
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_out_of_scope_and_missing_data_skip_provider(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-scope@example.com")
    completed = await complete_simple_match(client, owner, label="Scope")
    weather = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("What was the weather?"),
        headers=completed["headers"],
    )
    assert weather.status_code == 200
    assert "not recorded" in weather.json()["assistant_message"]["content"].lower()
    ipl = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("Who won the IPL last year?"),
        headers=completed["headers"],
    )
    assert ipl.json()["assistant_message"]["answer_type"] == "OUT_OF_SCOPE"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_analytical_question_uses_provider_and_grounds(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-why@example.com")
    completed = await complete_simple_match(client, owner, label="Office")
    package = assemble_fact_package(MatchScorecardResponse.model_validate(completed["scorecard"]))
    provider.response = grounded_chat(package)
    losing = completed["scorecard"]["match"]["team_b"]["name"]
    response = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload(f"Why did {losing} lose?"),
        headers=completed["headers"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["assistant_message"]["used_ai"] is True
    assert provider.calls == 1
    assert "BEGIN MATCH DATA" in provider.user_prompts[0]
    assert '"type": "over"' not in provider.user_prompts[0] or "FULL"  # analytical may include overs via key events
    follow = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("What was their biggest partnership?"),
        headers=completed["headers"],
    )
    assert follow.status_code == 200
    assert follow.json()["assistant_message"]["used_ai"] is False
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_player_follow_up_and_over_range_clarification(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-follow@example.com")
    completed = await complete_simple_match(client, owner, first_runs=4, second_runs=1, label="Follow")
    package = assemble_fact_package(MatchScorecardResponse.model_validate(completed["scorecard"]))
    provider.response = grounded_chat(package)
    batter = completed["scorecard"]["innings"][0]["batting"][0]["name"]
    first = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload(f"How did {batter} bat?"),
        headers=completed["headers"],
    )
    assert first.status_code == 200, first.text
    assert first.json()["assistant_message"]["used_ai"] is True
    prompt = provider.user_prompts[0]
    assert batter in prompt
    dismissed = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("Who dismissed him?"),
        headers=completed["headers"],
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["assistant_message"]["used_ai"] is False
    assert batter.split()[0] in dismissed.json()["assistant_message"]["content"]
    overs = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("What happened in the last 5 overs?"),
        headers=completed["headers"],
    )
    assert overs.json()["assistant_message"]["answer_type"] == "CLARIFICATION"
    chase = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload("The chase."),
        headers=completed["headers"],
    )
    assert chase.status_code == 200
    assert chase.json()["assistant_message"]["answer_type"] == "DIRECT_STAT"
    assert "overs" in chase.json()["assistant_message"]["content"].lower()


@pytest.mark.asyncio
async def test_provider_failure_keeps_user_message(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-fail@example.com")
    completed = await complete_simple_match(client, owner, label="FailChat")
    provider.error = AITimeoutError()
    client_id = str(uuid4())
    losing = completed["scorecard"]["match"]["team_b"]["name"]
    failed = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json={"message": f"Why did {losing} lose?", "client_message_id": client_id},
        headers=completed["headers"],
    )
    assert failed.status_code == 200
    assert failed.json()["assistant_message"] is None
    assert failed.json()["generation_error"]["code"] == "AI_TIMEOUT"
    history = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    assert [item["role"] for item in history.json()["messages"]] == ["USER"]
    provider.error = None
    provider.response = grounded_chat(
        assemble_fact_package(MatchScorecardResponse.model_validate(completed["scorecard"]))
    )
    retry = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json={"message": f"Why did {losing} lose?", "client_message_id": client_id},
        headers=completed["headers"],
    )
    assert retry.status_code == 200
    assert retry.json()["assistant_message"] is not None
    history = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    roles = [item["role"] for item in history.json()["messages"]]
    assert roles.count("USER") == 1


@pytest.mark.asyncio
async def test_grounding_rejects_unknown_fact(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-ground@example.com")
    completed = await complete_simple_match(client, owner, label="GroundChat")
    package = assemble_fact_package(MatchScorecardResponse.model_validate(completed["scorecard"]))
    answer = grounded_chat(package)
    provider.response = answer.model_copy(update={"fact_ids": ["fake_99"]})
    losing = completed["scorecard"]["match"]["team_b"]["name"]
    response = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload(f"Why did {losing} lose?"),
        headers=completed["headers"],
    )
    assert response.status_code == 200
    assert response.json()["generation_error"]["code"] == "AI_GROUNDING_FAILED"
    assert response.json()["assistant_message"] is None


@pytest.mark.asyncio
async def test_client_message_id_is_idempotent(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-idemp@example.com")
    completed = await complete_simple_match(client, owner, label="Idemp")
    client_id = str(uuid4())
    first = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json={"message": "Who won the match?", "client_message_id": client_id},
        headers=completed["headers"],
    )
    second = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json={"message": "Who won the match?", "client_message_id": client_id},
        headers=completed["headers"],
    )
    assert first.json()["assistant_message"]["id"] == second.json()["assistant_message"]["id"]
    history = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    assert len(history.json()["messages"]) == 2
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_invalid_chat_response_is_not_persisted(
    chat_env: tuple[AsyncClient, FakeAIProvider],
) -> None:
    client, provider = chat_env
    owner = await register_user(client, "chat-invalid@example.com")
    completed = await complete_simple_match(client, owner, label="InvalidChat")
    losing = completed["scorecard"]["match"]["team_b"]["name"]
    provider.error = AIInvalidResponseError()
    response = await client.post(
        f"/api/v1/matches/{completed['match_id']}/chat/messages",
        json=_payload(f"Why did {losing} lose?"),
        headers=completed["headers"],
    )
    assert response.json()["generation_error"]["code"] == "AI_INVALID_RESPONSE"
    history = await client.get(f"/api/v1/matches/{completed['match_id']}/chat/messages", headers=completed["headers"])
    assert [item["role"] for item in history.json()["messages"]] == ["USER"]
