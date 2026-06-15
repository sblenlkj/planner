from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


@dataclass(frozen=True, kw_only=True)
class ScheduleDateObservationReadModel:
    id: UUID
    user_id: UUID
    starts_on: ScheduleDate
    ends_on: ScheduleDate | None
    description: str


@dataclass(frozen=True, kw_only=True)
class ListScheduleDateObservationsQuery(Query):
    user_id: UUID
    date: ScheduleDate


@dataclass(frozen=True, kw_only=True)
class ListScheduleDateObservationsQueryResult:
    observations: list[ScheduleDateObservationReadModel]


@query_handler_registry.handler(ListScheduleDateObservationsQuery)
class ListScheduleDateObservationsQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: ListScheduleDateObservationsQuery,
        context: ScheduleQueryHandlerContext,
    ) -> ListScheduleDateObservationsQueryResult:
        observations = await context.uow.execution_reader.list_schedule_date_observations(
            user_id=query.user_id,
            date=query.date,
        )

        return ListScheduleDateObservationsQueryResult(
            observations=[
                ScheduleDateObservationReadModel(
                    id=observation.id,
                    user_id=observation.user_id,
                    starts_on=observation.starts_on,
                    ends_on=observation.ends_on,
                    description=observation.description,
                )
                for observation in observations
            ],
        )