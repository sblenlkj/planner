from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore import AbstractCommandUnitOfWork

from backend.context.analytics.adapters.outbound.read_repository import (
    SqlAlchemyAnalyticsReadRepository,
)
from backend.context.analytics.adapters.outbound.write_repository import (
    SqlAlchemyAnalyticsWriteRepository,
)
from backend.context.analytics.application.ports.analytics_unit_of_work import (
    AnalyticsUnitOfWork,
)


class SqlAlchemyAnalyticsCommandUnitOfWork(
    AbstractCommandUnitOfWork,
    AnalyticsUnitOfWork,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.analytics_reader = SqlAlchemyAnalyticsReadRepository(session)
        self.analytics_writer = SqlAlchemyAnalyticsWriteRepository(session)

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
