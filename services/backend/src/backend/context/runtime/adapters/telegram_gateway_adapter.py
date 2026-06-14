from __future__ import annotations

from uuid import UUID

import httpx

from backend.context.runtime.application.ports.telegram_gateway_port import (
    CloseConversationResult,
    TelegramGatewayPort,
)


class HttpTelegramGatewayAdapter(TelegramGatewayPort):
    def __init__(
        self,
        *,
        send_message_url: str,
        close_conversation_url: str,
    ) -> None:
        self._send_message_url = send_message_url
        self._close_conversation_url = close_conversation_url

    async def send_message(
        self,
        *,
        user_id: UUID,
        text: str,
    ) -> None:
        payload = {
            "business_user_id": str(user_id),
            "text": text,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._send_message_url,
                json=payload,
            )
            response.raise_for_status()

    async def close_conversation(
        self,
        *,
        user_id: UUID,
    ) -> CloseConversationResult:
        payload = {
            "business_user_id": str(user_id),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._close_conversation_url,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()

        return CloseConversationResult(
            user_id=user_id,
            closed=bool(data.get("closed", False)),
            reason=data.get("reason"),
        )