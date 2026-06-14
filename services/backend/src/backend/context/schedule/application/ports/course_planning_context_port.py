from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class PlannedCourseTaskReadModel:
    id: UUID
    course_id: UUID
    title: str
    status: str


@dataclass(frozen=True, kw_only=True)
class RecentPlannedActivityReadModel:
    title: str
    course_task_id: UUID | None
    course_task_status: str | None


@dataclass(frozen=True, kw_only=True)
class CoursePlanningContextReadModel:
    recent_activities: list[RecentPlannedActivityReadModel]


class CoursePlanningContextPort(Protocol):
    async def get_recent_planned_course_activity_context(
        self,
        user_id: UUID,
        course_task_ids: list[UUID],
    ) -> CoursePlanningContextReadModel:
        raise NotImplementedError