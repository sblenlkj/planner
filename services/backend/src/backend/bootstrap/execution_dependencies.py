from __future__ import annotations

from direttore.orchestration import (
    ModularMonolithExecutionDependencyContext,
    ModularMonolithExecutionDependencyRegistry,
)

from backend.context.schedule.adapters.outbound.user_utc_offset_adapter import (
    InProcessUserUtcOffsetAdapter,
)
from backend.context.schedule.application.ports.user_utc_offset_port import (
    UserUtcOffsetPort,
)
from backend.context.runtime.adapters.schedule_runtime_adapter import (
    InProcessScheduleRuntimeAdapter,
)
from backend.context.runtime.application.ports.schedule_runtime_port import (
    ScheduleRuntimePort,
)
from backend.context.runtime.application.ports.user_runtime_port import (
    UserRuntimePort,
)
from backend.context.runtime.adapters.user_runtime_adapter import (
    InProcessUserRuntimeAdapter
)

def build_execution_dependency_registry(
) -> ModularMonolithExecutionDependencyRegistry:
    registry = ModularMonolithExecutionDependencyRegistry()

    @registry.override(UserUtcOffsetPort)
    def build_user_utc_offset_port(
        context: ModularMonolithExecutionDependencyContext,
    ) -> UserUtcOffsetPort:
        return InProcessUserUtcOffsetAdapter(
            runtime=context.runtime,
        )

    @registry.override(ScheduleRuntimePort)
    def build_schedule_runtime_adapter(
        context: ModularMonolithExecutionDependencyContext,
    ) -> ScheduleRuntimePort:
        return InProcessScheduleRuntimeAdapter(
            runtime=context.runtime,
        )
    
    @registry.override(UserRuntimePort)
    def build_user_runtime_adapter(
        context: ModularMonolithExecutionDependencyContext,
    ) -> UserRuntimePort:
        return InProcessUserRuntimeAdapter(
            runtime=context.runtime,
        )

    return registry