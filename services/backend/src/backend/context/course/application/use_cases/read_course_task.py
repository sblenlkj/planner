from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.dto.course_read_models import (
    CourseTaskDetails,
)
from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)


@dataclass(frozen=True, kw_only=True)
class ReadCourseTaskCommand(Command):
    task_id: UUID
    with_observations: bool = False


@dataclass(frozen=True, kw_only=True)
class ReadCourseTaskCommandResult:
    task: CourseTaskDetails | None


@command_handler_registry.handler(ReadCourseTaskCommand)
class ReadCourseTaskCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ReadCourseTaskCommand,
        context: CourseCommandHandlerContext,
    ) -> ReadCourseTaskCommandResult:
        task = await context.uow.course_reader.get_course_task(
            task_id=command.task_id,
            with_observations=command.with_observations,
        )

        return ReadCourseTaskCommandResult(task=task)