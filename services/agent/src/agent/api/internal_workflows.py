from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from langchain_core.runnables import RunnableConfig

from agent.api.dependencies import (
    InternalRequestContext,
    get_backend_contexts,
    get_internal_context,
    get_langfuse_callback,
    get_llm_slot_pool,
)
from agent.api.schemas import (
    ConversationRequest,
    MorningBriefingRequest,
    MorningBriefingResponse,
    WorkflowOkResponse,
)
from agent.core.settings import LlmModelKind
from agent.infrastructure.llm.pool import LlmSlotPool
from agent.workflows import run_session_close_workflow

router = APIRouter(prefix="/internal/workflows", tags=["internal-workflows"])


@router.post("/session-close/run", response_model=WorkflowOkResponse)
async def run_session_close(
    request: ConversationRequest,
    context: InternalRequestContext = Depends(get_internal_context),
    backend_contexts: Any = Depends(get_backend_contexts),
    llm_slot_pool: LlmSlotPool = Depends(get_llm_slot_pool),
    langfuse_callback: Any | None = Depends(get_langfuse_callback),
) -> WorkflowOkResponse:
    config: RunnableConfig | None = None
    if langfuse_callback is not None:
        config = RunnableConfig(callbacks=[langfuse_callback])

    async with llm_slot_pool.acquire(model_kind=LlmModelKind.STRONG) as llm_slot:
        if llm_slot.llm is None:
            raise ValueError("Failed to acquire LLM slot.")
    
        await run_session_close_workflow(
            llm=llm_slot.llm,
            business_user_id=context.business_user_id,
            messages=request.messages,
            schedule_context=backend_contexts.schedule,
            config=config,
        )

    return WorkflowOkResponse(ok=True)


@router.post("/morning-briefing/run", response_model=MorningBriefingResponse)
async def run_morning_briefing(
    request: MorningBriefingRequest,
    context: InternalRequestContext = Depends(get_internal_context),
) -> MorningBriefingResponse:
    # TODO:
    # 1. Load user profile.
    # 2. Load courses.
    # 3. Load schedule date/day observations for request.date.
    # 4. Load active commitments.
    # 5. Generate morning briefing text.
    return MorningBriefingResponse(
        ok=True,
        assistant_text=(
            f"Доброе утро. Это тестовый morning briefing на {request.date} "
            f"для пользователя {context.business_user_id}."
        ),
    )