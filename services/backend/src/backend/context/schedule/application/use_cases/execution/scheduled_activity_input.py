from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.context.schedule.domain.shared.local_time import LocalTime


@dataclass(frozen=True, kw_only=True)
class ScheduledActivityInput:
    start_time: LocalTime
    end_time: LocalTime
    title: str
    description: str | None = None
    course_task_id: UUID | None = None