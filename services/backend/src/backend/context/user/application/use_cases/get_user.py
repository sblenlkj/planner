from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)
from backend.context.user.domain.user_runtime_profile import UserRuntimeStatus
from backend.context.user.application.errors import UserNotFoundError

@dataclass(frozen=True, kw_only=True)
class GetUserCommand(Command):
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class GetUserCommandResult:
    user_id: UUID
    login: str | None
    name: str | None
    language: str | None
    utc_offset_minutes: int | None
    region: str | None
    runtime_status: UserRuntimeStatus | None


@command_handler_registry.handler(GetUserCommand)
class GetUserCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: GetUserCommand,
        context: UserCommandHandlerContext,
    ) -> GetUserCommandResult:
        user = await context.uow.users.get_user_by_id(user_id=command.user_id)

        if user is None:
            raise UserNotFoundError(user_id=command.user_id)

        preferences = await context.uow.users.get_preferences_by_user_id(
            user_id=command.user_id,
        )
        runtime_profile = await context.uow.users.get_runtime_profile_by_user_id(
            user_id=command.user_id,
        )

        return GetUserCommandResult(
            user_id=user.id,
            login=user.login,
            name=user.name,
            language=preferences.language if preferences is not None else None,
            utc_offset_minutes=(
                preferences.utc_offset_minutes if preferences is not None else None
            ),
            region=preferences.region if preferences is not None else None,
            runtime_status=(
                runtime_profile.status if runtime_profile is not None else None
            ),
        )