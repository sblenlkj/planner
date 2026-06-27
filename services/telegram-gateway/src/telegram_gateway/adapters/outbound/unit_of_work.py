from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telegram_gateway.adapters.outbound.repository import (
    PostgresTelegramBindingRepository,
)

from telegram_gateway.application.ports.telegram_binding_repository import TelegramBindingRepository

class SqlAlchemyUnitOfWork:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def telegram_bindings(self) -> TelegramBindingRepository:
        if self._telegram_bindings is None:
            raise RuntimeError("UnitOfWork is not entered.")

        return self._telegram_bindings

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self._telegram_bindings = PostgresTelegramBindingRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        if exc is not None:
            await self.rollback()

        if self._session is not None:
            await self._session.close()

        self._session = None
        self._telegram_bindings = None

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not entered.")

        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not entered.")

        await self._session.rollback()
