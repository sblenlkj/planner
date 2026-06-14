from __future__ import annotations

from typing import Any

from direttore import CommandHandlerContext, CommandHandlerRegistry, EventHandlerRegistry

from direttore import (
    CommandHandlerRegistry,
)

from backend.context.course.application.ports.course_unit_of_work import (
    CourseUnitOfWork,
)


COURSE_CONTEXT_NAME = "course"


class CourseCommandHandlerContext(CommandHandlerContext[Any]):
    uow: CourseUnitOfWork


command_handler_registry = CommandHandlerRegistry(
    source_name=COURSE_CONTEXT_NAME,
)

event_handler_registry = EventHandlerRegistry(source_name=COURSE_CONTEXT_NAME)