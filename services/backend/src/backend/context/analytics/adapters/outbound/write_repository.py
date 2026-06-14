from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update as update_sql
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.analytics.adapters.outbound.models import (
    AnalyticsInsightRow,
    AnalyticsObservationRow,
)
from backend.context.analytics.application.ports.analytics_write_repository import (
    AnalyticsWriteRepository,
)
from backend.context.analytics.domain.entities.analytics_insight import AnalyticsInsight
from backend.context.analytics.domain.entities.analytics_observation import (
    AnalyticsObservation,
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


class SqlAlchemyAnalyticsWriteRepository(AnalyticsWriteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_observation(
        self,
        *,
        observation: AnalyticsObservation,
    ) -> None:
        self._session.add(self._to_observation_row(observation))

    async def get_observation_by_id(
        self,
        observation_id: UUID,
    ) -> AnalyticsObservation | None:
        result = await self._session.execute(
            select(AnalyticsObservationRow).where(
                AnalyticsObservationRow.id == observation_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_observation(row)

    async def update_observation(
        self,
        *,
        observation: AnalyticsObservation,
    ) -> None:
        await self._session.execute(
            update_sql(AnalyticsObservationRow)
            .where(AnalyticsObservationRow.id == observation.id)
            .values(
                user_id=observation.user_id,
                scope=observation.scope.value,
                description=observation.description,
                evidence=observation.evidence,
                confidence=observation.confidence,
                importance=observation.importance,
                stability=observation.stability.value,
                status=observation.status.value,
                tags=list(observation.tags),
                valid_until=observation.valid_until,
                source=observation.source.value,
                source_id=observation.source_id,
                observed_at=observation.observed_at,
            )
        )

    async def add_insight(
        self,
        *,
        insight: AnalyticsInsight,
    ) -> None:
        self._session.add(self._to_insight_row(insight))

    async def get_insight_by_id(
        self,
        insight_id: UUID,
    ) -> AnalyticsInsight | None:
        result = await self._session.execute(
            select(AnalyticsInsightRow).where(
                AnalyticsInsightRow.id == insight_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_insight(row)

    async def update_insight(
        self,
        *,
        insight: AnalyticsInsight,
    ) -> None:
        await self._session.execute(
            update_sql(AnalyticsInsightRow)
            .where(AnalyticsInsightRow.id == insight.id)
            .values(
                user_id=insight.user_id,
                scope=insight.scope.value,
                description=insight.description,
                evidence=insight.evidence,
                confidence=insight.confidence,
                importance=insight.importance,
                stability=insight.stability.value,
                status=insight.status.value,
                tags=list(insight.tags),
                valid_until=insight.valid_until,
                source_observation_ids=[
                    str(observation_id)
                    for observation_id in insight.source_observation_ids
                ],
                derived_at=insight.derived_at,
                replaced_by=insight.replaced_by,
            )
        )

    @staticmethod
    def _to_observation(row: AnalyticsObservationRow) -> AnalyticsObservation:
        return AnalyticsObservation(
            id=row.id,
            user_id=row.user_id,
            scope=AnalyticsScope(row.scope),
            description=row.description,
            evidence=row.evidence,
            confidence=row.confidence,
            importance=row.importance,
            stability=AnalyticsStability(row.stability),
            status=AnalyticsRecordStatus(row.status),
            tags=tuple(row.tags),
            valid_until=row.valid_until,
            source=AnalyticsObservationSource(row.source),
            source_id=row.source_id,
            observed_at=row.observed_at,
        )

    @staticmethod
    def _to_insight(row: AnalyticsInsightRow) -> AnalyticsInsight:
        return AnalyticsInsight(
            id=row.id,
            user_id=row.user_id,
            scope=AnalyticsScope(row.scope),
            description=row.description,
            evidence=row.evidence,
            confidence=row.confidence,
            importance=row.importance,
            stability=AnalyticsStability(row.stability),
            status=AnalyticsRecordStatus(row.status),
            tags=tuple(row.tags),
            valid_until=row.valid_until,
            source_observation_ids=tuple(
                UUID(str(observation_id))
                for observation_id in row.source_observation_ids
            ),
            derived_at=row.derived_at,
            replaced_by=row.replaced_by,
        )

    @staticmethod
    def _to_observation_row(
        observation: AnalyticsObservation,
    ) -> AnalyticsObservationRow:
        return AnalyticsObservationRow(
            id=observation.id,
            user_id=observation.user_id,
            scope=observation.scope.value,
            description=observation.description,
            evidence=observation.evidence,
            confidence=observation.confidence,
            importance=observation.importance,
            stability=observation.stability.value,
            status=observation.status.value,
            tags=list(observation.tags),
            valid_until=observation.valid_until,
            source=observation.source.value,
            source_id=observation.source_id,
            observed_at=observation.observed_at,
        )

    @staticmethod
    def _to_insight_row(insight: AnalyticsInsight) -> AnalyticsInsightRow:
        return AnalyticsInsightRow(
            id=insight.id,
            user_id=insight.user_id,
            scope=insight.scope.value,
            description=insight.description,
            evidence=insight.evidence,
            confidence=insight.confidence,
            importance=insight.importance,
            stability=insight.stability.value,
            status=insight.status.value,
            tags=list(insight.tags),
            valid_until=insight.valid_until,
            source_observation_ids=[
                str(observation_id)
                for observation_id in insight.source_observation_ids
            ],
            derived_at=insight.derived_at,
            replaced_by=insight.replaced_by,
        )
