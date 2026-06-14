from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from direttore import ModularMonolithExecutionRuntime

# backend/context/runtime/adapters/schedule_runtime_adapter.py

from backend.context.runtime.application.ports.schedule_runtime_port import (
    MorningDayMessageResult,
    MorningDayMessageStatus,
    RuntimeReminderReadModel,
    ScheduleRuntimePort,
)
from backend.context.schedule.adapters.inbound.in_process_facade import (
    ScheduleInProcessFacade,
)


class InProcessScheduleRuntimeAdapter(ScheduleRuntimePort):
    def __init__(
        self,
        runtime: ModularMonolithExecutionRuntime,
    ) -> None:
        self._schedule_facade = ScheduleInProcessFacade(runtime)

    async def list_active_future_reminders(
        self,
        *,
        now_utc: datetime,
    ) -> list[RuntimeReminderReadModel]:
        reminders = await self._schedule_facade.list_active_future_reminders(
            now_utc=now_utc,
        )

        return [
            RuntimeReminderReadModel(
                id=reminder.id,
                user_id=reminder.user_id,
                remind_at=reminder.remind_at,
                text=reminder.text,
            )
            for reminder in reminders
        ]

    async def expire_reminder(
        self,
        *,
        reminder_id: UUID,
    ) -> None:
        await self._schedule_facade.expire_reminder(
            reminder_id=reminder_id,
        )

    async def schedule_day_exists(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> bool:
        return await self._schedule_facade.schedule_day_exists(
            user_id=user_id,
            day=day,
        )

    async def build_morning_day_message(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> MorningDayMessageResult:
        result = await self._schedule_facade.build_morning_day_message(
            user_id=user_id,
            day=day,
        )

        return MorningDayMessageResult(
            status=MorningDayMessageStatus(result.status),
            text=result.text,
            reason=result.reason,
        )