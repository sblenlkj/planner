from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


@dataclass(kw_only=True, slots=True)
class AnalyticsRecord:
    id: UUID
    user_id: UUID

    scope: AnalyticsScope
    description: str
    evidence: str | None

    confidence: float
    importance: float
    stability: AnalyticsStability
    status: AnalyticsRecordStatus

    tags: tuple[str, ...]

    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        self._validate_id(self.id, "id")
        self._validate_id(self.user_id, "user_id")
        self._validate_scope(self.scope)
        self.description = self._normalize_required_text(self.description, "description")
        self.evidence = self._normalize_optional_text(self.evidence, "evidence")
        self._validate_score(self.confidence, "confidence")
        self._validate_score(self.importance, "importance")
        self._validate_stability(self.stability)
        self._validate_status(self.status)
        self.tags = self._normalize_tags(self.tags)
        self._validate_optional_datetime(self.valid_until, "valid_until")

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required_text(description, "description")

    def change_evidence(self, evidence: str | None) -> None:
        self.evidence = self._normalize_optional_text(evidence, "evidence")

    def change_confidence(self, confidence: float) -> None:
        self._validate_score(confidence, "confidence")
        self.confidence = confidence

    def change_importance(self, importance: float) -> None:
        self._validate_score(importance, "importance")
        self.importance = importance

    def change_scores(self, *, confidence: float, importance: float) -> None:
        self._validate_score(confidence, "confidence")
        self._validate_score(importance, "importance")
        self.confidence = confidence
        self.importance = importance

    def change_stability(self, stability: AnalyticsStability) -> None:
        self._validate_stability(stability)
        self.stability = stability

    def replace_tags(self, tags: tuple[str, ...]) -> None:
        self.tags = self._normalize_tags(tags)

    def change_valid_until(self, valid_until: datetime | None) -> None:
        self._validate_optional_datetime(valid_until, "valid_until")
        self.valid_until = valid_until

    def reject(self) -> None:
        if self.status == AnalyticsRecordStatus.SUPERSEDED:
            raise ValueError("superseded analytics record cannot be rejected")

        self.status = AnalyticsRecordStatus.REJECTED

    def expire(self) -> None:
        if self.status == AnalyticsRecordStatus.SUPERSEDED:
            raise ValueError("superseded analytics record cannot be expired")

        self.status = AnalyticsRecordStatus.EXPIRED

    def activate(self) -> None:
        if self.status == AnalyticsRecordStatus.SUPERSEDED:
            raise ValueError("superseded analytics record cannot be activated")

        self.status = AnalyticsRecordStatus.ACTIVE

    @property
    def is_active(self) -> bool:
        return self.status == AnalyticsRecordStatus.ACTIVE

    @staticmethod
    def _validate_id(value: UUID, field_name: str) -> None:
        if not isinstance(value, UUID):
            raise TypeError(f"{field_name} must be UUID")

    @staticmethod
    def _validate_scope(value: AnalyticsScope) -> None:
        if not isinstance(value, AnalyticsScope):
            raise TypeError("scope must be AnalyticsScope")

    @staticmethod
    def _validate_stability(value: AnalyticsStability) -> None:
        if not isinstance(value, AnalyticsStability):
            raise TypeError("stability must be AnalyticsStability")

    @staticmethod
    def _validate_status(value: AnalyticsRecordStatus) -> None:
        if not isinstance(value, AnalyticsRecordStatus):
            raise TypeError("status must be AnalyticsRecordStatus")

    @staticmethod
    def _validate_score(value: float, field_name: str) -> None:
        if not isinstance(value, int | float):
            raise TypeError(f"{field_name} must be number")

        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @staticmethod
    def _validate_datetime(value: datetime, field_name: str) -> None:
        if not isinstance(value, datetime):
            raise TypeError(f"{field_name} must be datetime")

    @classmethod
    def _validate_optional_datetime(
        cls,
        value: datetime | None,
        field_name: str,
    ) -> None:
        if value is None:
            return

        cls._validate_datetime(value, field_name)

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be str")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} is required")

        return normalized

    @staticmethod
    def _normalize_optional_text(value: str | None, field_name: str) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be str or None")

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @staticmethod
    def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(tags, tuple):
            raise TypeError("tags must be tuple[str, ...]")

        normalized_tags: list[str] = []

        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("each tag must be str")

            normalized = tag.strip().lower()

            if not normalized:
                continue

            if normalized not in normalized_tags:
                normalized_tags.append(normalized)

        return tuple(normalized_tags)