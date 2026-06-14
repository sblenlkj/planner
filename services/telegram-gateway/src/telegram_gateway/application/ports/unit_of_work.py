from types import TracebackType
from typing import Protocol, Self

from telegram_gateway.application.ports.telegram_binding_repository import (
    TelegramBindingRepository,
)


class UnitOfWork(Protocol):
    telegram_bindings: TelegramBindingRepository

    async def __aenter__(self) -> Self:
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError
