from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.runtime.application.orchestration import (
    RuntimeCommandHandlerContext,
    command_handler_registry,
)
from backend.context.runtime.application.ports.day_generation_stream_port import (
    DayGenerationStreamPort,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)
from backend.context.runtime.application.services.day_generation_request_service import (
    DayGenerationRequestResult,
    DayGenerationRequestService,
)


@dataclass(frozen=True, kw_only=True)
class RequestUserDayGenerationCommand(Command):
    user_id: UUID
    day: date


@dataclass(frozen=True, kw_only=True)
class RequestUserDayGenerationCommandResult:
    result: DayGenerationRequestResult




@command_handler_registry.handler(RequestUserDayGenerationCommand)
class RequestUserDayGenerationCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        schedule_runtime_port: ScheduleRuntimePort,
        day_generation_stream_port: DayGenerationStreamPort,
    ) -> None:
        self._day_generation_request_service = DayGenerationRequestService(
            schedule_runtime_port=schedule_runtime_port,
            day_generation_stream_port=day_generation_stream_port,
        )

    async def __call__(
        self,
        command: RequestUserDayGenerationCommand,
        context: RuntimeCommandHandlerContext,
    ) -> RequestUserDayGenerationCommandResult:
        result = await self._day_generation_request_service.request_generation_if_missing(
            user_id=command.user_id,
            day=command.day,
        )

        return RequestUserDayGenerationCommandResult(
            result=result,
        )