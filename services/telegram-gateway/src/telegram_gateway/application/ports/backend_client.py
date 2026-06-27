from uuid import UUID
from typing import Protocol


class BackendClient(Protocol):
    async def ensure_user_exists(
        self,
        business_user_id: UUID,
    ) -> None:
        ...

    async def create_user(
        self,
        *,
        password: str,
        login: str,
        name: str,
        utc_offset_minutes: int,
    ) -> UUID:
        ...
