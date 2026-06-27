from uuid import UUID
from typing import Protocol

from telegram_gateway.domain.models import TelegramBinding


class TelegramBindingRepository(Protocol):
    async def add(
        self,
        binding: TelegramBinding,
    ) -> None:
        ...

    async def upsert(
        self,
        binding: TelegramBinding,
    ) -> None:
        ...

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> TelegramBinding | None:
        ...

    async def get_by_business_user_id(
        self,
        business_user_id: UUID,
    ) -> TelegramBinding | None:
        ...
