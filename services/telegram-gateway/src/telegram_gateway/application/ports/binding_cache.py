from typing import Protocol
from uuid import UUID

from telegram_gateway.domain.models import TelegramBinding


class BindingCache(Protocol):
    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> TelegramBinding | None:
        raise NotImplementedError

    async def get_by_business_user_id(
        self,
        business_user_id: UUID,
    ) -> TelegramBinding | None:
        raise NotImplementedError

    async def get_by_telegram_chat_id(
        self,
        telegram_chat_id: int,
    ) -> TelegramBinding | None:
        raise NotImplementedError

    async def set_binding(
        self,
        binding: TelegramBinding,
    ) -> None:
        raise NotImplementedError
