from datetime import date, datetime
from uuid import UUID

import httpx

from telegram_gateway.application.ports.backend_client import (
    BackendClient,
    UserRuntimeStatus,
)


class HttpBackendClient(BackendClient):
    def __init__(
        self,
        *,
        create_user_url: str,
        get_user_runtime_status_url_template: str,
        update_user_runtime_status_url_template: str,
        update_user_last_session_at_url_template: str,
        generate_day_schedule_url: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._create_user_url = create_user_url
        self._get_user_runtime_status_url_template = get_user_runtime_status_url_template
        self._update_user_runtime_status_url_template = (
            update_user_runtime_status_url_template
        )
        self._update_user_last_session_at_url_template = (
            update_user_last_session_at_url_template
        )
        self._generate_day_schedule_url = generate_day_schedule_url
        self._timeout_seconds = timeout_seconds

    async def create_business_user(self) -> UUID:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(self._create_user_url, json={})

        response.raise_for_status()
        payload = response.json()
        return UUID(str(payload["user_id"]))

    async def get_user_runtime_status(
        self,
        business_user_id: UUID,
    ) -> UserRuntimeStatus:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(
                self._format_url(
                    self._get_user_runtime_status_url_template,
                    business_user_id,
                )
            )

        response.raise_for_status()
        payload = response.json()
        return UserRuntimeStatus(payload["status"])

    async def update_user_runtime_status(
        self,
        business_user_id: UUID,
        status: UserRuntimeStatus,
    ) -> UserRuntimeStatus:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.patch(
                self._format_url(
                    self._update_user_runtime_status_url_template,
                    business_user_id,
                ),
                json={"status": status.value},
            )

        response.raise_for_status()
        payload = response.json()
        return UserRuntimeStatus(payload["status"])

    async def update_user_last_session_at(
        self,
        business_user_id: UUID,
        last_session_at: datetime,
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.patch(
                self._format_url(
                    self._update_user_last_session_at_url_template,
                    business_user_id,
                ),
                json={"last_session_at": last_session_at.isoformat()},
            )

        response.raise_for_status()

    async def generate_day_schedule(
        self,
        business_user_id: UUID,
        day: date,
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._generate_day_schedule_url,
                json={"business_user_id": str(business_user_id), "day": day.isoformat()},
            )

        response.raise_for_status()

    def _format_url(self, url_template: str, business_user_id: UUID) -> str:
        return url_template.format(
            user_id=business_user_id,
            business_user_id=business_user_id,
        )
