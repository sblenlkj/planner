from __future__ import annotations


from typing import Any

from direttore import CommandHandlerContext, CommandHandlerRegistry, EventHandlerRegistry

from backend.context.analytics.application.ports.analytics_unit_of_work import (
    AnalyticsUnitOfWork,
)


ANALYTICS_CONTEXT_NAME = "analytics"


class AnalyticsCommandHandlerContext(CommandHandlerContext[Any]):
    uow: AnalyticsUnitOfWork


command_handler_registry = CommandHandlerRegistry(
    source_name=ANALYTICS_CONTEXT_NAME,
)


event_handler_registry = EventHandlerRegistry(
    source_name=ANALYTICS_CONTEXT_NAME,
)