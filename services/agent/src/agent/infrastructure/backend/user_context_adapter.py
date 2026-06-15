from __future__ import annotations

from typing import Any
from uuid import UUID

from agent.application.dto import UserProfileDto
from agent.application.ports import UserContextPort
from agent.core.backend_settings import BackendApiSettings

from .http_client import BackendHttpClient
from .parsing import as_int_or_none, as_uuid, require_mapping


class HttpUserContextAdapter(UserContextPort):
    def __init__(self, *, client: BackendHttpClient, settings: BackendApiSettings) -> None:
        self._client = client
        self._settings = settings

    async def get_user_profile(self, user_id: UUID) -> UserProfileDto:
        path = self._settings.get_user_profile_path.format(user_id=user_id)
        payload = require_mapping(await self._client.get_json(path))
        return _parse_user_profile(payload)

    async def update_user_profile(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        language: str | None = None,
        utc_offset_minutes: int | None = None,
        region: str | None = None,
    ) -> UserProfileDto:
        path = self._settings.update_user_profile_path.format(user_id=user_id)
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if language is not None:
            body["language"] = language
        if utc_offset_minutes is not None:
            body["utc_offset_minutes"] = utc_offset_minutes
        if region is not None:
            body["region"] = region

        payload = require_mapping(await self._client.patch_json(path, json=body))
        return _parse_user_profile(payload)


def _parse_user_profile(payload: dict[str, Any]) -> UserProfileDto:
    return UserProfileDto(
        user_id=as_uuid(payload.get("user_id") or payload.get("id"), field="user_id"),
        login=payload.get("login") or payload.get("email"),
        name=payload.get("name"),
        language=payload.get("language"),
        utc_offset_minutes=as_int_or_none(payload.get("utc_offset_minutes")),
        region=payload.get("region"),
        runtime_status=payload.get("runtime_status") or payload.get("status"),
    )
