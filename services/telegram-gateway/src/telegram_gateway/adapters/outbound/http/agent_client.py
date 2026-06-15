from datetime import datetime
from uuid import UUID

import httpx

from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.domain.models import ConversationMessage


class HttpAgentClient(AgentClient):
    def __init__(
        self,
        *,
        handle_messages_url: str,
        close_session_url: str,
        internal_api_token: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._handle_messages_url = handle_messages_url
        self._close_session_url = close_session_url
        self._internal_api_token = internal_api_token
        self._timeout_seconds = timeout_seconds

    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._handle_messages_url,
                headers=self._headers(business_user_id),
                json={
                    "messages": self._serialize_messages(messages),
                },
            )

        response.raise_for_status()
        payload = response.json()
        return payload.get("assistant_text")

    async def close_session(
        self,
        business_user_id: UUID,
        closed_at: datetime,
        messages: list[ConversationMessage],
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._close_session_url,
                headers=self._headers(business_user_id),
                json={
                    "closed_at": closed_at.isoformat(),
                    "messages": self._serialize_messages(messages),
                },
            )

        response.raise_for_status()

    def _headers(
        self,
        business_user_id: UUID,
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._internal_api_token}",
            "X-Business-User-Id": str(business_user_id),
        }

    def _serialize_messages(
        self,
        messages: list[ConversationMessage],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]
