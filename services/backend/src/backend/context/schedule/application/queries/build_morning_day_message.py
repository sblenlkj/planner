from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.domain.execution.entities.schedule_day import ScheduleDay
from backend.context.schedule.domain.execution.entities.scheduled_activity import (
    ScheduledActivity,
)
from backend.context.schedule.domain.shared.schedule_date import ScheduleDate


class ScheduleMorningDayMessageStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    ERROR = "error"


@dataclass(frozen=True, kw_only=True)
class BuildMorningDayMessageQuery(Query):
    user_id: UUID
    day: date


@dataclass(frozen=True, kw_only=True)
class BuildMorningDayMessageQueryResult:
    status: ScheduleMorningDayMessageStatus
    text: str | None = None
    reason: str | None = None


@query_handler_registry.handler(BuildMorningDayMessageQuery)
class BuildMorningDayMessageQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: BuildMorningDayMessageQuery,
        context: ScheduleQueryHandlerContext,
    ) -> BuildMorningDayMessageQueryResult:
        schedule_day = (
            await context.uow.execution_reader.get_schedule_day_by_user_id_and_date(
                user_id=query.user_id,
                date=self._to_schedule_date(query.day),
            )
        )

        if schedule_day is None:
            return BuildMorningDayMessageQueryResult(
                status=ScheduleMorningDayMessageStatus.NOT_READY,
                reason="schedule day not found",
            )

        return BuildMorningDayMessageQueryResult(
            status=ScheduleMorningDayMessageStatus.READY,
            text=self._build_message(schedule_day),
        )

    @staticmethod
    def _to_schedule_date(day: date) -> ScheduleDate:
        return ScheduleDate(
            year=day.year,
            month=day.month,
            day=day.day,
        )

    @classmethod
    def _build_message(cls, schedule_day: ScheduleDay) -> str:
        parts = [
            f"Доброе утро! План на сегодня: {schedule_day.title}",
            "",
            schedule_day.description,
        ]

        if schedule_day.activities:
            parts.extend(
                [
                    "",
                    "Задачи на день:",
                    *[
                        cls._format_activity(activity)
                        for activity in schedule_day.activities
                    ],
                ]
            )

        return "\n".join(parts)

    @staticmethod
    def _format_activity(activity: ScheduledActivity) -> str:
        base = (
            f"- {activity.start_time}-{activity.end_time}: "
            f"{activity.title}"
        )

        if activity.description is None or not activity.description.strip():
            return base

        return f"{base}. {activity.description}"