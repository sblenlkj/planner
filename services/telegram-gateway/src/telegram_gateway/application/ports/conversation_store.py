from uuid import UUID
from typing import Protocol

from telegram_gateway.domain.models import ConversationMessage


class ConversationStore(Protocol):
    async def append_message(
        self,
        business_user_id: UUID,
        message: ConversationMessage,
    ) -> list[ConversationMessage]:
        ...

    async def get_messages(
        self,
        business_user_id: UUID,
    ) -> list[ConversationMessage]:
        ...

    async def clear_messages(
        self,
        business_user_id: UUID,
    ) -> None:
        ...
