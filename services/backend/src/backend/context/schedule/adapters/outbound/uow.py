from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore.orchestration import AbstractCommandUnitOfWork, AbstractQueryUnitOfWork

from backend.context.schedule.adapters.outbound.repositories.commitment_read_repository import (
    SqlAlchemyCommitmentReadRepository,
)
from backend.context.schedule.adapters.outbound.repositories.commitment_write_repository import (
    SqlAlchemyCommitmentWriteRepository,
)
from backend.context.schedule.adapters.outbound.repositories.execution_read_repository import (
    SqlAlchemyExecutionReadRepository,
)
from backend.context.schedule.adapters.outbound.repositories.execution_write_repository import (
    SqlAlchemyExecutionWriteRepository,
)
from backend.context.schedule.adapters.outbound.repositories.template_read_repository import (
    SqlAlchemyTemplateReadRepository,
)
from backend.context.schedule.adapters.outbound.repositories.template_write_repository import (
    SqlAlchemyTemplateWriteRepository,
)
from backend.context.schedule.application.ports.schedule_read_unit_of_work import (
    ScheduleReadUnitOfWork,
)
from backend.context.schedule.application.ports.schedule_write_unit_of_work import (
    ScheduleWriteUnitOfWork,
)


class SqlAlchemyScheduleCommandUnitOfWork(
    AbstractCommandUnitOfWork,
    ScheduleWriteUnitOfWork,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.commitment_writer = SqlAlchemyCommitmentWriteRepository(session)
        self.template_writer = SqlAlchemyTemplateWriteRepository(session)
        self.execution_writer = SqlAlchemyExecutionWriteRepository(session)

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


class SqlAlchemyScheduleQueryUnitOfWork(
    AbstractQueryUnitOfWork,
    ScheduleReadUnitOfWork,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.commitment_reader = SqlAlchemyCommitmentReadRepository(session)
        self.template_reader = SqlAlchemyTemplateReadRepository(session)
        self.execution_reader = SqlAlchemyExecutionReadRepository(session)

    async def enter_session(self) -> None:
        return None

    async def exit_session(self) -> None:
        await self._session.close()
