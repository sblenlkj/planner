from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Mapping, Any

from .models import (
    LlmExecutionScope,
    LlmRequest,
    LlmResponse,
    LlmSessionRequest,
    LlmWorkload,
)
from .pool import LlmProviderPool
from .session import LlmSession


class LlmOrchestrator:
    """Single entry point for all LLM access inside the agent service."""

    def __init__(self, pool: LlmProviderPool) -> None:
        self._pool = pool

    async def complete(
        self,
        request: LlmRequest,
        *,
        workload: LlmWorkload = LlmWorkload.INTERACTIVE,
        purpose: str = "one_shot_complete",
        prompt_template: str | None = None,
        max_duration_seconds: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> LlmResponse:
        """One-shot LLM call.

        Implemented as a short reserved session to keep one access path for all
        LLM calls.
        """

        async with self.session(
            workload=workload,
            scope=LlmExecutionScope.ONE_SHOT,
            purpose=purpose,
            prompt_template=prompt_template,
            max_duration_seconds=max_duration_seconds,
            metadata=metadata,
        ) as session:
            return await session.complete(request)

    @asynccontextmanager
    async def session(
        self,
        *,
        workload: LlmWorkload,
        scope: LlmExecutionScope = LlmExecutionScope.AGENT_RUN,
        purpose: str,
        prompt_template: str | None = None,
        max_duration_seconds: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[LlmSession]:
        """Reserve one LLM slot for an execution scope."""

        session_request = LlmSessionRequest(
            workload=workload,
            scope=scope,
            purpose=purpose,
            prompt_template=prompt_template,
            max_duration_seconds=max_duration_seconds,
            metadata=metadata or {},
        )
        async with self._pool.session(session_request) as session:
            yield session
