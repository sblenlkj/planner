from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.analytics.application.dto.analytics_read_models import (
    AnalyticsInsightsResult,
    AnalyticsObservationsResult,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


class AnalyticsReadRepository(Protocol):
    async def list_observations(
        self,
        *,
        user_id: UUID,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None = None,
        stability: AnalyticsStability | None = None,
        min_confidence: float | None = None,
        min_importance: float | None = None,
        tags: tuple[str, ...] | None = None,
        limit: int | None = None,
    ) -> AnalyticsObservationsResult:
        raise NotImplementedError

    async def list_insights(
        self,
        *,
        user_id: UUID,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None = None,
        stability: AnalyticsStability | None = None,
        min_confidence: float | None = None,
        min_importance: float | None = None,
        tags: tuple[str, ...] | None = None,
        include_observations: bool = False,
        limit: int | None = None,
    ) -> AnalyticsInsightsResult:
        raise NotImplementedError
