from typing import Protocol

from telegram_gateway.domain.models import ConversationMessage


class ConversationStore(Protocol):
    async def get_messages(
        self,
        telegram_chat_id: int,
    ) -> list[ConversationMessage]:
        raise NotImplementedError

    async def append_message(
        self,
        telegram_chat_id: int,
        message: ConversationMessage,
    ) -> None:
        raise NotImplementedError

    async def clear_messages(
        self,
        telegram_chat_id: int,
    ) -> None:
        raise NotImplementedError
