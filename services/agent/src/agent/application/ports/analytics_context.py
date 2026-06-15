from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agent.application.dto import AnalyticsObservationDto


class AnalyticsContextPort(Protocol):
    async def list_observations(
        self,
        user_id: UUID,
        *,
        scope: str | None = None,
        status: str | None = "active",
        min_confidence: float | None = None,
        min_importance: float | None = None,
        limit: int | None = 20,
    ) -> list[AnalyticsObservationDto]: ...

    async def create_observation(
        self,
        user_id: UUID,
        *,
        description: str,
        scope: str = "productivity",
    ) -> AnalyticsObservationDto: ...