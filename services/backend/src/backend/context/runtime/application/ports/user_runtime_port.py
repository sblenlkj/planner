from __future__ import annotations

from typing import Protocol
from uuid import UUID


class UserRuntimePort(Protocol):
    async def get_ready_user_ids(self) -> tuple[UUID, ...]:
        raise NotImplementedError