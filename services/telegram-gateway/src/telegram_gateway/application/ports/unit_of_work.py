from types import TracebackType
from typing import Protocol

from telegram_gateway.application.ports.telegram_binding_repository import (
    TelegramBindingRepository,
)


class UnitOfWork(Protocol):
    @property
    def telegram_bindings(self) -> TelegramBindingRepository:
        ...

    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...