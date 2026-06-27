from typing import Annotated

from fastapi import APIRouter, Depends

from telegram_gateway.adapters.inbound.dependencies import (
    UowDep,
    get_attach_telegram_use_case,
    get_authenticate_business_user_use_case,
    get_close_agent_session_use_case,
    get_send_agent_message_use_case,
    get_send_telegram_notification_use_case,
    get_agent_session_use_case,
    get_handle_telegram_webhook_message_use_case,
    verify_telegram_webhook_secret,
)
from telegram_gateway.adapters.inbound.mappers import (
    map_telegram_update_to_incoming_webhook_message,
)
from telegram_gateway.adapters.inbound.schemas import (
    AgentMessageRequest,
    AgentMessageResponse,
    AttachTelegramRequest,
    AuthRequest,
    AuthResponse,
    CloseAgentSessionRequest,
    CloseAgentSessionResponse,
    OkResponse,
    SendTelegramNotificationRequest,
    GetAgentSessionRequest,
    GetAgentSessionResponse,
    ConversationMessageResponse,
    TelegramUpdateSchema,
)
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    SendAgentMessage,
    SendTelegramNotification,
    GetAgentSession
)
from telegram_gateway.application.use_cases.handle_telegram_webhook_message import (
    HandleTelegramWebhookMessage,
)
from telegram_gateway.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


@router.get("/health", response_model=OkResponse)
async def health() -> OkResponse:
    return OkResponse()


@router.post("/auth", response_model=AuthResponse)
async def auth(
    request_body: AuthRequest,
    use_case: Annotated[
        AuthenticateBusinessUser,
        Depends(get_authenticate_business_user_use_case),
    ],
) -> AuthResponse:
    log.info(
        "auth.received",
        business_user_id=str(request_body.business_user_id),
    )

    token = await use_case.authenticate(
        business_user_id=request_body.business_user_id,
    )

    return AuthResponse(
        access_token=token.access_token,
        token_type=token.token_type,
    )


@router.post("/telegram/attach", response_model=OkResponse)
async def attach_telegram(
    request_body: AttachTelegramRequest,
    use_case: Annotated[
        AttachTelegram,
        Depends(get_attach_telegram_use_case),
    ],
    uow: UowDep,
) -> OkResponse:
    log.info(
        "telegram_attach.received",
        business_user_id=str(request_body.business_user_id),
        telegram_user_id=request_body.telegram_user_id,
        telegram_chat_id=request_body.telegram_chat_id,
    )

    await use_case.attach(
        business_user_id=request_body.business_user_id,
        telegram_user_id=request_body.telegram_user_id,
        telegram_chat_id=request_body.telegram_chat_id,
        uow=uow,
    )

    return OkResponse()


@router.post("/agent/message", response_model=AgentMessageResponse)
async def send_agent_message(
    request_body: AgentMessageRequest,
    use_case: Annotated[
        SendAgentMessage,
        Depends(get_send_agent_message_use_case),
    ],
    uow: UowDep,
) -> AgentMessageResponse:
    log.info(
        "agent_message.received",
        business_user_id=str(request_body.business_user_id),
        text_length=len(request_body.text),
    )

    assistant_text = await use_case.send(
        business_user_id=request_body.business_user_id,
        text=request_body.text,
    )

    return AgentMessageResponse(
        assistant_text=assistant_text,
    )


@router.post("/telegram/notifications/send", response_model=OkResponse)
async def send_telegram_notification(
    request_body: SendTelegramNotificationRequest,
    use_case: Annotated[
        SendTelegramNotification,
        Depends(get_send_telegram_notification_use_case),
    ],
    uow: UowDep,
) -> OkResponse:
    log.info(
        "telegram_notification.received",
        business_user_id=str(request_body.business_user_id),
        text_length=len(request_body.text),
    )

    await use_case.send(
        business_user_id=request_body.business_user_id,
        text=request_body.text,
        uow=uow,
    )

    return OkResponse()


@router.post("/agent/session/get", response_model=GetAgentSessionResponse)
async def get_agent_session(
    request_body: GetAgentSessionRequest,
    use_case: Annotated[
        GetAgentSession,
        Depends(get_agent_session_use_case),
    ],
) -> GetAgentSessionResponse:
    log.info(
        "agent_session_get.received",
        business_user_id=str(request_body.business_user_id),
    )

    messages = await use_case.get(
        business_user_id=request_body.business_user_id,
    )

    return GetAgentSessionResponse(
        messages=[
            ConversationMessageResponse(
                role=message.role,
                content=message.content,
            )
            for message in messages
        ],
    )


@router.post("/agent/session/close", response_model=CloseAgentSessionResponse)
async def close_agent_session(
    request_body: CloseAgentSessionRequest,
    use_case: Annotated[
        CloseAgentSession,
        Depends(get_close_agent_session_use_case),
    ],
) -> CloseAgentSessionResponse:
    log.info(
        "agent_session_close.received",
        business_user_id=str(request_body.business_user_id),
    )

    closed = await use_case.close(
        business_user_id=request_body.business_user_id,
    )

    return CloseAgentSessionResponse(
        closed=closed,
        reason=None if closed else "no_active_session",
    )


@router.post("/telegram/webhook", response_model=OkResponse)
async def telegram_webhook(
    update: TelegramUpdateSchema,
    use_case: Annotated[
        HandleTelegramWebhookMessage,
        Depends(get_handle_telegram_webhook_message_use_case),
    ],
    uow: UowDep,
    _: Annotated[None, Depends(verify_telegram_webhook_secret)],
) -> OkResponse:
    log.info(
        "telegram_webhook.received",
        update_id=update.update_id,
        has_message=update.message is not None,
        telegram_user_id=None if update.message is None else update.message.from_user.id,
        telegram_chat_id=None if update.message is None else update.message.chat.id,
        message_date=None if update.message is None else update.message.date,
        text=None if update.message is None else update.message.text,
    )

    incoming = map_telegram_update_to_incoming_webhook_message(update)
    if incoming is None:
        return OkResponse()

    await use_case.handle(incoming, uow=uow)
    return OkResponse()
