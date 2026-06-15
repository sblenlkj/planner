from __future__ import annotations

from typing import Any
from uuid import UUID

from direttore.orchestration.base_types.message import DomainEvent


class TrackingRepository:
    def __init__(self) -> None:
        self._tracked: dict[UUID, Any] = {}

    def _track(self, entity: Any | None) -> Any | None:
        if entity is None:
            return None

        entity_id = getattr(entity, "id", None)

        if entity_id is None:
            raise TypeError(
                "Tracked object must have an 'id' attribute. "
                f"Got {type(entity).__module__}.{type(entity).__qualname__}."
            )

        pull_domain_events = getattr(entity, "pull_domain_events", None)

        if pull_domain_events is None:
            raise TypeError(
                "Tracked object must have a 'pull_domain_events' method. "
                f"Got {type(entity).__module__}.{type(entity).__qualname__}."
            )

        self._tracked[entity_id] = entity
        return entity

    def collect_events(self) -> list[DomainEvent]:
        result: list[DomainEvent] = []

        for aggregate in self._tracked.values():
            result.extend(aggregate.pull_domain_events())

        return result

    def clear_tracked(self) -> None:
        self._tracked.clear()