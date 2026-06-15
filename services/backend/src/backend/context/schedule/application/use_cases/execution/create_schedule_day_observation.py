from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.schedule_day_observation import (
    ScheduleDayObservation,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDayObservationCommand(Command):
    user_id: UUID
    date: ScheduleDate
    description: str
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateScheduleDayObservationCommandResult:
    observation_id: UUID


@command_handler_registry.handler(CreateScheduleDayObservationCommand)
class CreateScheduleDayObservationCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateScheduleDayObservationCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateScheduleDayObservationCommandResult:
        schedule_day = (
            await context.uow.execution_writer.get_schedule_day_by_user_id_and_date(
                user_id=command.user_id,
                date=command.date,
            )
        )

        if schedule_day is None:
            schedule_day = ScheduleDay(
                user_id=command.user_id,
                date=command.date,
                title="Unplanned day",
                description="Minimal schedule day created automatically for observations.",
                blocks=[],
                activities=[],
            )

            await context.uow.execution_writer.add_schedule_day(
                schedule_day=schedule_day,
            )

        observation_id = command.id or uuid4()

        observation = ScheduleDayObservation(
            id=observation_id,
            user_id=command.user_id,
            date=command.date,
            description=command.description,
        )

        schedule_day.add_observation(observation)

        await context.uow.execution_writer.update_schedule_day(
            schedule_day=schedule_day,
        )

        return CreateScheduleDayObservationCommandResult(
            observation_id=observation.id,
        )