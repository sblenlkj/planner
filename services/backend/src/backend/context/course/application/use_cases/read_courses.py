from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.dto.course_read_models import (
    CourseListItem,
)
from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.value_objects.course_status import CourseStatus


@dataclass(frozen=True, kw_only=True)
class ReadCoursesCommand(Command):
    user_id: UUID
    status: CourseStatus | None = None


@dataclass(frozen=True, kw_only=True)
class ReadCoursesCommandResult:
    courses: list[CourseListItem]


@command_handler_registry.handler(ReadCoursesCommand)
class ReadCoursesCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ReadCoursesCommand,
        context: CourseCommandHandlerContext,
    ) -> ReadCoursesCommandResult:
        courses = await context.uow.course_reader.list_courses(
            user_id=command.user_id,
            status=command.status,
        )

        return ReadCoursesCommandResult(courses=courses)