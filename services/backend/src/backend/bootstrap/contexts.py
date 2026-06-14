from __future__ import annotations

from direttore import ModularDirettoreContext

from backend.context.analytics.adapters.outbound.uow import (
    SqlAlchemyAnalyticsCommandUnitOfWork,
)
from backend.context.analytics.application.orchestration import (
    command_handler_registry as analytics_command_handler_registry,
    event_handler_registry as analytics_event_handler_registry,
)
from backend.context.course.adapters.outbound.uow import (
    SqlAlchemyCourseCommandUnitOfWork,
)
from backend.context.course.application.orchestration import (
    command_handler_registry as course_command_handler_registry,
    event_handler_registry as course_event_handler_registry,
)
from backend.context.runtime.adapters.outbound.uow import (
    SqlAlchemyRuntimeCommandUnitOfWork,
)
from backend.context.runtime.application.orchestration import (
    command_handler_registry as runtime_command_handler_registry,
    event_handler_registry as runtime_event_handler_registry,
)
from backend.context.schedule.adapters.outbound.uow import (
    SqlAlchemyScheduleCommandUnitOfWork,
    SqlAlchemyScheduleQueryUnitOfWork,
)
from backend.context.schedule.application.orchestration import (
    command_handler_registry as schedule_command_handler_registry,
    event_handler_registry as schedule_event_handler_registry,
    query_handler_registry as schedule_query_handler_registry,
)
from backend.context.user.adapters.outbound.uow import (
    SqlAlchemyUserCommandUnitOfWork,
)
from backend.context.user.application.orchestration import (
    command_handler_registry as user_command_handler_registry,
    event_handler_registry as user_event_handler_registry,
)

# Import modules with decorated handlers so decorators run.
import backend.context.runtime.application.use_cases  # noqa: F401
import backend.context.user.application.use_cases  # noqa: F401
import backend.context.course.application.use_cases  # noqa: F401
import backend.context.analytics.application.use_cases  # noqa: F401
import backend.context.schedule.application.use_cases  # noqa: F401
import backend.context.schedule.application.queries  # noqa: F401


def build_contexts() -> list[ModularDirettoreContext]:
    return [
        ModularDirettoreContext(
            command_handler_registry=user_command_handler_registry,
            event_handler_registry=user_event_handler_registry,
            command_root_uow_type=SqlAlchemyUserCommandUnitOfWork,
        ),
        ModularDirettoreContext(
            command_handler_registry=runtime_command_handler_registry,
            event_handler_registry=runtime_event_handler_registry,
            command_root_uow_type=SqlAlchemyRuntimeCommandUnitOfWork,
        ),
        ModularDirettoreContext(
            command_handler_registry=course_command_handler_registry,
            event_handler_registry=course_event_handler_registry,
            command_root_uow_type=SqlAlchemyCourseCommandUnitOfWork,
        ),
        ModularDirettoreContext(
            command_handler_registry=analytics_command_handler_registry,
            event_handler_registry=analytics_event_handler_registry,
            command_root_uow_type=SqlAlchemyAnalyticsCommandUnitOfWork,
        ),
        ModularDirettoreContext(
            command_handler_registry=schedule_command_handler_registry,
            event_handler_registry=schedule_event_handler_registry,
            command_root_uow_type=SqlAlchemyScheduleCommandUnitOfWork,
            query_handler_registry=schedule_query_handler_registry,
            query_root_uow_type=SqlAlchemyScheduleQueryUnitOfWork,
        ),
    ]