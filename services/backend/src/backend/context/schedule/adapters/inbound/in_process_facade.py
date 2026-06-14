from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from direttore import ModularMonolithExecutionRuntime

from backend.context.schedule.application.queries.list_active_future_reminders import (
    ActiveFutureReminderReadModel,
    ListActiveFutureRemindersQuery,
    ListActiveFutureRemindersQueryResult,
)
from backend.context.schedule.application.use_cases.commitment.expire_reminder import (
    ExpireReminderCommand,
    ExpireReminderCommandResult,
)
from datetime import date

from backend.context.schedule.application.queries import (
    BuildMorningDayMessageQuery,
    BuildMorningDayMessageQueryResult,
    ScheduleDayExistsQuery,
    ScheduleDayExistsQueryResult,
    ScheduleMorningDayMessageStatus,
)

@dataclass(frozen=True, slots=True)
class MorningDayMessageResult:
    status: ScheduleMorningDayMessageStatus
    text: str | None = None
    reason: str | None = None

@dataclass(frozen=True, slots=True)
class ActiveFutureReminderResult:
    id: UUID
    user_id: UUID
    remind_at: datetime
    text: str


class ScheduleInProcessFacade:
    def __init__(
        self,
        runtime: ModularMonolithExecutionRuntime,
    ) -> None:
        self._runtime = runtime

    async def list_active_future_reminders(
        self,
        *,
        now_utc: datetime,
    ) -> list[ActiveFutureReminderResult]:
        result = await self._runtime.invoke_query(
            ListActiveFutureRemindersQuery(
                now_utc=now_utc,
            )
        )

        if not isinstance(result, ListActiveFutureRemindersQueryResult):
            raise TypeError(
                "ListActiveFutureRemindersQuery returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )

        return [
            self._map_active_future_reminder(reminder)
            for reminder in result.reminders
        ]

    async def expire_reminder(
        self,
        *,
        reminder_id: UUID,
    ) -> None:
        result = await self._runtime.invoke(
            ExpireReminderCommand(
                reminder_id=reminder_id,
            )
        )

        if not isinstance(result, ExpireReminderCommandResult):
            raise TypeError(
                "ExpireReminderCommand returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )
        

    async def schedule_day_exists(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> bool:
        result = await self._runtime.invoke_query(
            ScheduleDayExistsQuery(
                user_id=user_id,
                day=day,
            )
        )

        if not isinstance(result, ScheduleDayExistsQueryResult):
            raise TypeError(
                "ScheduleDayExistsQuery returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )

        return result.exists

    async def build_morning_day_message(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> MorningDayMessageResult:
        result = await self._runtime.invoke_query(
            BuildMorningDayMessageQuery(
                user_id=user_id,
                day=day,
            )
        )

        if not isinstance(result, BuildMorningDayMessageQueryResult):
            raise TypeError(
                "BuildMorningDayMessageQuery returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )

        return MorningDayMessageResult(
            status=result.status,
            text=result.text,
            reason=result.reason,
        )

    @staticmethod
    def _map_active_future_reminder(
        reminder: ActiveFutureReminderReadModel,
    ) -> ActiveFutureReminderResult:
        return ActiveFutureReminderResult(
            id=reminder.id,
            user_id=reminder.user_id,
            remind_at=reminder.remind_at,
            text=reminder.text,
        )