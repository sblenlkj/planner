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
        if local_datetime.tzinfo is not None:
            raise ValueError("remind_at must be naive user-local datetime")

        utc_datetime = local_datetime - timedelta(minutes=utc_offset_minutes)

        return utc_datetime.replace(tzinfo=UTC)