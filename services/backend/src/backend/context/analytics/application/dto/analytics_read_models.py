from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsObservationDetails:
    id: UUID
    user_id: UUID

    scope: str
    description: str
    evidence: str | None

    confidence: float
    importance: float
    stability: str
    status: str

    tags: tuple[str, ...]

    valid_until: datetime | None

    source: str
    source_id: str | None
    observed_at: datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsInsightDetails:
    id: UUID
    user_id: UUID

    scope: str
    description: str
    evidence: str | None

    confidence: float
    importance: float
    stability: str
    status: str

    tags: tuple[str, ...]

    valid_until: datetime | None

    source_observation_ids: tuple[UUID, ...]
    derived_at: datetime
    replaced_by: UUID | None


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsObservationsResult:
    observations: list[AnalyticsObservationDetails]


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsInsightsResult:
    insights: list[AnalyticsInsightDetails]
    observations: list[AnalyticsObservationDetails] | None = None
