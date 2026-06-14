from __future__ import annotations

from typing import Protocol
from uuid import UUID


class UserUtcOffsetPort(Protocol):
    async def get_user_utc_offset_minutes(self, user_id: UUID) -> int:
        raise NotImplementedError