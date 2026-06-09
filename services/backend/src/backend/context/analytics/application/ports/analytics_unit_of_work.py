from __future__ import annotations

from typing import Protocol

from backend.context.analytics.application.ports.analytics_insight_repository import (
    AnalyticsInsightRepository,
)
from backend.context.analytics.application.ports.analytics_observation_repository import (
    AnalyticsObservationRepository,
)


class AnalyticsUnitOfWork(Protocol):
    observations: AnalyticsObservationRepository
    insights: AnalyticsInsightRepository
