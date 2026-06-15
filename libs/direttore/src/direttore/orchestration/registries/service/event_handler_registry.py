from __future__ import annotations

import inspect
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol, TypeVar

from direttore.orchestration.base_types.event_handler import EventHandler
from direttore.orchestration.base_types.message import Event


TEventHandler = TypeVar("TEventHandler", bound=type[EventHandler])


@dataclass(frozen=True, slots=True)
class EventHandlerRegistration:
    event_type: type[Event]
    handler_type: type[EventHandler]
    is_ready: bool = True
    source_name: str | None = None


class EventHandlerRegistryPort(Protocol):
    def get_registrations(
        self,
        event: Event,
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        raise NotImplementedError

    def get_registrations_by_event_type(
        self,
        event_type: type[Event],
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        raise NotImplementedError

    def iter_registrations(
        self,
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        raise NotImplementedError

    def get_handler_types_by_event_type(
        self,
        event_type: type[Event],
        *,
        include_not_ready: bool = False,
    ) -> list[type[EventHandler]]:
        raise NotImplementedError

    def iter_handler_types(
        self,
        *,
        include_not_ready: bool = False,
    ) -> list[type[EventHandler]]:
        raise NotImplementedError


class EventHandlerRegistry(EventHandlerRegistryPort):
    def __init__(self, *, source_name: str | None = None) -> None:
        self.source_name = source_name
        self._registrations_by_event: dict[
            type[Event],
            list[EventHandlerRegistration],
        ] = defaultdict(list)
        self._registrations: list[EventHandlerRegistration] = []
        self._registrations_by_key: dict[
            tuple[type[Event], type[EventHandler]],
            EventHandlerRegistration,
        ] = {}

    def handler(
        self,
        event_type: type[Event],
        *,
        is_ready: bool = True,
    ):
        self._validate_event_type(event_type)

        def decorator(handler_type: TEventHandler) -> TEventHandler:
            self.register(
                event_type=event_type,
                handler_type=handler_type,
                is_ready=is_ready,
            )
            return handler_type

        return decorator

    def register(
        self,
        *,
        event_type: type[Event],
        handler_type: type[EventHandler],
        is_ready: bool = True,
    ) -> None:
        self._validate_event_type(event_type)
        self._validate_handler_type(handler_type)

        self._add_registration(
            EventHandlerRegistration(
                event_type=event_type,
                handler_type=handler_type,
                is_ready=is_ready,
                source_name=self.source_name,
            )
        )

    def get_handler_types_by_event_type(
        self,
        event_type: type[Event],
        *,
        include_not_ready: bool = False,
    ) -> list[type[EventHandler]]:
        return [
            registration.handler_type
            for registration in self.get_registrations_by_event_type(
                event_type,
                include_not_ready=include_not_ready,
            )
        ]

    def get_registrations(
        self,
        event: Event,
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        return self.get_registrations_by_event_type(
            type(event),
            include_not_ready=include_not_ready,
        )

    def get_registrations_by_event_type(
        self,
        event_type: type[Event],
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        self._validate_event_type(event_type)

        registrations = self._registrations_by_event.get(event_type, [])

        if include_not_ready:
            return list(registrations)

        return [
            registration
            for registration in registrations
            if registration.is_ready
        ]

    def iter_handler_types(
        self,
        *,
        include_not_ready: bool = False,
    ) -> list[type[EventHandler]]:
        return [
            registration.handler_type
            for registration in self.iter_registrations(
                include_not_ready=include_not_ready,
            )
        ]

    def iter_registrations(
        self,
        *,
        include_not_ready: bool = False,
    ) -> list[EventHandlerRegistration]:
        if include_not_ready:
            return list(self._registrations)

        return [
            registration
            for registration in self._registrations
            if registration.is_ready
        ]

    def iter_event_types(self) -> list[type[Event]]:
        return list(self._registrations_by_event.keys())

    @classmethod
    def from_mapping(
        cls,
        mapping: dict[type[Event], list[type[EventHandler]]],
        *,
        source_name: str | None = None,
    ) -> EventHandlerRegistry:
        registry = cls(source_name=source_name)

        for event_type, handler_types in mapping.items():
            for handler_type in handler_types:
                registry.register(
                    event_type=event_type,
                    handler_type=handler_type,
                )

        return registry

    def _add_registration(self, registration: EventHandlerRegistration) -> None:
        key = (registration.event_type, registration.handler_type)

        existing_registration = self._registrations_by_key.get(key)

        if existing_registration is not None:
            raise ValueError(
                "Duplicate event handler registration. "
                f"Event={registration.event_type.__module__}."
                f"{registration.event_type.__qualname__}, "
                f"Handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}, "
                f"existing_source={existing_registration.source_name!r}, "
                f"new_source={registration.source_name!r}."
            )

        self._registrations_by_key[key] = registration
        self._registrations.append(registration)
        self._registrations_by_event[registration.event_type].append(registration)

    def _validate_event_type(self, event_type: type[Event]) -> None:
        if not isinstance(event_type, type):
            raise TypeError(f"Event type must be a type, got {event_type!r}.")

        if not issubclass(event_type, Event):
            raise TypeError(f"{event_type.__name__} must inherit from Event.")

    def _validate_handler_type(self, handler_type: type[EventHandler]) -> None:
        if not isinstance(handler_type, type):
            raise TypeError(f"Handler type must be a type, got {handler_type!r}.")

        if not issubclass(handler_type, EventHandler):
            raise TypeError(
                f"{handler_type.__name__} must inherit from EventHandler."
            )

        if inspect.isabstract(handler_type):
            raise TypeError(
                f"{handler_type.__name__} is abstract and cannot be registered."
            )