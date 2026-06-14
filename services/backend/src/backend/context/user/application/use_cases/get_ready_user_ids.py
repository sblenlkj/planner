from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.user.application.orchestration import (
    UserCommandHandlerContext,
    command_handler_registry,
)


@dataclass(frozen=True, kw_only=True)
class GetReadyUserIdsCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class GetReadyUserIdsCommandResult:
    user_ids: tuple[UUID, ...]


@command_handler_registry.handler(GetReadyUserIdsCommand)
class GetReadyUserIdsCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: GetReadyUserIdsCommand,
        context: UserCommandHandlerContext,
    ) -> GetReadyUserIdsCommandResult:
        user_ids = await context.uow.users.list_ready_user_ids()

        return GetReadyUserIdsCommandResult(user_ids=user_ids)