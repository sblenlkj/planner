from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from agent.application.dto.schedule import (
    DeadlineDto,
    ReminderDto,
    ScheduleDateObservationDto,
    ScheduleDayObservationDto,
)


class ScheduleContextPort(Protocol):
    async def list_schedule_date_observations(
        self,
        user_id: UUID,
        *,
        date_: date,
    ) -> list[ScheduleDateObservationDto]: ...

    async def create_schedule_date_observation(
        self,
        user_id: UUID,
        *,
        starts_on: date,
        description: str,
        ends_on: date | None = None,
    ) -> ScheduleDateObservationDto: ...

    async def list_schedule_day_observations(
        self,
        user_id: UUID,
        *,
        date_: date,
    ) -> list[ScheduleDayObservationDto]: ...

    async def create_schedule_day_observation(
        self,
        user_id: UUID,
        *,
        date_: date,
        description: str,
    ) -> ScheduleDayObservationDto: ...

    async def list_commitments(
        self,
        user_id: UUID,
    ) -> list[ReminderDto | DeadlineDto]: ...

    async def create_reminder(
        self,
        user_id: UUID,
        *,
        remind_at: datetime,
        title: str,
        description: str | None = None,
    ) -> ReminderDto: ...

    async def create_deadline(
        self,
        user_id: UUID,
        *,
        due_at: datetime,
        title: str,
        description: str | None = None,
        course_id: UUID | None = None,
        course_task_id: UUID | None = None,
    ) -> DeadlineDto: ...