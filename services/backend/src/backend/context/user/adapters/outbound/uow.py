from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore import AbstractCommandUnitOfWork

from backend.context.user.adapters.outbound.repository import (
    SqlAlchemyUserRepository,
)
from backend.context.user.application.ports import UserUnitOfWork, UserRepository


class SqlAlchemyUserCommandUnitOfWork(
    AbstractCommandUnitOfWork,
    UserUnitOfWork,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users: UserRepository = SqlAlchemyUserRepository(session)

    async def enter_session(self) -> None:
        return None

    async def exit_session(self) -> None:
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _iter_repositories(self):
        return ()