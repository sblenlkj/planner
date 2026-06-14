from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.entities.course_task_observation import (
    CourseTaskObservation,
)


@dataclass(frozen=True, kw_only=True)
class CreateCourseTaskObservationCommand(Command):
    task_id: UUID
    title: str
    description: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateCourseTaskObservationCommandResult:
    observation_id: UUID


@command_handler_registry.handler(CreateCourseTaskObservationCommand)
class CreateCourseTaskObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateCourseTaskObservationCommand,
        context: CourseCommandHandlerContext,
    ) -> CreateCourseTaskObservationCommandResult:
        task = await context.uow.course_writer.get_course_task_by_id(
            command.task_id,
        )
        if task is None:
            raise ValueError(f"Course task not found: {command.task_id}")

        observation_id = command.id or uuid4()

        observation = CourseTaskObservation.create(
            id=observation_id,
            task_id=command.task_id,
            title=command.title,
            description=command.description,
        )

        await context.uow.course_writer.add_course_task_observation(
            observation=observation,
        )

        return CreateCourseTaskObservationCommandResult(
            observation_id=observation_id,
        )