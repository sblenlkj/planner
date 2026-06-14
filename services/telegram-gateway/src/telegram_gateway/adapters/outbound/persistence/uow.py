from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telegram_gateway.adapters.outbound.persistence.repository import PostgresTelegramBindingRepository
from telegram_gateway.application.ports.telegram_binding_repository import (
    TelegramBindingRepository,
)
from telegram_gateway.application.ports.unit_of_work import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.telegram_bindings: TelegramBindingRepository

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.telegram_bindings = PostgresTelegramBindingRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        await self._require_session().commit()

    async def rollback(self) -> None:
        await self._require_session().rollback()

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active.")
        return self._session
