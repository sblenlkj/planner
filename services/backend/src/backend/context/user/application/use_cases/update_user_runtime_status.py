from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)
from backend.context.user.domain.user_runtime_profile import UserRuntimeStatus


@dataclass(frozen=True, kw_only=True)
class UpdateUserRuntimeStatusCommand(Command):
    user_id: UUID
    status: UserRuntimeStatus


@dataclass(frozen=True, kw_only=True)
class UpdateUserRuntimeStatusCommandResult:
    user_id: UUID
    status: UserRuntimeStatus


@command_handler_registry.handler(UpdateUserRuntimeStatusCommand)
class UpdateUserRuntimeStatusCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateUserRuntimeStatusCommand,
        context: UserCommandHandlerContext,
    ) -> UpdateUserRuntimeStatusCommandResult:
        user = await context.uow.users.get_user_by_id(user_id=command.user_id)

        if user is None:
            raise ValueError("User does not exist.")

        if not user.is_regular_user:
            raise ValueError("Only regular users can have runtime profile status.")

        await context.uow.users.update_runtime_status(
            user_id=command.user_id,
            status=command.status,
        )

        return UpdateUserRuntimeStatusCommandResult(
            user_id=command.user_id,
            status=command.status,
        )