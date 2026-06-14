from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.entities.analytics_observation import (
    AnalyticsObservation,
)


class AnalyticsWriteRepository(Protocol):
    async def add_observation(
        self,
        observation: AnalyticsObservation,
    ) -> None:
        raise NotImplementedError

    async def get_observation_by_id(
        self,
        observation_id: UUID,
    ) -> AnalyticsObservation | None:
        raise NotImplementedError

    async def update_observation(
        self,
        observation: AnalyticsObservation,
    ) -> None:
        raise NotImplementedError

    async def add_insight(
        self,
        insight: AnalyticsInsight,
    ) -> None:
        raise NotImplementedError

    async def get_insight_by_id(
        self,
        insight_id: UUID,
    ) -> AnalyticsInsight | None:
        raise NotImplementedError

    async def update_insight(
        self,
        insight: AnalyticsInsight,
    ) -> None:
        raise NotImplementedError
