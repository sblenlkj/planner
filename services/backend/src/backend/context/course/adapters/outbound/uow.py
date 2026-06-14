from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from direttore import AbstractCommandUnitOfWork

from backend.context.course.adapters.outbound.read_repository import (
    SqlAlchemyCourseReadRepository,
)
from backend.context.course.adapters.outbound.write_repository import (
    SqlAlchemyCourseWriteRepository,
)
from backend.context.course.application.ports.course_unit_of_work import (
    CourseUnitOfWork,
)


class SqlAlchemyCourseCommandUnitOfWork(
    AbstractCommandUnitOfWork,
    CourseUnitOfWork,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.course_reader = SqlAlchemyCourseReadRepository(session)
        self.course_writer = SqlAlchemyCourseWriteRepository(session)

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