from __future__ import annotations

from typing import Any

from direttore import CommandHandlerRegistry, QueryHandlerRegistry, EventHandlerRegistry, CommandHandlerContext, QueryHandlerContext

from backend.context.schedule.application.ports.schedule_read_unit_of_work import (
    ScheduleReadUnitOfWork,
)
from backend.context.schedule.application.ports.schedule_write_unit_of_work import (
    ScheduleWriteUnitOfWork,
)


SCHEDULE_CONTEXT_NAME = "schedule"


class ScheduleCommandHandlerContext(CommandHandlerContext[Any]):
    uow: ScheduleWriteUnitOfWork


class ScheduleQueryHandlerContext(QueryHandlerContext[Any]):
    uow: ScheduleReadUnitOfWork


command_handler_registry = CommandHandlerRegistry(
    source_name=SCHEDULE_CONTEXT_NAME,
)

query_handler_registry = QueryHandlerRegistry(
    source_name=SCHEDULE_CONTEXT_NAME,
)

event_handler_registry = EventHandlerRegistry(
    source_name=SCHEDULE_CONTEXT_NAME,
)