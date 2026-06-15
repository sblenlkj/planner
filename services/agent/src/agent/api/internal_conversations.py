from __future__ import annotations

from fastapi import APIRouter, Depends

from agent.api.dependencies import InternalRequestContext, get_internal_context
from agent.api.schemas import ConversationRequest, ConversationRespondResponse

router = APIRouter(prefix="/internal/conversations", tags=["internal-conversations"])


@router.post("/respond", response_model=ConversationRespondResponse)
async def respond_to_conversation(
    request: ConversationRequest,
    context: InternalRequestContext = Depends(get_internal_context),
) -> ConversationRespondResponse:
    last_user_message = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        None,
    )

    if last_user_message is None:
        return ConversationRespondResponse(
            assistant_text="Я получил историю сессии, но не нашел последнего сообщения пользователя."
        )

    return ConversationRespondResponse(
        assistant_text=(
            f"Получил сообщение для пользователя {context.business_user_id}. "
            f"Скоро здесь будет PlannerConversationAgent. "
            f"Последнее сообщение: {last_user_message}"
        )
    )