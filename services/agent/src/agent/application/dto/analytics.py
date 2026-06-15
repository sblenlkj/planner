from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID


def _uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


@dataclass(frozen=True, slots=True)
class AnalyticsObservationDto:
    """Agent-side analytics observation DTO.

    The backend analytics domain stores rich records:
    scope, confidence, importance, stability, evidence, status, source, etc.

    For the MVP agent context we intentionally expose only the fields
    the agent really needs for prompt memory:
      - id
      - description
    """

    id: UUID
    description: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AnalyticsObservationDto":
        return cls(
            id=_uuid(data["id"]),
            description=str(data["description"]),
        )


@dataclass(frozen=True, slots=True)
class AnalyticsInsightDto:
    """Minimal agent-side analytics insight DTO.

    Kept for future compatibility. If insights are not exposed by the backend yet,
    this class can remain unused.
    """

    id: UUID
    description: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AnalyticsInsightDto":
        return cls(
            id=_uuid(data["id"]),
            description=str(data["description"]),
        )