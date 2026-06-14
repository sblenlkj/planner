from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.entities.course import Course


@dataclass(frozen=True, kw_only=True)
class CreateCourseCommand(Command):
    user_id: UUID
    title: str
    description: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateCourseCommandResult:
    course_id: UUID


@command_handler_registry.handler(CreateCourseCommand)
class CreateCourseCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateCourseCommand,
        context: CourseCommandHandlerContext,
    ) -> CreateCourseCommandResult:
        course_id = command.id or uuid4()

        course = Course.create(
            id=course_id,
            user_id=command.user_id,
            title=command.title,
            description=command.description,
        )

        await context.uow.course_writer.add_course(course=course)

        return CreateCourseCommandResult(course_id=course_id)