from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore.orchestration import AbstractCommandUnitOfWork

from backend.context.runtime.adapters.outbound.repository import (
    SqlAlchemyRuntimeRepository,
)
from backend.context.runtime.application.ports.runtime_repository import (
    RuntimeRepository,
)
from backend.context.runtime.application.ports.runtime_unit_of_work import (
    RuntimeUnitOfWork,
)


class SqlAlchemyRuntimeCommandUnitOfWork(
    AbstractCommandUnitOfWork,
    RuntimeUnitOfWork,
):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

        self.runtime_repository: RuntimeRepository = SqlAlchemyRuntimeRepository(
            session,
        )

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