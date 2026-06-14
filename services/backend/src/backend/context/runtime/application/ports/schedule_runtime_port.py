from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True, slots=True)
class RuntimeReminderReadModel:
    id: UUID
    user_id: UUID
    remind_at: datetime
    text: str


class MorningDayMessageStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    ERROR = "error"


@dataclass(frozen=True, kw_only=True, slots=True)
class MorningDayMessageResult:
    status: MorningDayMessageStatus
    text: str | None = None
    reason: str | None = None


class ScheduleRuntimePort(Protocol):
    async def list_active_future_reminders(
        self,
        *,
        now_utc: datetime,
    ) -> list[RuntimeReminderReadModel]:
        raise NotImplementedError

    async def expire_reminder(
        self,
        *,
        reminder_id: UUID,
    ) -> None:
        raise NotImplementedError

    async def schedule_day_exists(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> bool:
        raise NotImplementedError

    async def build_morning_day_message(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> MorningDayMessageResult:
        raise NotImplementedError