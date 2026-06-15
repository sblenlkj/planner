from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.runtime_jobs import (
    REMINDER_TRIGGER_HANDLER_KEY,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)
from backend.shared.application.ports.api_scheduler import (
    ApiScheduledOperation,
    ApiSchedulerPort,
)


@dataclass(frozen=True, kw_only=True)
class RecoverActiveFutureRemindersCommand(Command):
    now_utc: datetime | None = None


@dataclass(frozen=True, kw_only=True)
class RecoverActiveFutureRemindersCommandResult:
    recovered_count: int


@command_handler_registry.handler(RecoverActiveFutureRemindersCommand)
class RecoverActiveFutureRemindersCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        schedule_reminder_port: ScheduleRuntimePort,
        api_scheduler: ApiSchedulerPort,
    ) -> None:
        self._schedule_reminder_port = schedule_reminder_port
        self._api_scheduler = api_scheduler

    async def __call__(
        self,
        command: RecoverActiveFutureRemindersCommand,
        context: RuntimeCommandHandlerContext,
    ) -> RecoverActiveFutureRemindersCommandResult:
        now_utc = self._resolve_now_utc(command.now_utc)

        reminders = await self._schedule_reminder_port.list_active_future_reminders(
            now_utc=now_utc,
        )

        for reminder in reminders:
            await self._api_scheduler.schedule_operation(
                ApiScheduledOperation(
                    operation_key=str(reminder.id),
                    run_at=reminder.remind_at,
                    handler_key=REMINDER_TRIGGER_HANDLER_KEY,
                    payload={
                        "reminder_id": str(reminder.id),
                        "user_id": str(reminder.user_id),
                        "text": reminder.text,
                    },
                    owner_user_id=reminder.user_id,
                )
            )

        return RecoverActiveFutureRemindersCommandResult(
            recovered_count=len(reminders),
        )

    @staticmethod
    def _resolve_now_utc(now_utc: datetime | None) -> datetime:
        if now_utc is None:
            return datetime.now(UTC).replace(tzinfo=None)

        if now_utc.tzinfo is None:
            return now_utc

        return now_utc.astimezone(UTC).replace(tzinfo=None)