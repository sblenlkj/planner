from typing import Protocol


class TelegramMessageSender(Protocol):
    async def send_text(
        self,
        telegram_chat_id: int,
        text: str,
    ) -> None:
        raise NotImplementedError

    async def send_chat_action(
        self,
        telegram_chat_id: int,
        action: str,
    ) -> None:
        raise NotImplementedError
