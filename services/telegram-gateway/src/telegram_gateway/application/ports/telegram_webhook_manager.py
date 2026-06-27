from typing import Protocol


class TelegramWebhookManager(Protocol):
    async def set_webhook(
        self,
        *,
        webhook_url: str,
        secret_token: str,
        drop_pending_updates: bool,
    ) -> None:
        ...

    async def delete_webhook(
        self,
        *,
        drop_pending_updates: bool,
    ) -> None:
        ...
