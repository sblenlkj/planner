from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.analytics.adapters.outbound.models import (
    AnalyticsInsightRow,
    AnalyticsObservationRow,
)
from backend.context.analytics.application.dto.analytics_read_models import (
    AnalyticsInsightDetails,
    AnalyticsInsightsResult,
    AnalyticsObservationDetails,
    AnalyticsObservationsResult,
)
from backend.context.analytics.application.ports.analytics_read_repository import (
    AnalyticsReadRepository,
)
from backend.context.analytics.domain.value_objects.analytics_record_status import (
    AnalyticsRecordStatus,
)
from backend.context.analytics.domain.value_objects.analytics_scope import AnalyticsScope
from backend.context.analytics.domain.value_objects.analytics_stability import (
    AnalyticsStability,
)


class SqlAlchemyAnalyticsReadRepository(AnalyticsReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_observations(
        self,
        *,
        user_id: UUID,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None = None,
        stability: AnalyticsStability | None = None,
        min_confidence: float | None = None,
        min_importance: float | None = None,
        tags: tuple[str, ...] | None = None,
        limit: int | None = None,
    ) -> AnalyticsObservationsResult:
        statement = select(AnalyticsObservationRow).where(
            AnalyticsObservationRow.user_id == user_id,
        )

        statement = self._apply_record_filters(
            statement=statement,
            row_type=AnalyticsObservationRow,
            scopes=scopes,
            statuses=statuses,
            stability=stability,
            min_confidence=min_confidence,
            min_importance=min_importance,
        ).order_by(AnalyticsObservationRow.observed_at.desc())

        result = await self._session.execute(statement)
        rows = list(result.scalars().all())

        rows = self._filter_rows_by_tags(rows=rows, tags=tags)

        if limit is not None:
            rows = rows[:limit]

        return AnalyticsObservationsResult(
            observations=[
                self._to_observation_details(row)
                for row in rows
            ],
        )

    async def list_insights(
        self,
        *,
        user_id: UUID,
        scopes: tuple[AnalyticsScope, ...] | None = None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None = None,
        stability: AnalyticsStability | None = None,
        min_confidence: float | None = None,
        min_importance: float | None = None,
        tags: tuple[str, ...] | None = None,
        include_observations: bool = False,
        limit: int | None = None,
    ) -> AnalyticsInsightsResult:
        statement = select(AnalyticsInsightRow).where(
            AnalyticsInsightRow.user_id == user_id,
        )

        statement = self._apply_record_filters(
            statement=statement,
            row_type=AnalyticsInsightRow,
            scopes=scopes,
            statuses=statuses,
            stability=stability,
            min_confidence=min_confidence,
            min_importance=min_importance,
        ).order_by(AnalyticsInsightRow.derived_at.desc())

        result = await self._session.execute(statement)
        rows = list(result.scalars().all())

        rows = self._filter_rows_by_tags(rows=rows, tags=tags)

        if limit is not None:
            rows = rows[:limit]

        observations: list[AnalyticsObservationDetails] | None = None

        if include_observations:
            observations = await self._list_source_observations_for_insights(rows)

        return AnalyticsInsightsResult(
            insights=[
                self._to_insight_details(row)
                for row in rows
            ],
            observations=observations,
        )

    async def _list_source_observations_for_insights(
        self,
        insight_rows: list[AnalyticsInsightRow],
    ) -> list[AnalyticsObservationDetails]:
        observation_ids: list[UUID] = []

        for row in insight_rows:
            for raw_observation_id in row.source_observation_ids:
                observation_id = UUID(str(raw_observation_id))

                if observation_id not in observation_ids:
                    observation_ids.append(observation_id)

        if not observation_ids:
            return []

        result = await self._session.execute(
            select(AnalyticsObservationRow).where(
                AnalyticsObservationRow.id.in_(observation_ids),
            )
        )
        rows = result.scalars().all()

        return [
            self._to_observation_details(row)
            for row in rows
        ]

    @staticmethod
    def _apply_record_filters(
        *,
        statement,
        row_type,
        scopes: tuple[AnalyticsScope, ...] | None,
        statuses: tuple[AnalyticsRecordStatus, ...] | None,
        stability: AnalyticsStability | None,
        min_confidence: float | None,
        min_importance: float | None,
    ):
        if scopes is not None:
            statement = statement.where(
                row_type.scope.in_([scope.value for scope in scopes]),
            )

        if statuses is not None:
            statement = statement.where(
                row_type.status.in_([status.value for status in statuses]),
            )

        if stability is not None:
            statement = statement.where(row_type.stability == stability.value)

        if min_confidence is not None:
            statement = statement.where(row_type.confidence >= min_confidence)

        if min_importance is not None:
            statement = statement.where(row_type.importance >= min_importance)

        return statement

    @staticmethod
    def _filter_rows_by_tags(
        *,
        rows,
        tags: tuple[str, ...] | None,
    ):
        if tags is None:
            return rows

        normalized_tags = {
            tag.strip().lower()
            for tag in tags
            if tag.strip()
        }

        if not normalized_tags:
            return rows

        return [
            row
            for row in rows
            if normalized_tags.intersection(
                {
                    tag.strip().lower()
                    for tag in row.tags
                }
            )
        ]

    @staticmethod
    def _to_observation_details(
        row: AnalyticsObservationRow,
    ) -> AnalyticsObservationDetails:
        return AnalyticsObservationDetails(
            id=row.id,
            user_id=row.user_id,
            scope=row.scope,
            description=row.description,
            evidence=row.evidence,
            confidence=row.confidence,
            importance=row.importance,
            stability=row.stability,
            status=row.status,
            tags=tuple(row.tags),
            valid_until=row.valid_until,
            source=row.source,
            source_id=row.source_id,
            observed_at=row.observed_at,
        )

    @staticmethod
    def _to_insight_details(row: AnalyticsInsightRow) -> AnalyticsInsightDetails:
        return AnalyticsInsightDetails(
            id=row.id,
            user_id=row.user_id,
            scope=row.scope,
            description=row.description,
            evidence=row.evidence,
            confidence=row.confidence,
            importance=row.importance,
            stability=row.stability,
            status=row.status,
            tags=tuple(row.tags),
            valid_until=row.valid_until,
            source_observation_ids=tuple(
                UUID(str(observation_id))
                for observation_id in row.source_observation_ids
            ),
            derived_at=row.derived_at,
            replaced_by=row.replaced_by,
        )
