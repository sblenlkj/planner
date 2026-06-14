from __future__ import annotations

from typing import Any

from direttore import CommandHandlerContext, CommandHandlerRegistry, EventHandlerRegistry

from .ports.user_unit_of_work import UserUnitOfWork

USER_SOURCE_NAME = "user"


class UserCommandHandlerContext(CommandHandlerContext[Any]):
    uow: UserUnitOfWork


command_handler_registry = CommandHandlerRegistry(source_name=USER_SOURCE_NAME)


event_handler_registry = EventHandlerRegistry(source_name=USER_SOURCE_NAME)