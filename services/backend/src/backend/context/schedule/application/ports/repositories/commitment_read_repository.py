from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.entities.reminder import Reminder
from backend.context.schedule.domain.commitment.value_objects.commitment_status import (
    CommitmentStatus,
)


class CommitmentReadRepository(Protocol):
    async def get_reminder_by_id(self, reminder_id: UUID) -> Reminder | None:
        raise NotImplementedError

    async def get_deadline_by_id(self, deadline_id: UUID) -> Deadline | None:
        raise NotImplementedError

    async def list_reminders(
        self,
        user_id: UUID,
        status: CommitmentStatus | None = None,
    ) -> list[Reminder]:
        raise NotImplementedError

    async def list_deadlines(
        self,
        user_id: UUID,
        status: CommitmentStatus | None = None,
    ) -> list[Deadline]:
        raise NotImplementedError

    async def list_active_future_reminders(
        self,
        now_utc: datetime,
    ) -> list[Reminder]:
        raise NotImplementedError