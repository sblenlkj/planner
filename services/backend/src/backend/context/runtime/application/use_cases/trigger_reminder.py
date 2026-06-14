from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.runtime_jobs import (
    REMINDER_TRIGGER_HANDLER_KEY,
)
from backend.context.runtime.application.ports.telegram_gateway_port import (
    TelegramGatewayPort,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)


@dataclass(frozen=True, kw_only=True)
class TriggerReminderCommand(Command):
    reminder_id: UUID
    user_id: UUID
    text: str


@dataclass(frozen=True, kw_only=True)
class TriggerReminderCommandResult:
    delivered: bool


@command_handler_registry.handler(TriggerReminderCommand, key=REMINDER_TRIGGER_HANDLER_KEY)
class TriggerReminderCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        telegram_gateway_port: TelegramGatewayPort,
        schedule_reminder_port: ScheduleRuntimePort,
    ) -> None:
        self._telegram_gateway_port = telegram_gateway_port
        self._schedule_reminder_port = schedule_reminder_port

    async def __call__(
        self,
        command: TriggerReminderCommand,
        context: RuntimeCommandHandlerContext,
    ) -> TriggerReminderCommandResult:
        await self._telegram_gateway_port.send_message(
            user_id=command.user_id,
            text=command.text,
        )

        await self._schedule_reminder_port.expire_reminder(
            reminder_id=command.reminder_id,
        )

        return TriggerReminderCommandResult(delivered=True)