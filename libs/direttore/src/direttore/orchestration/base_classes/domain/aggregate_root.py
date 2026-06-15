from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from typing import ClassVar
from abc import ABC, abstractmethod


from direttore.orchestration.base_types.message import DomainEvent


@dataclass(eq=False)
class AbstractAggregateRoot(ABC):
    id: UUID
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    @property
    def events(self) -> list[DomainEvent]:
        return self._domain_events

    def record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)
    
    @abstractmethod
    def pull_domain_events(self) -> list[DomainEvent]:
        raise NotImplementedError



@dataclass(eq=False)
class SimpleAggregateRoot(AbstractAggregateRoot):
    """
    Aggregate root that collects only its own domain events.
    """

    def pull_domain_events(self) -> list[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events


@dataclass(eq=False)
class NestedAggregateRoot(AbstractAggregateRoot):
    __track__: ClassVar[tuple[str, ...]] = ()

    def pull_domain_events(self) -> list[DomainEvent]:
        visited: set[int] = set()
        return self._pull_domain_events_recursive(visited)

    def _pull_domain_events_recursive(self, visited: set[int]) -> list[DomainEvent]:
        obj_id = id(self)
        if obj_id in visited:
            return []

        visited.add(obj_id)

        events = self._pull_own_domain_events()

        for attr_name in self.__track__:
            if not hasattr(self, attr_name):
                raise AttributeError(
                    f"{type(self).__name__} declares tracked attribute '{attr_name}', "
                    f"but it does not exist."
                )

            value = getattr(self, attr_name)
            events.extend(self._pull_domain_events_from_value(value, visited))

        return events

    def _pull_own_domain_events(self) -> list[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def _pull_domain_events_from_value(
        self,
        value: object,
        visited: set[int],
    ) -> list[DomainEvent]:
        if value is None:
            return []

        if isinstance(value, AbstractAggregateRoot):
            return self._pull_from_aggregate(value, visited)

        if isinstance(value, (list, tuple)):
            events: list[DomainEvent] = []
            for item in value:
                if not isinstance(item, AbstractAggregateRoot):
                    raise TypeError(
                        f"Tracked collection contains unsupported item type {type(item)}."
                    )

                events.extend(self._pull_from_aggregate(item, visited))

            return events

        raise TypeError(
            f"Tracked attribute has unsupported type {type(value)}. "
            "Expected aggregate, list[aggregate], tuple[aggregate], or None."
        )

    def _pull_from_aggregate(
        self,
        aggregate: AbstractAggregateRoot,
        visited: set[int],
    ) -> list[DomainEvent]:
        if isinstance(aggregate, NestedAggregateRoot):
            return aggregate._pull_domain_events_recursive(visited)

        return aggregate.pull_domain_events()