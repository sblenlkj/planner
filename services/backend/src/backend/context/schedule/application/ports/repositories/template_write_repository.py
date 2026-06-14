from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.schedule.domain.template.entities.weekly_schedule_template import (
    WeeklyScheduleTemplate,
)


class TemplateWriteRepository(Protocol):
    async def add_weekly_schedule_template(
        self,
        template: WeeklyScheduleTemplate,
    ) -> None:
        raise NotImplementedError

    async def get_weekly_schedule_template_by_user_id(
        self,
        user_id: UUID,
    ) -> WeeklyScheduleTemplate | None:
        raise NotImplementedError

    async def update_weekly_schedule_template(
        self,
        template: WeeklyScheduleTemplate,
    ) -> None:
        raise NotImplementedError