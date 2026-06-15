from typing import Annotated

from fastapi import Depends, Request

from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.use_cases import (
    AttachTelegram,
    AuthenticateBusinessUser,
    CloseAgentSession,
    SendAgentMessage,
    SendTelegramNotification,
    GetAgentSession
)


async def get_uow(
    request: Request,
) -> UnitOfWork:
    uow_factory = request.app.state.uow_factory
    return uow_factory()


UowDep = Annotated[
    UnitOfWork,
    Depends(get_uow),
]


async def get_authenticate_business_user_use_case(
    request: Request,
) -> AuthenticateBusinessUser:
    return request.app.state.authenticate_business_user_use_case


async def get_attach_telegram_use_case(
    request: Request,
) -> AttachTelegram:
    return request.app.state.attach_telegram_use_case


async def get_send_agent_message_use_case(
    request: Request,
) -> SendAgentMessage:
    return request.app.state.send_agent_message_use_case


async def get_send_telegram_notification_use_case(
    request: Request,
) -> SendTelegramNotification:
    return request.app.state.send_telegram_notification_use_case


async def get_close_agent_session_use_case(
    request: Request,
) -> CloseAgentSession:
    return request.app.state.close_agent_session_use_case

async def get_agent_session_use_case(
    request: Request,
) -> GetAgentSession:
    return request.app.state.get_agent_session_use_case