from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class AnalyticsPlanningInsightReadModel:
    description: str


@dataclass(frozen=True, kw_only=True)
class AnalyticsPlanningContextReadModel:
    insights: list[AnalyticsPlanningInsightReadModel]


class AnalyticsPlanningContextPort(Protocol):
    async def get_user_planning_context(
        self,
        user_id: UUID,
    ) -> AnalyticsPlanningContextReadModel:
        raise NotImplementedError