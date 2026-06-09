from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from backend.context.analytics.domain.entities.analytics_record import AnalyticsRecord
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


@dataclass(kw_only=True, slots=True)
class AnalyticsInsight(AnalyticsRecord):
    source_observation_ids: tuple[UUID, ...]
    derived_at: datetime
    replaced_by: UUID | None = None

    def __post_init__(self) -> None:
        AnalyticsRecord.__post_init__(self)

        self.source_observation_ids = self._normalize_source_observation_ids(
            self.source_observation_ids
        )
        self._validate_datetime(self.derived_at, "derived_at")
        self._validate_optional_id(self.replaced_by, "replaced_by")
        self._validate_valid_until_against_derived_at()
        self._validate_replacement_state()

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        scope: AnalyticsScope,
        description: str,
        evidence: str | None = None,
        source_observation_ids: tuple[UUID, ...],
        confidence: float,
        importance: float,
        stability: AnalyticsStability,
        tags: tuple[str, ...] = (),
        derived_at: datetime,
        valid_until: datetime | None = None,
        id: UUID | None = None,
    ) -> Self:
        return cls(
            id=id or uuid4(),
            user_id=user_id,
            scope=scope,
            description=description,
            evidence=evidence,
            source_observation_ids=source_observation_ids,
            confidence=confidence,
            importance=importance,
            stability=stability,
            status=AnalyticsRecordStatus.ACTIVE,
            tags=tags,
            valid_until=valid_until,
            derived_at=derived_at,
            replaced_by=None,
        )

    def replace_source_observations(
        self,
        source_observation_ids: tuple[UUID, ...],
    ) -> None:
        self.source_observation_ids = self._normalize_source_observation_ids(
            source_observation_ids
        )

    def add_source_observation(self, observation_id: UUID) -> None:
        self._validate_id(observation_id, "observation_id")

        if observation_id in self.source_observation_ids:
            return

        self.source_observation_ids = (*self.source_observation_ids, observation_id)

    def remove_source_observation(self, observation_id: UUID) -> None:
        self._validate_id(observation_id, "observation_id")

        self.source_observation_ids = tuple(
            existing_observation_id
            for existing_observation_id in self.source_observation_ids
            if existing_observation_id != observation_id
        )

    def change_derived_at(self, derived_at: datetime) -> None:
        self._validate_datetime(derived_at, "derived_at")

        if self.valid_until is not None and self.valid_until < derived_at:
            raise ValueError("valid_until cannot be earlier than derived_at")

        self.derived_at = derived_at

    def change_valid_until(self, valid_until: datetime | None) -> None:
        self._validate_optional_datetime(valid_until, "valid_until")

        if valid_until is not None and valid_until < self.derived_at:
            raise ValueError("valid_until cannot be earlier than derived_at")

        self.valid_until = valid_until

    def supersede_by(self, new_insight_id: UUID) -> None:
        self._validate_id(new_insight_id, "new_insight_id")

        if new_insight_id == self.id:
            raise ValueError("insight cannot be superseded by itself")

        if self.status != AnalyticsRecordStatus.ACTIVE:
            raise ValueError("only active insight can be superseded")

        self.status = AnalyticsRecordStatus.SUPERSEDED
        self.replaced_by = new_insight_id

    def reject(self) -> None:
        AnalyticsRecord.reject(self)
        self.replaced_by = None

    def expire(self) -> None:
        AnalyticsRecord.expire(self)
        self.replaced_by = None

    def activate(self) -> None:
        AnalyticsRecord.activate(self)
        self.replaced_by = None

    @classmethod
    def _validate_optional_id(cls, value: UUID | None, field_name: str) -> None:
        if value is None:
            return

        cls._validate_id(value, field_name)

    @classmethod
    def _normalize_source_observation_ids(
        cls,
        source_observation_ids: tuple[UUID, ...],
    ) -> tuple[UUID, ...]:
        if not isinstance(source_observation_ids, tuple):
            raise TypeError("source_observation_ids must be tuple[UUID, ...]")

        normalized_ids: list[UUID] = []

        for observation_id in source_observation_ids:
            cls._validate_id(observation_id, "source_observation_id")

            if observation_id not in normalized_ids:
                normalized_ids.append(observation_id)

        return tuple(normalized_ids)

    def _validate_valid_until_against_derived_at(self) -> None:
        if self.valid_until is not None and self.valid_until < self.derived_at:
            raise ValueError("valid_until cannot be earlier than derived_at")

    def _validate_replacement_state(self) -> None:
        if self.replaced_by is not None and self.replaced_by == self.id:
            raise ValueError("insight cannot be replaced by itself")

        if self.status == AnalyticsRecordStatus.SUPERSEDED and self.replaced_by is None:
            raise ValueError("superseded insight must have replaced_by")

        if self.status != AnalyticsRecordStatus.SUPERSEDED and self.replaced_by is not None:
            raise ValueError("only superseded insight can have replaced_by")