from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.context.analytics.application.dto.analytics_read_models import (
    AnalyticsObservationDetails,
)
from backend.context.analytics.domain.value_objects.analytics_observation_source import (
    AnalyticsObservationSource,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


class AnalyticsObservationResponse(BaseModel):
    id: UUID
    user_id: UUID

    scope: AnalyticsScope
    description: str
    evidence: str | None

    confidence: float
    importance: float
    stability: AnalyticsStability
    status: AnalyticsRecordStatus

    tags: list[str]

    source: AnalyticsObservationSource
    source_id: str | None

    observed_at: datetime
    valid_until: datetime | None

    @classmethod
    def from_read_model(
        cls,
        item: AnalyticsObservationDetails,
    ) -> "AnalyticsObservationResponse":
        return cls(
            id=item.id,
            user_id=item.user_id,
            scope=AnalyticsScope(item.scope),
            description=item.description,
            evidence=item.evidence,
            confidence=item.confidence,
            importance=item.importance,
            stability=AnalyticsStability(item.stability),
            status=AnalyticsRecordStatus(item.status),
            tags=list(item.tags),
            source=AnalyticsObservationSource(item.source),
            source_id=item.source_id,
            observed_at=item.observed_at,
            valid_until=item.valid_until,
        )


class CreateAnalyticsObservationRequest(BaseModel):
    user_id: UUID
    scope: AnalyticsScope
    description: str = Field(min_length=1)

    evidence: str | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    stability: AnalyticsStability = AnalyticsStability.SHORT_TERM
    tags: list[str] = Field(default_factory=list)

    source: AnalyticsObservationSource = (
        AnalyticsObservationSource.AGENT_OBSERVATION
    )
    source_id: str | None = None

    valid_until: datetime | None = None


class CreateAnalyticsObservationResponse(BaseModel):
    observation_id: UUID


class ListAnalyticsObservationsResponse(BaseModel):
    observations: list[AnalyticsObservationResponse]
