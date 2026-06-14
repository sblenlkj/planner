from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.entities.course_task import CourseTask
from backend.context.course.domain.value_objects.course_task_priority import (
    CourseTaskPriority,
)


@dataclass(frozen=True, kw_only=True)
class CreateCourseTaskCommand(Command):
    course_id: UUID
    title: str
    description: str | None = None
    priority: int | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateCourseTaskCommandResult:
    task_id: UUID


@command_handler_registry.handler(CreateCourseTaskCommand)
class CreateCourseTaskCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateCourseTaskCommand,
        context: CourseCommandHandlerContext,
    ) -> CreateCourseTaskCommandResult:
        course = await context.uow.course_writer.get_course_by_id(
            command.course_id,
        )
        if course is None:
            raise ValueError(f"Course not found: {command.course_id}")

        task_id = command.id or uuid4()

        priority = (
            CourseTaskPriority(value=command.priority)
            if command.priority is not None
            else CourseTaskPriority.normal()
        )

        task = CourseTask.create(
            id=task_id,
            course_id=command.course_id,
            title=command.title,
            description=command.description,
            priority=priority,
        )

        await context.uow.course_writer.add_course_task(task=task)

        return CreateCourseTaskCommandResult(task_id=task_id)