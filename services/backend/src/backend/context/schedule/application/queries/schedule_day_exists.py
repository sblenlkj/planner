from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


@dataclass(frozen=True, kw_only=True)
class ScheduleDayExistsQuery(Query):
    user_id: UUID
    day: date


@dataclass(frozen=True, kw_only=True)
class ScheduleDayExistsQueryResult:
    exists: bool


@query_handler_registry.handler(ScheduleDayExistsQuery)
class ScheduleDayExistsQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: ScheduleDayExistsQuery,
        context: ScheduleQueryHandlerContext,
    ) -> ScheduleDayExistsQueryResult:
        schedule_day = (
            await context.uow.execution_reader.get_schedule_day_by_user_id_and_date(
                user_id=query.user_id,
                date=self._to_schedule_date(query.day),
            )
        )

        return ScheduleDayExistsQueryResult(
            exists=schedule_day is not None,
        )

    @staticmethod
    def _to_schedule_date(day: date) -> ScheduleDate:
        return ScheduleDate(
            year=day.year,
            month=day.month,
            day=day.day,
        )