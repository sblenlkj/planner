from uuid import UUID

import httpx

from telegram_gateway.application.errors import BusinessUserNotFoundError


class HttpBackendClient:
    def __init__(
        self,
        *,
        get_user_url_template: str,
        create_user_url: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._get_user_url_template = get_user_url_template
        self._create_user_url = create_user_url
        self._timeout_seconds = timeout_seconds

    async def ensure_user_exists(
        self,
        business_user_id: UUID,
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(
                self._format_url(self._get_user_url_template, business_user_id),
            )

        if response.status_code == 404:
            raise BusinessUserNotFoundError(
                f"Business user was not found: {business_user_id}"
            )

        response.raise_for_status()

    async def create_user(
        self,
        *,
        password: str,
        login: str,
        name: str,
        utc_offset_minutes: int,
    ) -> UUID:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._create_user_url,
                json={
                    "password": password,
                    "login": login,
                    "name": name,
                    "utc_offset_minutes": utc_offset_minutes,
                },
            )

        response.raise_for_status()
        payload = response.json()
        return UUID(payload["user_id"])

    def _format_url(self, url_template: str, business_user_id: UUID) -> str:
        return url_template.format(
            user_id=business_user_id,
            business_user_id=business_user_id,
        )
