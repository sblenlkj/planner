from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from agent.api.dependencies import (
    InternalRequestContext,
    get_agent_context_loader,
    get_backend_contexts,
    get_internal_context,
    get_langfuse_callback,
    get_llm_slot_pool,
)
from agent.api.schemas import ConversationRequest, ConversationRespondResponse
from agent.application.services import AgentContextLoader
from agent.conversation_agent.input_guard import UserInputGuard
from agent.conversation_agent.main_assistant import run_main_assistant_agent

from agent.core.settings import LlmModelKind
from agent.infrastructure.llm.pool import LlmSlotPool
router = APIRouter(prefix="/internal/conversations", tags=["internal-conversations"])


@router.post("/respond", response_model=ConversationRespondResponse)
async def respond_to_conversation(
    request: ConversationRequest,
    context: InternalRequestContext = Depends(get_internal_context),
    context_loader: AgentContextLoader = Depends(get_agent_context_loader),
    backend_contexts: Any = Depends(get_backend_contexts),
    llm_slot_pool: LlmSlotPool = Depends(get_llm_slot_pool),
    langfuse_callback: Any | None = Depends(get_langfuse_callback),
) -> ConversationRespondResponse:
    last_user_message = next(
        (
            message.content
            for message in reversed(request.messages)
            if message.role == "user"
        ),
        None,
    )

    if last_user_message is None:
        return ConversationRespondResponse(
            assistant_text=(
                "Я получил историю сессии, но не нашел последнего сообщения пользователя."
            )
        )

    UserInputGuard().ensure_safe_text(last_user_message)

    planner_context = await context_loader.load(context.business_user_id)

    callbacks: list[Any] | None = [langfuse_callback] if langfuse_callback else None

    async with llm_slot_pool.acquire(model_kind=LlmModelKind.STRONG) as llm_slot:
        if llm_slot.llm is None:
            raise ValueError("Failed to acquire LLM slot.")

        result = await run_main_assistant_agent(
            llm=llm_slot.llm,
            business_user_id=context.business_user_id,
            messages=request.messages,
            planner_context=planner_context,
            course_context=backend_contexts.course,
            schedule_context=backend_contexts.schedule,
            analytics_context=backend_contexts.analytics,
            callbacks=callbacks,
        )

    return ConversationRespondResponse(
        assistant_text=result.assistant_text,
    )