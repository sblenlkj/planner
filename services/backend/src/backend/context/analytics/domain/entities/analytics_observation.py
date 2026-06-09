from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from backend.context.analytics.domain.entities.analytics_record import AnalyticsRecord
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


@dataclass(kw_only=True, slots=True)
class AnalyticsObservation(AnalyticsRecord):
    source: AnalyticsObservationSource
    source_id: str | None
    observed_at: datetime

    def __post_init__(self) -> None:
        AnalyticsRecord.__post_init__(self)

        self._validate_source(self.source)
        self.source_id = self._normalize_optional_text(self.source_id, "source_id")
        self._validate_datetime(self.observed_at, "observed_at")
        self._validate_valid_until_against_observed_at()

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        scope: AnalyticsScope,
        description: str,
        evidence: str | None = None,
        confidence: float,
        importance: float,
        stability: AnalyticsStability,
        tags: tuple[str, ...] = (),
        source: AnalyticsObservationSource = AnalyticsObservationSource.AGENT_OBSERVATION,
        source_id: str | None = None,
        observed_at: datetime,
        valid_until: datetime | None = None,
        id: UUID | None = None,
    ) -> Self:
        return cls(
            id=id or uuid4(),
            user_id=user_id,
            scope=scope,
            description=description,
            evidence=evidence,
            confidence=confidence,
            importance=importance,
            stability=stability,
            status=AnalyticsRecordStatus.ACTIVE,
            tags=tags,
            valid_until=valid_until,
            source=source,
            source_id=source_id,
            observed_at=observed_at,
        )

    def change_source(
        self,
        source: AnalyticsObservationSource,
        source_id: str | None = None,
    ) -> None:
        self._validate_source(source)

        self.source = source
        self.source_id = self._normalize_optional_text(source_id, "source_id")

    def change_source_id(self, source_id: str | None) -> None:
        self.source_id = self._normalize_optional_text(source_id, "source_id")

    def change_observed_at(self, observed_at: datetime) -> None:
        self._validate_datetime(observed_at, "observed_at")

        if self.valid_until is not None and self.valid_until < observed_at:
            raise ValueError("valid_until cannot be earlier than observed_at")

        self.observed_at = observed_at

    def change_valid_until(self, valid_until: datetime | None) -> None:
        self._validate_optional_datetime(valid_until, "valid_until")

        if valid_until is not None and valid_until < self.observed_at:
            raise ValueError("valid_until cannot be earlier than observed_at")

        self.valid_until = valid_until

    @staticmethod
    def _validate_source(value: AnalyticsObservationSource) -> None:
        if not isinstance(value, AnalyticsObservationSource):
            raise TypeError("source must be AnalyticsObservationSource")

    def _validate_valid_until_against_observed_at(self) -> None:
        if self.valid_until is not None and self.valid_until < self.observed_at:
            raise ValueError("valid_until cannot be earlier than observed_at")