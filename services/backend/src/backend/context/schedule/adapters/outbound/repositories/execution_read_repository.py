from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.schedule.adapters.outbound.models import (
    ScheduleDateObservationRow,
    ScheduleDayObservationRow,
    ScheduleDayRow,
    ScheduledActivityRow,
    ScheduledBlockRow,
)
from backend.context.schedule.application.ports.repositories.execution_read_repository import (
    ExecutionReadRepository,
)
from backend.context.schedule.domain.execution.entities.schedule_date_observation import (
    ScheduleDateObservation,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.schedule_day_observation import (
    ScheduleDayObservation,
)
from backend.context.schedule.domain.execution.entities.scheduled_activity import (
    ScheduledActivity,
)
from backend.context.schedule.domain.execution.entities.scheduled_block import ScheduledBlock
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind


class SqlAlchemyExecutionReadRepository(ExecutionReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_schedule_day_by_user_id_and_date(
        self,
        *,
        user_id: UUID,
        date: ScheduleDate,
    ) -> ScheduleDay | None:
        result = await self._session.execute(
            select(ScheduleDayRow).where(
                ScheduleDayRow.user_id == user_id,
                ScheduleDayRow.date == date.to_date(),
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return await self._to_schedule_day(row)

    async def list_schedule_date_observations(
        self,
        *,
        user_id: UUID,
        date: ScheduleDate,
    ) -> list[ScheduleDateObservation]:
        row_date = date.to_date()
        result = await self._session.execute(
            select(ScheduleDateObservationRow)
            .where(
                ScheduleDateObservationRow.user_id == user_id,
                ScheduleDateObservationRow.starts_on <= row_date,
                or_(
                    ScheduleDateObservationRow.ends_on.is_(None),
                    ScheduleDateObservationRow.ends_on >= row_date,
                ),
            )
            .order_by(ScheduleDateObservationRow.starts_on)
        )
        rows = result.scalars().all()

        return [self._to_schedule_date_observation(row) for row in rows]

    async def _to_schedule_day(self, row: ScheduleDayRow) -> ScheduleDay:
        schedule_date = ScheduleDate.from_date(row.date)
        return ScheduleDay(
            user_id=row.user_id,
            date=schedule_date,
            title=row.title,
            description=row.description,
            blocks=await self._list_scheduled_blocks(
                user_id=row.user_id,
                date=schedule_date,
            ),
            activities=await self._list_scheduled_activities(
                user_id=row.user_id,
                date=schedule_date,
            ),
            observations=await self._list_schedule_day_observations(
                user_id=row.user_id,
                date=schedule_date,
            ),
        )

    async def _list_scheduled_blocks(
        self,
        *,
        user_id: UUID,
        date: ScheduleDate,
    ) -> list[ScheduledBlock]:
        result = await self._session.execute(
            select(ScheduledBlockRow)
            .where(
                ScheduledBlockRow.user_id == user_id,
                ScheduledBlockRow.date == date.to_date(),
            )
            .order_by(ScheduledBlockRow.start_time)
        )
        rows = result.scalars().all()

        return [
            ScheduledBlock(
                id=row.id,
                start_time=LocalTime.parse(row.start_time),
                end_time=LocalTime.parse(row.end_time),
                kind=TimeBlockKind(row.kind),
                title=row.title,
                description=row.description,
            )
            for row in rows
        ]

    async def _list_scheduled_activities(
        self,
        *,
        user_id: UUID,
        date: ScheduleDate,
    ) -> list[ScheduledActivity]:
        result = await self._session.execute(
            select(ScheduledActivityRow)
            .where(
                ScheduledActivityRow.user_id == user_id,
                ScheduledActivityRow.date == date.to_date(),
            )
            .order_by(ScheduledActivityRow.start_time)
        )
        rows = result.scalars().all()

        return [
            ScheduledActivity(
                id=row.id,
                start_time=LocalTime.parse(row.start_time),
                end_time=LocalTime.parse(row.end_time),
                title=row.title,
                description=row.description,
                course_task_id=row.course_task_id,
            )
            for row in rows
        ]

    async def _list_schedule_day_observations(
        self,
        *,
        user_id: UUID,
        date: ScheduleDate,
    ) -> list[ScheduleDayObservation]:
        result = await self._session.execute(
            select(ScheduleDayObservationRow).where(
                ScheduleDayObservationRow.user_id == user_id,
                ScheduleDayObservationRow.date == date.to_date(),
            )
        )
        rows = result.scalars().all()

        return [
            ScheduleDayObservation(
                id=row.id,
                user_id=row.user_id,
                date=ScheduleDate.from_date(row.date),
                description=row.description,
            )
            for row in rows
        ]

    @staticmethod
    def _to_schedule_date_observation(
        row: ScheduleDateObservationRow,
    ) -> ScheduleDateObservation:
        return ScheduleDateObservation(
            id=row.id,
            user_id=row.user_id,
            starts_on=ScheduleDate.from_date(row.starts_on),
            ends_on=ScheduleDate.from_date(row.ends_on)
            if row.ends_on is not None
            else None,
            description=row.description,
        )
