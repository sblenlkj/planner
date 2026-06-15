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
)
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    SendAgentMessage,
    SendTelegramNotification,
    GetAgentSession
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
        uow=uow,
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