from __future__ import annotations

from typing import Any

import httpx


class HttpTelegramWebhookManager:
    def __init__(
        self,
        *,
        bot_token: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._timeout_seconds = timeout_seconds

    async def set_webhook(
        self,
        *,
        webhook_url: str,
        secret_token: str,
        drop_pending_updates: bool,
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/setWebhook",
                json={
                    "url": webhook_url,
                    "secret_token": secret_token,
                    "drop_pending_updates": drop_pending_updates,
                },
            )
        self._ensure_success(response)

    async def delete_webhook(
        self,
        *,
        drop_pending_updates: bool,
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/deleteWebhook",
                json={
                    "drop_pending_updates": drop_pending_updates,
                },
            )
        self._ensure_success(response)

    def _ensure_success(self, response: httpx.Response) -> None:
        if response.is_error:
            raise RuntimeError(
                f"Telegram webhook API failed: status={response.status_code}, body={response.text}"
            )
