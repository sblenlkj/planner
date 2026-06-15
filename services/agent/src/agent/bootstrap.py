from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.core.settings import get_settings
from agent.infrastructure.llm import LlmSlotPool
from agent.infrastructure.observability import build_langfuse_callback, configure_langfuse_env


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    configure_langfuse_env(settings)

    app.state.settings = settings
    app.state.llm_slot_pool = LlmSlotPool.from_settings(settings)
    app.state.langfuse_callback = build_langfuse_callback()

    yield