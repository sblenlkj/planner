from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)


@dataclass(frozen=True, kw_only=True)
class UpdateUserLastSessionAtCommand(Command):
    user_id: UUID
    last_session_at: datetime


@dataclass(frozen=True, kw_only=True)
class UpdateUserLastSessionAtCommandResult:
    user_id: UUID
    last_session_at: datetime


@command_handler_registry.handler(UpdateUserLastSessionAtCommand)
class UpdateUserLastSessionAtCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateUserLastSessionAtCommand,
        context: UserCommandHandlerContext,
    ) -> UpdateUserLastSessionAtCommandResult:
        user = await context.uow.users.get_user_by_id(user_id=command.user_id)

        if user is None:
            raise ValueError("User does not exist.")

        if not user.is_regular_user:
            raise ValueError("Only regular users can have last session metadata.")

        await context.uow.users.update_last_session_at(
            user_id=command.user_id,
            last_session_at=command.last_session_at,
        )

        return UpdateUserLastSessionAtCommandResult(
            user_id=command.user_id,
            last_session_at=command.last_session_at,
        )