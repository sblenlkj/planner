from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)
from backend.context.user.domain.user import User
from backend.shared.security.password_hashing import PasswordHasher


@dataclass(frozen=True, kw_only=True)
class CreateUserCommand(Command):
    password: str
    login: str | None = None
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateUserCommandResult:
    user_id: UUID


@command_handler_registry.handler(CreateUserCommand)
class CreateUserCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateUserCommand,
        context: UserCommandHandlerContext,
    ) -> CreateUserCommandResult:
        user_id = command.id or uuid4()
        password_hash = PasswordHasher().hash_password(command.password)

        user = User.create_user(
            id=user_id,
            login=command.login,
            password_hash=password_hash,
        )

        await context.uow.users.add_user(user=user)

        return CreateUserCommandResult(user_id=user_id)