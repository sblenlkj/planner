from __future__ import annotations

from uuid import UUID

from backend.context.analytics.application.dto.analytics_context_dto import (
    AnalyticsContextDto,
)

from backend.context.analytics.application.ports.analytics_unit_of_work import (
    AnalyticsUnitOfWork,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope


class AnalyticsContextService:
    def __init__(self, unit_of_work: AnalyticsUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def build_context(
        self,
        *,
        user_id: UUID,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        min_confidence: float | None = None,
        insight_limit: int | None = None,
        observation_limit: int | None = None,
    ) -> AnalyticsContextDto:
        self._validate_user_id(user_id)
        self._validate_optional_scopes(scopes)
        self._validate_optional_min_confidence(min_confidence)
        self._validate_optional_limit(insight_limit, "insight_limit")
        self._validate_optional_limit(observation_limit, "observation_limit")

        insights = await self._unit_of_work.insights.list_by_user(
            user_id,
            scopes=scopes,
            statuses=(AnalyticsRecordStatus.ACTIVE,),
            min_confidence=min_confidence,
            limit=insight_limit,
        )
        observations = await self._unit_of_work.observations.list_by_user(
            user_id,
            scopes=scopes,
            statuses=(AnalyticsRecordStatus.ACTIVE,),
            min_confidence=min_confidence,
            limit=observation_limit,
        )

        return AnalyticsContextDto(
            insights=insights,
            observations=observations,
        )

    @staticmethod
    def _validate_user_id(user_id: UUID) -> None:
        if not isinstance(user_id, UUID):
            raise TypeError("user_id must be UUID")

    @staticmethod
    def _validate_optional_scopes(scopes: tuple[AnalyticsScope, ...] | None) -> None:
        if scopes is None:
            return

        if not isinstance(scopes, tuple):
            raise TypeError("scopes must be tuple[AnalyticsScope, ...] or None")

        for scope in scopes:
            if not isinstance(scope, AnalyticsScope):
                raise TypeError("each scope must be AnalyticsScope")

    @staticmethod
    def _validate_optional_min_confidence(min_confidence: float | None) -> None:
        if min_confidence is None:
            return

        if not isinstance(min_confidence, int | float):
            raise TypeError("min_confidence must be number or None")

        if not 0.0 <= float(min_confidence) <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0")

    @staticmethod
    def _validate_optional_limit(limit: int | None, field_name: str) -> None:
        if limit is None:
            return

        if not isinstance(limit, int):
            raise TypeError(f"{field_name} must be int or None")

        if limit <= 0:
            raise ValueError(f"{field_name} must be positive")
