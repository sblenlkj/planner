from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.schedule.domain.commitment.entities.deadline import Deadline
from backend.context.schedule.domain.commitment.entities.reminder import Reminder


class CommitmentWriteRepository(Protocol):
    async def add_reminder(self, reminder: Reminder) -> None:
        raise NotImplementedError

    async def get_reminder_by_id(self, reminder_id: UUID) -> Reminder | None:
        raise NotImplementedError

    async def update_reminder(self, reminder: Reminder) -> None:
        raise NotImplementedError

    async def add_deadline(self, deadline: Deadline) -> None:
        raise NotImplementedError

    async def get_deadline_by_id(self, deadline_id: UUID) -> Deadline | None:
        raise NotImplementedError

    async def update_deadline(self, deadline: Deadline) -> None:
        raise NotImplementedError