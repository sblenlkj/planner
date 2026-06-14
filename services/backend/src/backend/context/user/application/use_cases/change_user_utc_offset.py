from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)


@dataclass(frozen=True, kw_only=True)
class ChangeUserUtcOffsetCommand(Command):
    user_id: UUID
    utc_offset_minutes: int


@dataclass(frozen=True, kw_only=True)
class ChangeUserUtcOffsetCommandResult:
    user_id: UUID
    utc_offset_minutes: int


@command_handler_registry.handler(
    ChangeUserUtcOffsetCommand,
)
class ChangeUserUtcOffsetCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ChangeUserUtcOffsetCommand,
        context: UserCommandHandlerContext,
    ) -> ChangeUserUtcOffsetCommandResult:
        user = await context.uow.users.get_user_by_id(user_id=command.user_id)

        if user is None:
            raise ValueError("User does not exist.")

        preferences = await context.uow.users.get_preferences_by_user_id(
            user_id=command.user_id,
        )

        if preferences is None:
            raise ValueError("User preferences do not exist.")

        preferences.change_utc_offset_minutes(command.utc_offset_minutes)

        await context.uow.users.change_user_utc_offset_minutes(
            user_id=command.user_id,
            utc_offset_minutes=preferences.utc_offset_minutes,
        )

        return ChangeUserUtcOffsetCommandResult(
            user_id=command.user_id,
            utc_offset_minutes=preferences.utc_offset_minutes,
        )