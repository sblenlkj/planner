from __future__ import annotations

import asyncio

import pytest

from agent.llm import (
    LlmExecutionScope,
    LlmMessage,
    LlmOrchestrator,
    LlmProviderPool,
    LlmRequest,
    LlmSlot,
    LlmWorkload,
)
from agent.llm.testing import FakeLlmProvider


@pytest.mark.asyncio
async def test_complete_uses_slot_and_returns_response() -> None:
    provider = FakeLlmProvider(prefix="ok")
    pool = LlmProviderPool(
        [LlmSlot(slot_id="slot-1", provider=provider, workloads={LlmWorkload.INTERACTIVE})]
    )
    orchestrator = LlmOrchestrator(pool)

    response = await orchestrator.complete(
        LlmRequest(messages=[LlmMessage(role="user", content="hello")]),
        workload=LlmWorkload.INTERACTIVE,
    )

    assert response.content == "ok: hello"


@pytest.mark.asyncio
async def test_session_holds_slot_until_context_exit() -> None:
    provider = FakeLlmProvider(delay_seconds=0.05)
    pool = LlmProviderPool(
        [LlmSlot(slot_id="slot-1", provider=provider, workloads={LlmWorkload.INTERACTIVE})],
        acquire_timeout_seconds=0.1,
    )
    orchestrator = LlmOrchestrator(pool)

    async with orchestrator.session(
        workload=LlmWorkload.INTERACTIVE,
        scope=LlmExecutionScope.AGENT_RUN,
        purpose="test",
    ) as session:
        assert session.slot_id == "slot-1"
        result = await session.complete(
            LlmRequest(messages=[LlmMessage(role="user", content="inside")])
        )
        assert result.content == "fake: inside"

    response = await orchestrator.complete(
        LlmRequest(messages=[LlmMessage(role="user", content="after")]),
        workload=LlmWorkload.INTERACTIVE,
    )
    assert response.content == "fake: after"


@pytest.mark.asyncio
async def test_two_sessions_do_not_use_one_slot_concurrently() -> None:
    provider = FakeLlmProvider(delay_seconds=0.1)
    pool = LlmProviderPool(
        [LlmSlot(slot_id="slot-1", provider=provider, workloads={LlmWorkload.INTERACTIVE})],
        acquire_timeout_seconds=1.0,
    )
    orchestrator = LlmOrchestrator(pool)
    order: list[str] = []

    async def run(name: str) -> None:
        async with orchestrator.session(
            workload=LlmWorkload.INTERACTIVE,
            scope=LlmExecutionScope.AGENT_RUN,
            purpose=name,
        ) as session:
            order.append(f"start:{name}:{session.slot_id}")
            await asyncio.sleep(0.05)
            order.append(f"end:{name}:{session.slot_id}")

    await asyncio.gather(run("a"), run("b"))

    assert order in (
        ["start:a:slot-1", "end:a:slot-1", "start:b:slot-1", "end:b:slot-1"],
        ["start:b:slot-1", "end:b:slot-1", "start:a:slot-1", "end:a:slot-1"],
    )
