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
class GetUserRuntimeStatusCommand(Command):
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class GetUserRuntimeStatusCommandResult:
    user_id: UUID
    status: UserRuntimeStatus


@command_handler_registry.handler(GetUserRuntimeStatusCommand)
class GetUserRuntimeStatusCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: GetUserRuntimeStatusCommand,
        context: UserCommandHandlerContext,
    ) -> GetUserRuntimeStatusCommandResult:
        runtime_profile = await context.uow.users.get_runtime_profile_by_user_id(
            user_id=command.user_id,
        )

        if runtime_profile is None:
            raise ValueError("User runtime profile does not exist.")

        return GetUserRuntimeStatusCommandResult(
            user_id=command.user_id,
            status=runtime_profile.status,
        )