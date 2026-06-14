from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractCommandHandler, Command

from backend.context.analytics.application.dto.analytics_read_models import (
    AnalyticsInsightsResult,
)
from backend.context.analytics.application.orchestration import (
    AnalyticsCommandHandlerContext,
    command_handler_registry,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


@dataclass(frozen=True, kw_only=True)
class ListAnalyticsInsightsCommand(Command):
    user_id: UUID
    scopes: tuple[AnalyticsScope, ...] | None = None
    statuses: tuple[AnalyticsRecordStatus, ...] | None = (
        AnalyticsRecordStatus.ACTIVE,
    )
    stability: AnalyticsStability | None = None
    min_confidence: float | None = None
    min_importance: float | None = None
    tags: tuple[str, ...] | None = None
    include_observations: bool = False
    limit: int | None = None


@command_handler_registry.handler(ListAnalyticsInsightsCommand)
class ListAnalyticsInsightsCommandHandler(AbstractCommandHandler):
    async def __call__(
        self,
        command: ListAnalyticsInsightsCommand,
        context: AnalyticsCommandHandlerContext,
    ) -> AnalyticsInsightsResult:
        return await context.uow.analytics_reader.list_insights(
            user_id=command.user_id,
            scopes=command.scopes,
            statuses=command.statuses,
            stability=command.stability,
            min_confidence=command.min_confidence,
            min_importance=command.min_importance,
            tags=command.tags,
            include_observations=command.include_observations,
            limit=command.limit,
        )
