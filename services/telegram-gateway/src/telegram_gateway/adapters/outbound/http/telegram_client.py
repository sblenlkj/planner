import httpx

from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)


class TelegramBotClient(TelegramMessageSender):
    def __init__(
        self,
        *,
        bot_token: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._timeout_seconds = timeout_seconds

    async def send_text(self, telegram_chat_id: int, text: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/sendMessage",
                json={"chat_id": telegram_chat_id, "text": text},
            )

        response.raise_for_status()
        payload = response.json()

        if not payload.get("ok", False):
            raise RuntimeError(
                f"Telegram sendMessage failed: {payload.get('description', 'unknown')}"
            )

    async def send_chat_action(
        self,
        telegram_chat_id: int,
        action: str = "typing",
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/sendChatAction",
                json={"chat_id": telegram_chat_id, "action": action},
            )

        response.raise_for_status()
