from __future__ import annotations

from typing import Any

from direttore import CommandHandlerContext, CommandHandlerRegistry, EventHandlerRegistry

from backend.context.runtime.application.ports.runtime_unit_of_work import (
    RuntimeUnitOfWork,
)


RUNTIME_CONTEXT_NAME = "runtime"

class RuntimeCommandHandlerContext(CommandHandlerContext[Any]):
    uow: RuntimeUnitOfWork


command_handler_registry = CommandHandlerRegistry(
    source_name=RUNTIME_CONTEXT_NAME,
)


event_handler_registry = EventHandlerRegistry(source_name=RUNTIME_CONTEXT_NAME)