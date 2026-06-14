from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from direttore import AbstractQueryHandler, Query

from backend.context.schedule.application.orchestration import (
    ScheduleQueryHandlerContext,
    query_handler_registry,
)
from backend.context.schedule.application.reminder_runtime import (
    build_reminder_text,
)
from backend.context.schedule.domain.commitment.entities.reminder import Reminder


@dataclass(frozen=True, kw_only=True)
class ActiveFutureReminderReadModel:
    id: UUID
    user_id: UUID
    remind_at: datetime
    text: str


@dataclass(frozen=True, kw_only=True)
class ListActiveFutureRemindersQuery(Query):
    now_utc: datetime


@dataclass(frozen=True, kw_only=True)
class ListActiveFutureRemindersQueryResult:
    reminders: list[ActiveFutureReminderReadModel]


@query_handler_registry.handler(ListActiveFutureRemindersQuery)
class ListActiveFutureRemindersQueryHandler(AbstractQueryHandler):
    async def __call__(
        self,
        query: ListActiveFutureRemindersQuery,
        context: ScheduleQueryHandlerContext,
    ) -> ListActiveFutureRemindersQueryResult:
        self._validate_utc_datetime(query.now_utc)

        reminders = await context.uow.commitment_reader.list_active_future_reminders(
            now_utc=query.now_utc,
        )

        return ListActiveFutureRemindersQueryResult(
            reminders=[
                self._map_reminder(reminder)
                for reminder in reminders
            ],
        )

    @staticmethod
    def _map_reminder(reminder: Reminder) -> ActiveFutureReminderReadModel:
        return ActiveFutureReminderReadModel(
            id=reminder.id,
            user_id=reminder.user_id,
            remind_at=reminder.remind_at,
            text=build_reminder_text(reminder),
        )

    @staticmethod
    def _validate_utc_datetime(value: datetime) -> None:
        if value.tzinfo is None:
            return

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("now_utc must be UTC datetime or naive UTC datetime")