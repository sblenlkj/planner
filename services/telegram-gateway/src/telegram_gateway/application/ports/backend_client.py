from datetime import date, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class UserRuntimeStatus(StrEnum):
    NOT_READY = "not_ready"
    READY = "ready"


class BackendClient(Protocol):
    async def create_business_user(self) -> UUID:
        raise NotImplementedError

    async def get_user_runtime_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus:
        raise NotImplementedError

    async def update_user_runtime_status(
        self,
        business_user_id: UUID,
        status: UserRuntimeStatus,
    ) -> UserRuntimeStatus:
        raise NotImplementedError

    async def update_user_last_session_at(
        self,
        business_user_id: UUID,
        last_session_at: datetime,
    ) -> None:
        raise NotImplementedError

    async def generate_day_schedule(
        self,
        business_user_id: UUID,
        day: date,
    ) -> None:
        raise NotImplementedError
