from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

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
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)
from backend.shared.application.ports.api_scheduler import (
    ApiScheduledOperation,
    ApiSchedulerPort,
)


@dataclass(frozen=True, kw_only=True)
class UpdateReminderCommand(Command):
    reminder_id: UUID
    remind_at: datetime | None = None
    title: str | None = None
    description: str | None = None
    status: CommitmentStatus | None = None


@dataclass(frozen=True, kw_only=True)
class UpdateReminderCommandResult:
    reminder_id: UUID


@command_handler_registry.handler(UpdateReminderCommand)
class UpdateReminderCommandHandler(AbstractCommandHandler):
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
        command: UpdateReminderCommand,
        context: ScheduleCommandHandlerContext,
    ) -> UpdateReminderCommandResult:
        reminder = await context.uow.commitment_writer.get_reminder_by_id(
            reminder_id=command.reminder_id,
        )

        if reminder is None:
            raise ValueError("reminder not found")

        scheduler_payload_changed = False
        scheduler_time_changed = False
        scheduler_status_changed = False

        if command.remind_at is not None:
            utc_offset_minutes = await self._user_utc_offset.get_user_utc_offset_minutes(
                user_id=reminder.user_id,
            )

            remind_at_utc = self._to_utc(
                local_datetime=command.remind_at,
                utc_offset_minutes=utc_offset_minutes,
            )

            reminder.reschedule(remind_at_utc)
            scheduler_time_changed = True

        if command.title is not None:
            reminder.rename(command.title)
            scheduler_payload_changed = True

        if command.description is not None:
            reminder.change_description(command.description)
            scheduler_payload_changed = True

        if command.status is not None:
            if command.status == CommitmentStatus.ACTIVE:
                reminder.reactivate()
            elif command.status == CommitmentStatus.CANCELLED:
                reminder.cancel()
            elif command.status == CommitmentStatus.EXPIRED:
                reminder.expire()
            else:
                raise ValueError("unsupported reminder status")

            scheduler_status_changed = True

        await context.uow.commitment_writer.update_reminder(
            reminder=reminder,
        )

        if reminder.status == CommitmentStatus.ACTIVE:
            if (
                scheduler_time_changed
                or scheduler_payload_changed
                or scheduler_status_changed
            ):
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
        elif scheduler_status_changed:
            await self._api_scheduler.cancel_operation(
                operation_key=str(reminder.id),
            )

        return UpdateReminderCommandResult(
            reminder_id=reminder.id,
        )

    @staticmethod
    def _to_utc(
        *,
        local_datetime: datetime,
        utc_offset_minutes: int,
    ) -> datetime:
        # MVP rule:
        # API may receive timezone-aware UTC datetime from Agent Server.
        # Database stores UTC as TIMESTAMP WITHOUT TIME ZONE.
        #
        # Therefore we normalize to UTC and strip tzinfo before persistence.

        if local_datetime.tzinfo is not None:
            return local_datetime.astimezone(UTC).replace(tzinfo=None)

        # Naive datetime is treated as already UTC.
        return local_datetime