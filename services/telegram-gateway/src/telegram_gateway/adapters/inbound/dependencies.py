from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    SendAgentMessage,
    SendTelegramNotification,
    GetAgentSession
)
from telegram_gateway.bootstrap import AppContainer
from telegram_gateway.application.use_cases.handle_telegram_webhook_message import (
    HandleTelegramWebhookMessage,
)


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def get_uow(
    request: Request,
) -> UnitOfWork:
    return get_container(request).uow_factory()


UowDep = Annotated[
    UnitOfWork,
    Depends(get_uow),
]


async def get_authenticate_business_user_use_case(
    request: Request,
) -> AuthenticateBusinessUser:
    return get_container(request).authenticate_business_user_use_case


async def get_attach_telegram_use_case(
    request: Request,
) -> AttachTelegram:
    return get_container(request).attach_telegram_use_case


async def get_send_agent_message_use_case(
    request: Request,
) -> SendAgentMessage:
    return get_container(request).send_agent_message_use_case


async def get_send_telegram_notification_use_case(
    request: Request,
) -> SendTelegramNotification:
    return get_container(request).send_telegram_notification_use_case


async def get_close_agent_session_use_case(
    request: Request,
) -> CloseAgentSession:
    return get_container(request).close_agent_session_use_case

async def get_agent_session_use_case(
    request: Request,
) -> GetAgentSession:
    return get_container(request).get_agent_session_use_case


async def get_handle_telegram_webhook_message_use_case(
    request: Request,
) -> HandleTelegramWebhookMessage:
    return get_container(request).handle_telegram_webhook_message_use_case


async def verify_telegram_webhook_secret(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> None:
    settings = get_container(request).settings
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret.")
