from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.dto import UpdateUserDTO
from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)

@dataclass(frozen=True, kw_only=True)
class UpdateUserCommand(Command):
    user_id: UUID
    login: str | None = None
    name: str | None = None
    language: str | None = None
    utc_offset_minutes: int | None = None
    region: str | None = None


@dataclass(frozen=True, kw_only=True)
class UpdateUserCommandResult:
    user_id: UUID


@command_handler_registry.handler(
    UpdateUserCommand,
)
class UpdateUserCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: UpdateUserCommand,
        context: UserCommandHandlerContext,
    ) -> UpdateUserCommandResult:
        user = await context.uow.users.get_user_by_id(user_id=command.user_id)

        if user is None:
            raise ValueError("User does not exist.")

        update = UpdateUserDTO(
            user_id=command.user_id,
            login=_normalize_optional_text(command.login),
            name=_normalize_optional_text(command.name),
            language=_normalize_optional_text(command.language),
            utc_offset_minutes=command.utc_offset_minutes,
            region=_normalize_optional_text(command.region),
        )

        await context.uow.users.update_user(update=update)

        return UpdateUserCommandResult(user_id=command.user_id)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    return value or None