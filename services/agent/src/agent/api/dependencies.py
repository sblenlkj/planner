from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from agent.application.services import AgentContextLoader
from agent.core.settings import get_settings

from agent.infrastructure.llm.pool import LlmSlotPool

@dataclass(frozen=True, slots=True)
class InternalRequestContext:
    business_user_id: UUID


async def require_internal_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    settings = get_settings()
    expected = f"Bearer {settings.internal_api_token}"

    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API token",
        )


async def get_internal_context(
    _: None = Depends(require_internal_token),
    x_business_user_id: str | None = Header(default=None, alias="X-Business-User-Id"),
) -> InternalRequestContext:
    if not x_business_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-User-Id header is required",
        )

    try:
        business_user_id = UUID(x_business_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Business-User-Id must be UUID",
        ) from exc

    return InternalRequestContext(business_user_id=business_user_id)


def get_agent_context_loader(request: Request) -> AgentContextLoader:
    loader = getattr(request.app.state, "agent_context_loader", None)

    if loader is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AgentContextLoader is not initialized",
        )

    return loader


def get_backend_contexts(request: Request) -> Any:
    backend_contexts = getattr(request.app.state, "backend_contexts", None)

    if backend_contexts is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend context adapters are not initialized",
        )

    return backend_contexts


def get_llm_slot_pool(request: Request) -> LlmSlotPool:
    llm_slot_pool = getattr(request.app.state, "llm_slot_pool", None)

    if llm_slot_pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM slot pool is not initialized",
        )

    if not isinstance(llm_slot_pool, LlmSlotPool):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid LLM slot pool type",
        )

    return llm_slot_pool


def get_langfuse_callback(request: Request) -> Any | None:
    return getattr(request.app.state, "langfuse_callback", None)