from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.application.services import AgentContextLoader
from agent.core.backend_settings import BackendApiSettings
from agent.core.settings import get_settings
from agent.infrastructure.backend.factory import build_backend_context_adapters
from agent.infrastructure.llm import LlmSlotPool
from agent.infrastructure.observability import build_langfuse_callback, configure_langfuse_env


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    configure_langfuse_env(settings)

    backend_settings = BackendApiSettings.local()
    backend_contexts = build_backend_context_adapters(backend_settings)

    app.state.settings = settings
    app.state.backend_settings = backend_settings
    app.state.backend_contexts = backend_contexts

    app.state.agent_context_loader = AgentContextLoader(
        user_context=backend_contexts.user,
        course_context=backend_contexts.course,
        schedule_context=backend_contexts.schedule,
        analytics_context=backend_contexts.analytics,
    )

    app.state.llm_slot_pool = LlmSlotPool.from_settings(settings)
    app.state.langfuse_callback = build_langfuse_callback()

    try:
        yield
    finally:
        await backend_contexts.aclose()