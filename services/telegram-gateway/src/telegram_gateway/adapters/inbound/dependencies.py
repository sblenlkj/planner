from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telegram_gateway.adapters.outbound.persistence.uow import SqlAlchemyUnitOfWork
from telegram_gateway.application.ports.unit_of_work import UnitOfWork
from telegram_gateway.application.use_cases import (
    CloseTelegramSession,
    HandleTelegramMessage,
    SendBusinessMessage,
)
from telegram_gateway.settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_handle_telegram_message_use_case(request: Request) -> HandleTelegramMessage:
    return request.app.state.handle_telegram_message


def get_send_business_message_use_case(request: Request) -> SendBusinessMessage:
    return request.app.state.send_business_message


def get_close_telegram_session_use_case(request: Request) -> CloseTelegramSession:
    return request.app.state.close_telegram_session


async def get_uow(request: Request) -> AsyncIterator[UnitOfWork]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    yield SqlAlchemyUnitOfWork(session_factory=session_factory)


async def verify_telegram_webhook_secret(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> None:
    settings: Settings = request.app.state.settings

    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram webhook secret.",
        )


UowDep = Annotated[UnitOfWork, Depends(get_uow)]
