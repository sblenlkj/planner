from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.dto.course_read_models import (
    CourseDetails,
)
from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.value_objects.course_task_status import (
    CourseTaskStatus,
)


@dataclass(frozen=True, kw_only=True)
class ReadCourseCommand(Command):
    course_id: UUID
    with_observations: bool = False
    with_tasks: bool = True
    task_status: CourseTaskStatus | None = None


@dataclass(frozen=True, kw_only=True)
class ReadCourseCommandResult:
    course: CourseDetails | None


@command_handler_registry.handler(ReadCourseCommand)
class ReadCourseCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ReadCourseCommand,
        context: CourseCommandHandlerContext,
    ) -> ReadCourseCommandResult:
        course = await context.uow.course_reader.get_course(
            course_id=command.course_id,
            with_observations=command.with_observations,
            with_tasks=command.with_tasks,
            task_status=command.task_status,
        )

        return ReadCourseCommandResult(course=course)