from uuid import UUID

import httpx

from telegram_gateway.application.errors import BusinessUserNotFoundError
from telegram_gateway.application.ports.backend_client import BackendClient


class HttpBackendClient(BackendClient):
    def __init__(
        self,
        *,
        get_user_url_template: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._get_user_url_template = get_user_url_template
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

    def _format_url(self, url_template: str, business_user_id: UUID) -> str:
        return url_template.format(
            user_id=business_user_id,
            business_user_id=business_user_id,
        )
