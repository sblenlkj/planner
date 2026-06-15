from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self

class Message:
    """Base message type for orchestration kernel."""

    pass

class ApplicationMessage(Message):
    """Base message type for application layer: command and query."""

    pass

class Command(ApplicationMessage):
    """Base command type."""

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> Self:
        return cls(**payload)

    def to_payload(self) -> dict[str, Any]:
        return dict(self.__dict__)


class Query(ApplicationMessage):
    """Base query type."""

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> Self:
        return cls(**payload)

    def to_payload(self) -> dict[str, Any]:
        return dict(self.__dict__)

class Event(Message):
    """Base event type."""

    pass


class DomainEvent(Event):
    """Event raised by aggregate roots / domain model."""

    pass


class ApplicationEvent(Event):
    """Event raised by application layer."""

    pass