from __future__ import annotations

from dataclasses import dataclass

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)
from backend.shared.auth import JwtTokenService
from backend.shared.security.password_hashing import PasswordHasher


@dataclass(frozen=True, kw_only=True)
class AuthenticateUserCommand(Command):
    login: str
    password: str


@dataclass(frozen=True, kw_only=True)
class AuthenticateUserCommandResult:
    user_id: str
    access_token: str
    role: str


@command_handler_registry.handler(AuthenticateUserCommand)
class AuthenticateUserCommandHandler(AbstractCommandHandler):
    def __init__(
        self,
        *,
        password_hasher: PasswordHasher,
        jwt_token_service: JwtTokenService,
    ) -> None:
        self._password_hasher = password_hasher
        self._jwt_token_service = jwt_token_service

    async def __call__(
        self,
        command: AuthenticateUserCommand,
        context: UserCommandHandlerContext,
    ) -> AuthenticateUserCommandResult:
        user = await context.uow.users.get_user_by_login(login=command.login)

        if user is None:
            raise ValueError("Invalid user credentials.")

        password_is_valid = self._password_hasher.verify_password(
            password=command.password,
            password_hash=user.password_hash,
        )

        if not password_is_valid:
            raise ValueError("Invalid user credentials.")

        access_token = self._jwt_token_service.create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        return AuthenticateUserCommandResult(
            user_id=str(user.id),
            access_token=access_token,
            role=user.role.value,
        )