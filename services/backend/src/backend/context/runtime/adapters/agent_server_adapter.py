# backend/context/runtime/adapters/agent_server_adapter.py

from __future__ import annotations

from datetime import date
from uuid import UUID

import httpx

from backend.context.runtime.application.ports.agent_server_port import (
    AgentServerPort,
    MorningBriefingResult,
    MorningBriefingStatus,
)


class HttpAgentServerAdapter(AgentServerPort):
    def __init__(
        self,
        *,
        morning_briefing_url: str,
        internal_api_token: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._morning_briefing_url = morning_briefing_url
        self._internal_api_token = internal_api_token
        self._timeout_seconds = timeout_seconds

    async def run_morning_briefing(
        self,
        *,
        user_id: UUID,
        day: date,
    ) -> MorningBriefingResult:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._morning_briefing_url,
                headers=self._build_headers(user_id=user_id),
                json={
                    "date": day.isoformat(),
                },
            )

        response.raise_for_status()

        payload = response.json()
        status = self._parse_status(payload.get("status"))

        return MorningBriefingResult(
            status=status,
            text=payload.get("text"),
            reason=payload.get("reason"),
        )

    def _build_headers(
        self,
        *,
        user_id: UUID,
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._internal_api_token}",
            "X-Business-User-Id": str(user_id),
        }

    @staticmethod
    def _parse_status(
        raw_status: object,
    ) -> MorningBriefingStatus:
        if not isinstance(raw_status, str):
            return MorningBriefingStatus.ERROR

        try:
            return MorningBriefingStatus(raw_status)
        except ValueError:
            return MorningBriefingStatus.ERROR