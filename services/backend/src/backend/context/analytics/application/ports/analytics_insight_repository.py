from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope


class AnalyticsInsightRepository(Protocol):
    async def add(self, insight: AnalyticsInsight) -> None:
        raise NotImplementedError

    async def get_by_id(self, insight_id: UUID) -> AnalyticsInsight | None:
        raise NotImplementedError

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None = None,
        min_confidence: float | None = None,
        limit: int | None = None,
    ) -> tuple[AnalyticsInsight, ...]:
        raise NotImplementedError

    async def save(self, insight: AnalyticsInsight) -> None:
        raise NotImplementedError
