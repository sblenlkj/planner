from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.schedule.application.orchestration import (
    ScheduleCommandHandlerContext,
    command_handler_registry,
)
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


@dataclass(frozen=True, kw_only=True)
class ExpireReminderCommand(Command):
    reminder_id: UUID


@dataclass(frozen=True, kw_only=True)
class ExpireReminderCommandResult:
    reminder_id: UUID
    expired: bool


@command_handler_registry.handler(ExpireReminderCommand)
class ExpireReminderCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ExpireReminderCommand,
        context: ScheduleCommandHandlerContext,
    ) -> ExpireReminderCommandResult:
        reminder = await context.uow.commitment_writer.get_reminder_by_id(
            reminder_id=command.reminder_id,
        )

        if reminder is None:
            raise ValueError("reminder not found")

        if reminder.status != CommitmentStatus.ACTIVE:
            return ExpireReminderCommandResult(
                reminder_id=reminder.id,
                expired=False,
            )

        reminder.expire()

        await context.uow.commitment_writer.update_reminder(
            reminder=reminder,
        )

        return ExpireReminderCommandResult(
            reminder_id=reminder.id,
            expired=True,
        )