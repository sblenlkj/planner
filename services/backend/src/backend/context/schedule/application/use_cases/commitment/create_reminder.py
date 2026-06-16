from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.application.ports.user_utc_offset_port import (
    UserUtcOffsetPort,
)
from backend.context.schedule.application.reminder_runtime import (
    RUNTIME_TRIGGER_REMINDER_HANDLER_KEY,
    build_reminder_text,
)
from backend.context.schedule.domain.commitment.entities.reminder import Reminder
from backend.shared.application.ports.api_scheduler import (
    ApiScheduledOperation,
    ApiSchedulerPort,
)


@dataclass(frozen=True, kw_only=True)
class CreateReminderCommand(Command):
    user_id: UUID
    remind_at: datetime
    title: str
    description: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateReminderCommandResult:
    reminder_id: UUID


@command_handler_registry.handler(CreateReminderCommand)
class CreateReminderCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        user_utc_offset: UserUtcOffsetPort,
        api_scheduler: ApiSchedulerPort,
    ) -> None:
        self._user_utc_offset = user_utc_offset
        self._api_scheduler = api_scheduler

    async def __call__(
        self,
        command: CreateReminderCommand,
        context: ScheduleCommandHandlerContext,
    ) -> CreateReminderCommandResult:
        reminder_id = command.id or uuid4()

        utc_offset_minutes = await self._user_utc_offset.get_user_utc_offset_minutes(
            user_id=command.user_id,
        )

        print(
            f"utc_offset_minutes: {utc_offset_minutes}",
            f"remind_at: {command.remind_at}",
        )

        remind_at_utc = self._to_utc(
            local_datetime=command.remind_at,
            utc_offset_minutes=utc_offset_minutes,
        )

        reminder = Reminder(
            id=reminder_id,
            user_id=command.user_id,
            remind_at=remind_at_utc,
            title=command.title,
            description=command.description,
        )

        await context.uow.commitment_writer.add_reminder(
            reminder=reminder,
        )

        await self._api_scheduler.schedule_operation(
            ApiScheduledOperation(
                operation_key=str(reminder.id),
                run_at=reminder.remind_at,
                handler_key=RUNTIME_TRIGGER_REMINDER_HANDLER_KEY,
                payload={
                    "reminder_id": str(reminder.id),
                    "user_id": str(reminder.user_id),
                    "text": build_reminder_text(reminder),
                },
                owner_user_id=reminder.user_id,
            )
        )

        return CreateReminderCommandResult(
            reminder_id=reminder.id,
        )

    @staticmethod
    def _to_utc(
        *,
        local_datetime: datetime,
        utc_offset_minutes: int,
    ) -> datetime:
        # Contract:
        # utc_offset_minutes is the user's standard offset from UTC.
        #
        # Examples:
        # UTC+3  -> +180
        # UTC-5  -> -300
        #
        # Conversion:
        # local time -> UTC time
        # UTC = local - offset
        #
        # Example:
        # local_datetime=2026-06-16 09:30:00
        # utc_offset_minutes=180
        # stored UTC=2026-06-16 06:30:00
        #
        # Database stores UTC as TIMESTAMP WITHOUT TIME ZONE.
        # If datetime has tzinfo, ignore tzinfo and treat wall time as user-local.

        local_naive = local_datetime.replace(tzinfo=None)

        return local_naive - timedelta(minutes=utc_offset_minutes)