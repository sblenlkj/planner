from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)


@dataclass(frozen=True, kw_only=True)
class GetUserUtcOffsetCommand(Command):
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class GetUserUtcOffsetCommandResult:
    user_id: UUID
    utc_offset_minutes: int


@command_handler_registry.handler(
    GetUserUtcOffsetCommand,
)
class GetUserUtcOffsetCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: GetUserUtcOffsetCommand,
        context: UserCommandHandlerContext,
    ) -> GetUserUtcOffsetCommandResult:
        preferences = await context.uow.users.get_preferences_by_user_id(
            user_id=command.user_id,
        )

        if preferences is None:
            raise ValueError("User preferences do not exist.")

        return GetUserUtcOffsetCommandResult(
            user_id=command.user_id,
            utc_offset_minutes=preferences.utc_offset_minutes,
        )