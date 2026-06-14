from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update as update_sql
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.course.adapters.outbound.models import (
    CourseObservationRow,
    CourseRow,
    CourseTaskObservationRow,
    CourseTaskRow,
)
from backend.context.course.application.ports.course_write_repository import (
    CourseWriteRepository,
)
from backend.context.course.domain.entities.course import Course
from backend.context.course.domain.entities.course_observation import (
    CourseObservation,
)
from backend.context.course.domain.entities.course_task import CourseTask
from backend.context.course.domain.entities.course_task_observation import (
    CourseTaskObservation,
)
from backend.context.course.domain.value_objects import (
    CourseStatus,
    CourseTaskPriority,
    CourseTaskStatus,
)


class SqlAlchemyCourseWriteRepository(CourseWriteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_course(
        self,
        *,
        course: Course,
    ) -> None:
        self._session.add(self._to_course_row(course))

    async def get_course_by_id(
        self,
        course_id: UUID,
    ) -> Course | None:
        result = await self._session.execute(
            select(CourseRow).where(CourseRow.id == course_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_course(row)

    async def update_course(
        self,
        *,
        course: Course,
    ) -> None:
        await self._session.execute(
            update_sql(CourseRow)
            .where(CourseRow.id == course.id)
            .values(
                title=course.title,
                description=course.description,
                status=course.status.value,
            )
        )

    async def add_course_task(
        self,
        *,
        task: CourseTask,
    ) -> None:
        self._session.add(self._to_course_task_row(task))

    async def get_course_task_by_id(
        self,
        task_id: UUID,
    ) -> CourseTask | None:
        result = await self._session.execute(
            select(CourseTaskRow).where(CourseTaskRow.id == task_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_course_task(row)

    async def update_course_task(
        self,
        *,
        task: CourseTask,
    ) -> None:
        await self._session.execute(
            update_sql(CourseTaskRow)
            .where(CourseTaskRow.id == task.id)
            .values(
                title=task.title,
                description=task.description,
                priority=task.priority.value,
                status=task.status.value,
            )
        )

    async def add_course_observation(
        self,
        *,
        observation: CourseObservation,
    ) -> None:
        self._session.add(self._to_course_observation_row(observation))

    async def get_course_observation_by_id(
        self,
        observation_id: UUID,
    ) -> CourseObservation | None:
        result = await self._session.execute(
            select(CourseObservationRow).where(
                CourseObservationRow.id == observation_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_course_observation(row)

    async def update_course_observation(
        self,
        *,
        observation: CourseObservation,
    ) -> None:
        await self._session.execute(
            update_sql(CourseObservationRow)
            .where(CourseObservationRow.id == observation.id)
            .values(
                title=observation.title,
                description=observation.description,
            )
        )

    async def add_course_task_observation(
        self,
        *,
        observation: CourseTaskObservation,
    ) -> None:
        self._session.add(self._to_course_task_observation_row(observation))

    async def get_course_task_observation_by_id(
        self,
        observation_id: UUID,
    ) -> CourseTaskObservation | None:
        result = await self._session.execute(
            select(CourseTaskObservationRow).where(
                CourseTaskObservationRow.id == observation_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_course_task_observation(row)

    async def update_course_task_observation(
        self,
        *,
        observation: CourseTaskObservation,
    ) -> None:
        await self._session.execute(
            update_sql(CourseTaskObservationRow)
            .where(CourseTaskObservationRow.id == observation.id)
            .values(
                title=observation.title,
                description=observation.description,
            )
        )

    @staticmethod
    def _to_course(row: CourseRow) -> Course:
        return Course(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            description=row.description,
            status=CourseStatus(row.status),
        )

    @staticmethod
    def _to_course_task(row: CourseTaskRow) -> CourseTask:
        return CourseTask(
            id=row.id,
            course_id=row.course_id,
            title=row.title,
            description=row.description,
            priority=CourseTaskPriority(value=row.priority),
            status=CourseTaskStatus(row.status),
        )

    @staticmethod
    def _to_course_observation(row: CourseObservationRow) -> CourseObservation:
        return CourseObservation(
            id=row.id,
            course_id=row.course_id,
            title=row.title,
            description=row.description,
        )

    @staticmethod
    def _to_course_task_observation(
        row: CourseTaskObservationRow,
    ) -> CourseTaskObservation:
        return CourseTaskObservation(
            id=row.id,
            task_id=row.task_id,
            title=row.title,
            description=row.description,
        )

    @staticmethod
    def _to_course_row(course: Course) -> CourseRow:
        return CourseRow(
            id=course.id,
            user_id=course.user_id,
            title=course.title,
            description=course.description,
            status=course.status.value,
        )

    @staticmethod
    def _to_course_task_row(task: CourseTask) -> CourseTaskRow:
        return CourseTaskRow(
            id=task.id,
            course_id=task.course_id,
            title=task.title,
            description=task.description,
            priority=task.priority.value,
            status=task.status.value,
        )

    @staticmethod
    def _to_course_observation_row(
        observation: CourseObservation,
    ) -> CourseObservationRow:
        return CourseObservationRow(
            id=observation.id,
            course_id=observation.course_id,
            title=observation.title,
            description=observation.description,
        )

    @staticmethod
    def _to_course_task_observation_row(
        observation: CourseTaskObservation,
    ) -> CourseTaskObservationRow:
        return CourseTaskObservationRow(
            id=observation.id,
            task_id=observation.task_id,
            title=observation.title,
            description=observation.description,
        )