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
class CreateAdminCommand(Command):
    login: str
    name: str
    password: str
    id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class CreateAdminCommandResult:
    admin_id: UUID


@command_handler_registry.handler(CreateAdminCommand)
class CreateAdminCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: CreateAdminCommand,
        context: UserCommandHandlerContext,
    ) -> CreateAdminCommandResult:
        admin_id = command.id or uuid4()
        password_hash = PasswordHasher().hash_password(command.password)

        admin = User.create_admin(
            id=admin_id,
            login=command.login,
            name=command.name,
            password_hash=password_hash,
        )

        await context.uow.users.add_admin(admin=admin)

        return CreateAdminCommandResult(admin_id=admin_id)