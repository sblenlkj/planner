from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.execution.entities.schedule_date_observation import (
    ScheduleDateObservation,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDateObservationCommand(Command):
    user_id: UUID
    starts_on: ScheduleDate
    description: str
    ends_on: ScheduleDate | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDateObservationCommandResult:
    observation_id: UUID


@command_handler_registry.handler(CreateScheduleDateObservationCommand)
class CreateScheduleDateObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateScheduleDateObservationCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateScheduleDateObservationCommandResult:
        observation_id = command.id or uuid4()

        observation = ScheduleDateObservation(
            id=observation_id,
            user_id=command.user_id,
            starts_on=command.starts_on,
            ends_on=command.ends_on,
            description=command.description,
        )

        await context.uow.execution_writer.add_schedule_date_observation(
            observation=observation,
        )

        return CreateScheduleDateObservationCommandResult(
            observation_id=observation.id,
        )