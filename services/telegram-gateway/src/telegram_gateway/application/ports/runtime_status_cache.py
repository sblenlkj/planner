from typing import Protocol
from uuid import UUID

from telegram_gateway.application.ports.backend_client import UserRuntimeStatus


class RuntimeStatusCache(Protocol):
    async def get_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus | None:
        raise NotImplementedError

    async def set_status(
        self,
        business_user_id: UUID,
        status: UserRuntimeStatus,
    ) -> None:
        raise NotImplementedError

    async def clear_status(
        self,
        business_user_id: UUID,
    ) -> None:
        raise NotImplementedError
