from __future__ import annotations

from typing import Protocol
from uuid import UUID


class ReminderNotificationPort(Protocol):
    async def send_reminder(
        self,
        *,
        user_id: UUID,
        text: str,
    ) -> None:
        raise NotImplementedError