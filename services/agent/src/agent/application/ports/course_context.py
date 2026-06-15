from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agent.application.dto import (
    CourseDto,
    CourseObservationDto,
    CourseTaskDto,
    CourseTaskObservationDto,
)


class CourseContextPort(Protocol):
    # Read side
    async def list_courses(self, user_id: UUID) -> list[CourseDto]: ...

    async def get_course(
        self,
        course_id: UUID,
        *,
        with_observations: bool = False,
        with_tasks: bool = True,
        task_status: str | None = None,
    ) -> CourseDto: ...

    async def list_course_tasks(self, course_id: UUID) -> list[CourseTaskDto]: ...

    async def get_course_task(self, task_id: UUID) -> CourseTaskDto: ...

    async def list_course_observations(self, course_id: UUID) -> list[CourseObservationDto]: ...

    async def list_course_task_observations(self, task_id: UUID) -> list[CourseTaskObservationDto]: ...

    # Write side
    async def create_course(
        self,
        user_id: UUID,
        *,
        title: str,
        description: str | None = None,
    ) -> CourseDto: ...

    async def create_course_task(
        self,
        course_id: UUID,
        *,
        title: str,
        description: str | None = None,
        priority: int = 2,
    ) -> CourseTaskDto: ...

    async def update_course_task_progress(
        self,
        task_id: UUID,
        *,
        progress: int,
    ) -> CourseTaskDto: ...

    async def create_course_observation(
        self,
        course_id: UUID,
        *,
        title: str,
        description: str,
    ) -> CourseObservationDto: ...

    async def create_course_task_observation(
        self,
        task_id: UUID,
        *,
        title: str,
        description: str,
        progress: int | None = None,
    ) -> CourseTaskObservationDto: ...
