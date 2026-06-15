import asyncio

import httpx

from telegram_gateway.application.ports.telegram_message_sender import (
    TelegramMessageSender,
)
from telegram_gateway.application.errors import TelegramMessageDeliveryError

class TelegramBotClient(TelegramMessageSender):
    def __init__(
        self,
        *,
        bot_token: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._timeout_seconds = timeout_seconds

    async def send_text(
        self,
        telegram_chat_id: int,
        text: str,
    ) -> None:
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(
                        f"{self._base_url}/sendMessage",
                        json={
                            "chat_id": telegram_chat_id,
                            "text": text,
                        },
                    )

                if response.is_error:
                    raise TelegramMessageDeliveryError(
                        "Telegram sendMessage failed: "
                        f"status={response.status_code}, body={response.text}"
                    )

                return

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                await asyncio.sleep(0.5 * (attempt + 1))

        raise RuntimeError(f"Telegram sendMessage failed after retries: {last_error}")
