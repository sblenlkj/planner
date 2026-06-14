from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)


class UpdateCourseStatusAction(StrEnum):
    COMPLETE = "complete"
    ARCHIVE = "archive"
    REACTIVATE = "reactivate"


@dataclass(frozen=True, kw_only=True)
class UpdateCourseStatusCommand(Command):
    course_id: UUID
    action: UpdateCourseStatusAction


@dataclass(frozen=True, kw_only=True)
class UpdateCourseStatusCommandResult:
    course_id: UUID


@command_handler_registry.handler(UpdateCourseStatusCommand)
class UpdateCourseStatusCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateCourseStatusCommand,
        context: CourseCommandHandlerContext,
    ) -> UpdateCourseStatusCommandResult:
        course = await context.uow.course_writer.get_course_by_id(
            command.course_id,
        )
        if course is None:
            raise ValueError(f"Course not found: {command.course_id}")

        match command.action:
            case UpdateCourseStatusAction.COMPLETE:
                course.complete()
            case UpdateCourseStatusAction.ARCHIVE:
                course.archive()
            case UpdateCourseStatusAction.REACTIVATE:
                course.reactivate()

        await context.uow.course_writer.update_course(course=course)

        return UpdateCourseStatusCommandResult(course_id=course.id)