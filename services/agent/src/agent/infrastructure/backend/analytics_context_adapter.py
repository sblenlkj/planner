from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from agent.application.dto.analytics import AnalyticsInsightDto, AnalyticsObservationDto
from agent.application.ports.analytics_context import AnalyticsContextPort
from agent.core.backend_settings import BackendApiSettings
from agent.infrastructure.backend.http_client import BackendHttpClient
from .parsing import extract_created_id

class HttpAnalyticsContextAdapter(AnalyticsContextPort):
    """HTTP adapter for Backend analytics context.

    Backend stores a rich analytics model, but Agent Server MVP uses analytics
    as compact prompt memory. Therefore read/write methods expose only
    observation id + description to the agent layer.

    Real Backend endpoints:
      GET  /analytics/observations
      POST /analytics/observations
    """

    def __init__(
        self,
        *,
        client: BackendHttpClient,
        settings: BackendApiSettings,
    ) -> None:
        self._client = client
        self._settings = settings

    async def list_observations(
        self,
        user_id: UUID,
        *,
        scope: str | None = None,
        status: str | None = "active",
        min_confidence: float | None = None,
        min_importance: float | None = None,
        limit: int | None = 20,
    ) -> list[AnalyticsObservationDto]:
        params: dict[str, Any] = {
            "user_id": str(user_id),
            "scope": scope,
            "status": status,
            "min_confidence": min_confidence,
            "min_importance": min_importance,
            "limit": limit,
        }

        payload = await self._client.get_json(
            self._settings.list_analytics_observations_path,
            params=params,
        )

        items = _extract_items(payload, key="observations")
        return [AnalyticsObservationDto.from_mapping(item) for item in items]

    async def create_observation(
        self,
        user_id: UUID,
        *,
        description: str,
        scope: str = "productivity",
    ) -> AnalyticsObservationDto:
        payload = await self._client.post_json(
            self._settings.create_analytics_observation_path,
            json={
                "user_id": str(user_id),
                "scope": scope,
                "description": description,
                "evidence": None,
                "confidence": 0.7,
                "importance": 0.5,
                "stability": "short_term",
                "tags": [],
                "valid_until": None,
                "source": "agent_observation",
                "source_id": None,
            },
        )

        observation_id = extract_created_id(payload, "observation_id", "id")

        return AnalyticsObservationDto(
            id=observation_id,
            description=description,
        )


def _extract_items(payload: Any, *, key: str) -> list[Mapping[str, Any]]:
    """Extract list response from common backend shapes.

    Supported shapes:
      - [{...}, {...}]
      - {"observations": [{...}]}
      - {"items": [{...}]}
      - {"data": [{...}]}
    """

    if payload is None:
        return []

    if isinstance(payload, list):
        return [_ensure_mapping(item) for item in payload]

    if isinstance(payload, Mapping):
        for candidate_key in (key, "items", "data"):
            value = payload.get(candidate_key)
            if isinstance(value, list):
                return [_ensure_mapping(item) for item in value]

    raise TypeError(f"Unexpected analytics list payload shape: {payload!r}")


def _extract_single(payload: Any, *, key: str) -> Mapping[str, Any]:
    """Extract single item response from common backend shapes.

    Supported shapes:
      - {"id": "...", "description": "..."}
      - {"observation": {"id": "...", "description": "..."}}
      - {"item": {...}}
      - {"data": {...}}
    """

    if isinstance(payload, Mapping):
        nested = payload.get(key) or payload.get("item") or payload.get("data")
        if nested is not None:
            return _ensure_mapping(nested)

        if "id" in payload and "description" in payload:
            return payload

    raise TypeError(f"Unexpected analytics single payload shape: {payload!r}")


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise TypeError(f"Expected mapping payload item, got: {type(value)!r}")