from uuid import UUID

import httpx

from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.domain.models import ConversationMessage


class HttpAgentClient(AgentClient):
    def __init__(
        self,
        *,
        handle_onboarding_messages_url: str,
        handle_messages_url: str,
        internal_api_token: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._handle_onboarding_messages_url = handle_onboarding_messages_url
        self._handle_messages_url = handle_messages_url
        self._internal_api_token = internal_api_token
        self._timeout_seconds = timeout_seconds

    async def handle_onboarding_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        return await self._post_messages(
            url=self._handle_onboarding_messages_url,
            business_user_id=business_user_id,
            messages=messages,
        )

    async def handle_messages(
        self,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        return await self._post_messages(
            url=self._handle_messages_url,
            business_user_id=business_user_id,
            messages=messages,
        )

    async def _post_messages(
        self,
        *,
        url: str,
        business_user_id: UUID,
        messages: list[ConversationMessage],
    ) -> str | None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                url,
                headers=self._headers(business_user_id),
                json={
                    "messages": [
                        {"role": message.role.value, "content": message.content}
                        for message in messages
                    ],
                },
            )

        response.raise_for_status()
        payload = response.json()
        return payload.get("assistant_text")

    def _headers(self, business_user_id: UUID) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._internal_api_token}",
            "X-Business-User-Id": str(business_user_id),
        }
