from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)


class UpdateCourseTaskStatusAction(StrEnum):
    START = "start"
    SKIP = "skip"
    COMPLETE = "complete"
    REOPEN = "reopen"


@dataclass(frozen=True, kw_only=True)
class UpdateCourseTaskStatusCommand(Command):
    task_id: UUID
    action: UpdateCourseTaskStatusAction


@dataclass(frozen=True, kw_only=True)
class UpdateCourseTaskStatusCommandResult:
    task_id: UUID


@command_handler_registry.handler(UpdateCourseTaskStatusCommand)
class UpdateCourseTaskStatusCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateCourseTaskStatusCommand,
        context: CourseCommandHandlerContext,
    ) -> UpdateCourseTaskStatusCommandResult:
        task = await context.uow.course_writer.get_course_task_by_id(
            command.task_id,
        )
        if task is None:
            raise ValueError(f"Course task not found: {command.task_id}")

        match command.action:
            case UpdateCourseTaskStatusAction.START:
                task.start()
            case UpdateCourseTaskStatusAction.SKIP:
                task.skip()
            case UpdateCourseTaskStatusAction.COMPLETE:
                task.complete()
            case UpdateCourseTaskStatusAction.REOPEN:
                task.reopen()

        await context.uow.course_writer.update_course_task(task=task)

        return UpdateCourseTaskStatusCommandResult(task_id=task.id)