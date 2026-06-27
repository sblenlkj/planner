from typing import Protocol


class TelegramMessageSender(Protocol):
    async def send_text(
        self,
        telegram_chat_id: int,
        text: str,
    ) -> None:
        ...
