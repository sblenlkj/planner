from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from telegram_gateway.application.errors import (
    AgentInputBlockedError,
    AgentResponseError,
)
from telegram_gateway.domain.models import ConversationMessage


class HttpAgentClient:
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
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._handle_messages_url,
                    headers=self._headers(business_user_id),
                    json={
                        "messages": self._serialize_messages(messages),
                    },
                )
        except httpx.RequestError as exc:
            raise AgentResponseError(
                f"Failed to reach Agent Server at {self._handle_messages_url}: {exc}"
            ) from exc

        self._ensure_success(response)

        payload = response.json()
        return payload.get("assistant_text")

    async def close_session(
        self,
        business_user_id: UUID,
        closed_at: datetime,
        messages: list[ConversationMessage],
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._close_session_url,
                    headers=self._headers(business_user_id),
                    json={
                        "closed_at": closed_at.isoformat(),
                        "messages": self._serialize_messages(messages),
                    },
                )
        except httpx.RequestError as exc:
            raise AgentResponseError(
                f"Failed to reach Agent Server at {self._close_session_url}: {exc}"
            ) from exc

        self._ensure_success(response)

    def _ensure_success(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return

        payload = self._safe_json(response)

        if response.status_code == 403:
            error = payload.get("error") if isinstance(payload, dict) else None

            if isinstance(error, dict) and error.get("code") == "input_guard_blocked":
                violations = error.get("violations")
                raise AgentInputBlockedError(
                    error.get(
                        "message",
                        "User message was blocked by Agent Server input guard.",
                    ),
                    violations=violations if isinstance(violations, list) else [],
                )

        raise AgentResponseError(
            f"Agent Server returned {response.status_code}: {response.text}"
        )

    def _safe_json(self, response: httpx.Response) -> dict[str, Any] | list[Any] | None:
        try:
            payload = response.json()
        except ValueError:
            return None

        if isinstance(payload, (dict, list)):
            return payload

        return None

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
