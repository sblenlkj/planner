from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.course.application.orchestration import (
    CourseCommandHandlerContext,
    command_handler_registry,
)
from backend.context.course.domain.entities.course_observation import (
    CourseObservation,
)


@dataclass(frozen=True, kw_only=True)
class CreateCourseObservationCommand(Command):
    course_id: UUID
    title: str
    description: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateCourseObservationCommandResult:
    observation_id: UUID


@command_handler_registry.handler(CreateCourseObservationCommand)
class CreateCourseObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateCourseObservationCommand,
        context: CourseCommandHandlerContext,
    ) -> CreateCourseObservationCommandResult:
        course = await context.uow.course_writer.get_course_by_id(
            command.course_id,
        )
        if course is None:
            raise ValueError(f"Course not found: {command.course_id}")

        observation_id = command.id or uuid4()

        observation = CourseObservation.create(
            id=observation_id,
            course_id=command.course_id,
            title=command.title,
            description=command.description,
        )

        await context.uow.course_writer.add_course_observation(
            observation=observation,
        )

        return CreateCourseObservationCommandResult(
            observation_id=observation_id,
        )