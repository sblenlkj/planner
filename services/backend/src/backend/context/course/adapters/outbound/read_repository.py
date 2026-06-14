from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.course.adapters.outbound.models import (
    CourseObservationRow,
    CourseRow,
    CourseTaskObservationRow,
    CourseTaskRow,
)
from backend.context.course.application.dto.course_read_models import (
    CourseDetails,
    CourseListItem,
    CourseObservationReadItem,
    CourseTaskDetails,
    CourseTaskObservationReadItem,
    CourseTaskReadItem,
)
from backend.context.course.application.ports.course_read_repository import (
    CourseReadRepository,
)
from backend.context.course.domain.value_objects import (
    CourseStatus,
    CourseTaskStatus,
)


class SqlAlchemyCourseReadRepository(CourseReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_courses(
        self,
        *,
        user_id: UUID,
        status: CourseStatus | None = None,
    ) -> list[CourseListItem]:
        statement = select(CourseRow).where(CourseRow.user_id == user_id)

        if status is not None:
            statement = statement.where(CourseRow.status == status.value)

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        return [self._to_course_list_item(row) for row in rows]

    async def get_course(
        self,
        *,
        course_id: UUID,
        with_observations: bool = False,
        with_tasks: bool = True,
        task_status: CourseTaskStatus | None = None,
    ) -> CourseDetails | None:
        result = await self._session.execute(
            select(CourseRow).where(CourseRow.id == course_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        observations: list[CourseObservationReadItem] | None = None
        tasks: list[CourseTaskReadItem] | None = None

        if with_observations:
            observations = await self._list_course_observations(
                course_id=course_id,
            )

        if with_tasks:
            tasks = await self._list_course_tasks(
                course_id=course_id,
                status=task_status,
            )

        return CourseDetails(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            description=row.description,
            status=CourseStatus(row.status),
            observations=observations,
            tasks=tasks,
        )

    async def get_course_task(
        self,
        *,
        task_id: UUID,
        with_observations: bool = False,
    ) -> CourseTaskDetails | None:
        result = await self._session.execute(
            select(CourseTaskRow).where(CourseTaskRow.id == task_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        observations: list[CourseTaskObservationReadItem] | None = None

        if with_observations:
            observations = await self._list_course_task_observations(
                task_id=task_id,
            )

        return CourseTaskDetails(
            id=row.id,
            course_id=row.course_id,
            title=row.title,
            description=row.description,
            priority=row.priority,
            status=CourseTaskStatus(row.status),
            observations=observations,
        )

    async def _list_course_observations(
        self,
        *,
        course_id: UUID,
    ) -> list[CourseObservationReadItem]:
        result = await self._session.execute(
            select(CourseObservationRow).where(
                CourseObservationRow.course_id == course_id,
            )
        )
        rows = result.scalars().all()

        return [
            CourseObservationReadItem(
                id=row.id,
                title=row.title,
                description=row.description,
            )
            for row in rows
        ]

    async def _list_course_tasks(
        self,
        *,
        course_id: UUID,
        status: CourseTaskStatus | None = None,
    ) -> list[CourseTaskReadItem]:
        statement = select(CourseTaskRow).where(
            CourseTaskRow.course_id == course_id,
        )

        if status is not None:
            statement = statement.where(CourseTaskRow.status == status.value)

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        return [
            CourseTaskReadItem(
                id=row.id,
                course_id=row.course_id,
                title=row.title,
                description=row.description,
                priority=row.priority,
                status=CourseTaskStatus(row.status),
            )
            for row in rows
        ]

    async def _list_course_task_observations(
        self,
        *,
        task_id: UUID,
    ) -> list[CourseTaskObservationReadItem]:
        result = await self._session.execute(
            select(CourseTaskObservationRow).where(
                CourseTaskObservationRow.task_id == task_id,
            )
        )
        rows = result.scalars().all()

        return [
            CourseTaskObservationReadItem(
                id=row.id,
                title=row.title,
                description=row.description,
            )
            for row in rows
        ]

    @staticmethod
    def _to_course_list_item(row: CourseRow) -> CourseListItem:
        return CourseListItem(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            description=row.description,
            status=CourseStatus(row.status),
        )