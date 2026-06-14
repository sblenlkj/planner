from typing import Annotated

from fastapi import APIRouter, Depends, Request

from telegram_gateway.adapters.inbound.dependencies import (
    UowDep,
    get_close_telegram_session_use_case,
    get_handle_telegram_message_use_case,
    get_send_business_message_use_case,
    verify_telegram_webhook_secret,
)
from telegram_gateway.adapters.inbound.mappers import (
    UnsupportedTelegramUpdateError,
    map_telegram_update_to_message,
)
from telegram_gateway.adapters.inbound.schemas import (
    CloseTelegramConversationRequest,
    CloseTelegramConversationResponse,
    OkResponse,
    SendTelegramMessageRequest,
    TelegramUpdateSchema,
)
from telegram_gateway.application.use_cases import (
    CloseTelegramSession,
    HandleTelegramMessage,
    SendBusinessMessage,
)


router = APIRouter()


@router.get("/health", response_model=OkResponse)
async def health() -> OkResponse:
    return OkResponse()


@router.post(
    "/telegram/webhook",
    response_model=OkResponse,
    dependencies=[Depends(verify_telegram_webhook_secret)],
)
async def telegram_webhook(
    request: Request,
    update: TelegramUpdateSchema,
    use_case: Annotated[
        HandleTelegramMessage,
        Depends(get_handle_telegram_message_use_case),
    ],
    uow: UowDep,
) -> OkResponse:
    deduplicator = request.app.state.update_deduplicator

    if await deduplicator.is_duplicate(update.update_id):
        return OkResponse()

    try:
        message = map_telegram_update_to_message(update)
    except UnsupportedTelegramUpdateError:
        return OkResponse()

    await use_case.handle(message=message, uow=uow)
    return OkResponse()


@router.post("/internal/messages/send", response_model=OkResponse)
async def send_message(
    request_body: SendTelegramMessageRequest,
    use_case: Annotated[
        SendBusinessMessage,
        Depends(get_send_business_message_use_case),
    ],
    uow: UowDep,
) -> OkResponse:
    await use_case.send_to_business_user(
        business_user_id=request_body.business_user_id,
        text=request_body.text,
        uow=uow,
    )
    return OkResponse()


@router.post(
    "/internal/conversations/close",
    response_model=CloseTelegramConversationResponse,
)
async def close_conversation(
    request_body: CloseTelegramConversationRequest,
    use_case: Annotated[
        CloseTelegramSession,
        Depends(get_close_telegram_session_use_case),
    ],
    uow: UowDep,
) -> CloseTelegramConversationResponse:
    closed = await use_case.close_by_business_user(
        business_user_id=request_body.business_user_id,
        uow=uow,
    )
    return CloseTelegramConversationResponse(
        closed=closed,
        reason=None if closed else "no_active_session",
    )
