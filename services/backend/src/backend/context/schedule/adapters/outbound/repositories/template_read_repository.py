from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.schedule.adapters.outbound.models import (
    ScheduleDayTemplateRow,
    TemplateTimeBlockRow,
    WeeklyScheduleObservationRow,
    WeeklyScheduleTemplateRow,
)
from backend.context.schedule.application.ports.repositories.template_read_repository import (
    TemplateReadRepository,
)
from backend.context.schedule.domain.shared.local_time import LocalTime
from backend.context.schedule.domain.shared.time_block_kind import TimeBlockKind
from backend.context.schedule.domain.template.entities.schedule_day_template import (
    ScheduleDayTemplate,
)
from backend.context.schedule.domain.template.entities.time_block import TimeBlock
from backend.context.schedule.domain.template.entities.weekly_schedule_observation import (
    WeeklyScheduleObservation,
)
from backend.context.schedule.domain.template.entities.weekly_schedule_template import (
    WeeklyScheduleTemplate,
)
from backend.context.schedule.domain.template.value_objects.weekday import Weekday


class SqlAlchemyTemplateReadRepository(TemplateReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_weekly_schedule_template_by_user_id(
        self,
        user_id: UUID,
    ) -> WeeklyScheduleTemplate | None:
        result = await self._session.execute(
            select(WeeklyScheduleTemplateRow).where(
                WeeklyScheduleTemplateRow.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return WeeklyScheduleTemplate(
            id=row.id,
            user_id=row.user_id,
            days=await self._list_days(template_id=row.id),
            observations=await self._list_observations(template_id=row.id),
        )

    async def _list_days(self, *, template_id: UUID) -> list[ScheduleDayTemplate]:
        result = await self._session.execute(
            select(ScheduleDayTemplateRow)
            .where(ScheduleDayTemplateRow.weekly_schedule_template_id == template_id)
            .order_by(ScheduleDayTemplateRow.weekday)
        )
        rows = result.scalars().all()

        days: list[ScheduleDayTemplate] = []
        for row in rows:
            weekday = Weekday(row.weekday)
            days.append(
                ScheduleDayTemplate(
                    weekly_schedule_template_id=row.weekly_schedule_template_id,
                    weekday=weekday,
                    time_blocks=await self._list_time_blocks(
                        template_id=template_id,
                        weekday=weekday,
                    ),
                )
            )

        return days

    async def _list_time_blocks(
        self,
        *,
        template_id: UUID,
        weekday: Weekday,
    ) -> list[TimeBlock]:
        result = await self._session.execute(
            select(TemplateTimeBlockRow)
            .where(
                TemplateTimeBlockRow.weekly_schedule_template_id == template_id,
                TemplateTimeBlockRow.weekday == weekday.value,
            )
            .order_by(TemplateTimeBlockRow.start_time)
        )
        rows = result.scalars().all()

        return [
            TimeBlock(
                id=row.id,
                start_time=LocalTime.parse(row.start_time),
                end_time=LocalTime.parse(row.end_time),
                kind=TimeBlockKind(row.kind),
                title=row.title,
                description=row.description,
            )
            for row in rows
        ]

    async def _list_observations(
        self,
        *,
        template_id: UUID,
    ) -> list[WeeklyScheduleObservation]:
        result = await self._session.execute(
            select(WeeklyScheduleObservationRow).where(
                WeeklyScheduleObservationRow.weekly_schedule_template_id == template_id,
            )
        )
        rows = result.scalars().all()

        return [
            WeeklyScheduleObservation(
                id=row.id,
                weekly_schedule_template_id=row.weekly_schedule_template_id,
                description=row.description,
            )
            for row in rows
        ]
