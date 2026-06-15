from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agent.application.dto import UserProfileDto


class UserContextPort(Protocol):
    async def get_user_profile(self, user_id: UUID) -> UserProfileDto: ...

    async def update_user_profile(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        language: str | None = None,
        utc_offset_minutes: int | None = None,
        region: str | None = None,
    ) -> UserProfileDto: ...
