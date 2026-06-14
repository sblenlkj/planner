from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.template.entities.weekly_schedule_observation import (
    WeeklyScheduleObservation,
)


@dataclass(frozen=True, kw_only=True)
class CreateWeeklyScheduleObservationCommand(Command):
    user_id: UUID
    description: str
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateWeeklyScheduleObservationCommandResult:
    observation_id: UUID
    template_id: UUID


@command_handler_registry.handler(CreateWeeklyScheduleObservationCommand)
class CreateWeeklyScheduleObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateWeeklyScheduleObservationCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateWeeklyScheduleObservationCommandResult:
        template = await context.uow.template_writer.get_weekly_schedule_template_by_user_id(
            user_id=command.user_id,
        )

        if template is None:
            raise ValueError("weekly schedule template not found")

        observation_id = command.id or uuid4()

        observation = WeeklyScheduleObservation(
            id=observation_id,
            weekly_schedule_template_id=template.id,
            description=command.description,
        )

        template.add_observation(observation)

        await context.uow.template_writer.update_weekly_schedule_template(
            template=template,
        )

        return CreateWeeklyScheduleObservationCommandResult(
            observation_id=observation.id,
            template_id=template.id,
        )