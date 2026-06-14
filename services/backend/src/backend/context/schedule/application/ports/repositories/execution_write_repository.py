from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.schedule.domain.execution.entities.schedule_date_observation import (
    ScheduleDateObservation,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


class ExecutionWriteRepository(Protocol):
    async def add_schedule_day(self, schedule_day: ScheduleDay) -> None:
        raise NotImplementedError

    async def get_schedule_day_by_user_id_and_date(
        self,
        user_id: UUID,
        date: ScheduleDate,
    ) -> ScheduleDay | None:
        raise NotImplementedError

    async def update_schedule_day(self, schedule_day: ScheduleDay) -> None:
        raise NotImplementedError

    async def add_schedule_date_observation(
        self,
        observation: ScheduleDateObservation,
    ) -> None:
        raise NotImplementedError