from __future__ import annotations

from dataclasses import dataclass

from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.entities.analytics_observation import (
    AnalyticsObservation,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsContextDto:
    insights: tuple[AnalyticsInsight, ...]
    observations: tuple[AnalyticsObservation, ...]