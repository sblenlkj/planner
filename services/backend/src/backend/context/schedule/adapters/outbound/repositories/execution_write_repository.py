from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select, update as update_sql
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.schedule.adapters.outbound.models import (
    ScheduleDateObservationRow,
    ScheduleDayObservationRow,
    ScheduleDayRow,
    ScheduledActivityRow,
    ScheduledBlockRow,
)
from backend.context.schedule.application.ports.repositories.execution_write_repository import (
    ExecutionWriteRepository,
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


class SqlAlchemyExecutionWriteRepository(ExecutionWriteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_schedule_day(self, *, schedule_day: ScheduleDay) -> None:
        self._session.add(self._to_schedule_day_row(schedule_day))
        self._add_schedule_day_children(schedule_day)

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

    async def update_schedule_day(self, *, schedule_day: ScheduleDay) -> None:
        await self._session.execute(
            update_sql(ScheduleDayRow)
            .where(
                ScheduleDayRow.user_id == schedule_day.user_id,
                ScheduleDayRow.date == schedule_day.date.to_date(),
            )
            .values(
                title=schedule_day.title,
                description=schedule_day.description,
            )
        )
        await self._delete_schedule_day_children(schedule_day)
        self._add_schedule_day_children(schedule_day)

    async def add_schedule_date_observation(
        self,
        *,
        observation: ScheduleDateObservation,
    ) -> None:
        self._session.add(self._to_schedule_date_observation_row(observation))

    def _add_schedule_day_children(self, schedule_day: ScheduleDay) -> None:
        row_date = schedule_day.date.to_date()

        for block in schedule_day.blocks:
            self._session.add(
                ScheduledBlockRow(
                    id=block.id,
                    user_id=schedule_day.user_id,
                    date=row_date,
                    start_time=str(block.start_time),
                    end_time=str(block.end_time),
                    kind=block.kind.value,
                    title=block.title,
                    description=block.description,
                )
            )

        for activity in schedule_day.activities:
            self._session.add(
                ScheduledActivityRow(
                    id=activity.id,
                    user_id=schedule_day.user_id,
                    date=row_date,
                    start_time=str(activity.start_time),
                    end_time=str(activity.end_time),
                    title=activity.title,
                    description=activity.description,
                    course_task_id=activity.course_task_id,
                )
            )

        for observation in schedule_day.observations:
            self._session.add(
                ScheduleDayObservationRow(
                    id=observation.id,
                    user_id=schedule_day.user_id,
                    date=row_date,
                    description=observation.description,
                )
            )

    async def _delete_schedule_day_children(self, schedule_day: ScheduleDay) -> None:
        row_date = schedule_day.date.to_date()
        filters = (
            ScheduledBlockRow.user_id == schedule_day.user_id,
            ScheduledBlockRow.date == row_date,
        )

        await self._session.execute(delete(ScheduledBlockRow).where(*filters))
        await self._session.execute(
            delete(ScheduledActivityRow).where(
                ScheduledActivityRow.user_id == schedule_day.user_id,
                ScheduledActivityRow.date == row_date,
            )
        )
        await self._session.execute(
            delete(ScheduleDayObservationRow).where(
                ScheduleDayObservationRow.user_id == schedule_day.user_id,
                ScheduleDayObservationRow.date == row_date,
            )
        )

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
    def _to_schedule_day_row(schedule_day: ScheduleDay) -> ScheduleDayRow:
        return ScheduleDayRow(
            user_id=schedule_day.user_id,
            date=schedule_day.date.to_date(),
            title=schedule_day.title,
            description=schedule_day.description,
        )

    @staticmethod
    def _to_schedule_date_observation_row(
        observation: ScheduleDateObservation,
    ) -> ScheduleDateObservationRow:
        return ScheduleDateObservationRow(
            id=observation.id,
            user_id=observation.user_id,
            starts_on=observation.starts_on.to_date(),
            ends_on=observation.ends_on.to_date()
            if observation.ends_on is not None
            else None,
            description=observation.description,
        )
