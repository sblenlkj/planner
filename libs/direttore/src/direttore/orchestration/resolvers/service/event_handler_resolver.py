from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, get_type_hints

from direttore.orchestration.base_types.event_handler import EventHandler
from direttore.orchestration.base_types.message import Event
from direttore.orchestration.registries.service.event_handler_registry import (
    EventHandlerRegistration,
    EventHandlerRegistryPort,
)
from direttore.orchestration.resolvers.container import Container


TEventHandler = TypeVar("TEventHandler", bound=EventHandler)


@dataclass(frozen=True, slots=True)
class ResolvedEventHandlerConfig:
    source_name: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedEventHandler:
    handler: EventHandler
    config: ResolvedEventHandlerConfig


class EventHandlerResolverPort(Protocol):
    def validate_event_handlers(
        self,
        *,
        include_not_ready: bool = False,
    ) -> None:
        raise NotImplementedError

    def resolve(
        self,
        event: Event,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
        include_not_ready: bool = False,
    ) -> list[ResolvedEventHandler]:
        raise NotImplementedError


class ContainerEventHandlerResolver(EventHandlerResolverPort):
    def __init__(
        self,
        registry: EventHandlerRegistryPort,
        container: Container,
    ) -> None:
        self._registry = registry
        self._container = container

    def validate_event_handlers(
        self,
        *,
        include_not_ready: bool = False,
    ) -> None:
        seen: set[type[EventHandler]] = set()

        for registration in self._registry.iter_registrations(
            include_not_ready=include_not_ready,
        ):
            handler_type = registration.handler_type

            if handler_type in seen:
                continue

            self._container.get(handler_type)
            seen.add(handler_type)

    def resolve(
        self,
        event: Event,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
        include_not_ready: bool = False,
    ) -> list[ResolvedEventHandler]:
        if overrides:
            raise RuntimeError(
                "ContainerEventHandlerResolver does not support execution "
                "dependency overrides. Use WarmUpCacheAutoWiringEventHandlerResolver "
                "when event handlers need modular-monolith in-process clients."
            )

        registrations = self._registry.get_registrations_by_event_type(
            type(event),
            include_not_ready=include_not_ready,
        )

        return [
            self._resolve_registration(
                registration=registration,
            )
            for registration in registrations
        ]

    def _resolve_registration(
        self,
        *,
        registration: EventHandlerRegistration,
    ) -> ResolvedEventHandler:
        return ResolvedEventHandler(
            handler=self._container.get(registration.handler_type),
            config=ResolvedEventHandlerConfig(
                source_name=registration.source_name,
            ),
        )


class WarmUpCacheAutoWiringEventHandlerResolver(EventHandlerResolverPort):
    """
    Auto-wiring event handler resolver with eager cache warm-up.

    Cache is populated only during warm-up.

    Runtime resolve path:
    - if handler is cached, return cached instance;
    - otherwise build a fresh instance using execution overrides when relevant.

    Handlers that depend on execution-scoped dependency types are never cached.
    """

    def __init__(
        self,
        *,
        registry: EventHandlerRegistryPort,
        container: Container,
        execution_dependency_types: set[type[Any]] | None = None,
        include_not_ready: bool = False,
    ) -> None:
        self._registry = registry
        self._container = container
        self._execution_dependency_types = execution_dependency_types or set()
        self._include_not_ready = include_not_ready
        self._cache: dict[type[EventHandler], EventHandler] = {}

        self.warm_up_cache()

    def warm_up_cache(self) -> None:
        for registration in self._registry.iter_registrations(
            include_not_ready=self._include_not_ready,
        ):
            self._warm_up_registration_cache(registration)

    def validate_event_handlers(
        self,
        *,
        include_not_ready: bool = False,
    ) -> None:
        for registration in self._registry.iter_registrations(
            include_not_ready=include_not_ready,
        ):
            self._validate_handler(registration=registration)

    def resolve(
        self,
        event: Event,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
        include_not_ready: bool = False,
    ) -> list[ResolvedEventHandler]:
        registrations = self._registry.get_registrations_by_event_type(
            type(event),
            include_not_ready=include_not_ready,
        )

        return [
            self._resolve_registration(
                registration=registration,
                overrides=overrides,
            )
            for registration in registrations
        ]

    def _resolve_registration(
        self,
        *,
        registration: EventHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedEventHandler:
        return ResolvedEventHandler(
            handler=self._resolve_handler(
                registration=registration,
                overrides=overrides,
            ),
            config=ResolvedEventHandlerConfig(
                source_name=registration.source_name,
            ),
        )

    def _warm_up_registration_cache(
        self,
        registration: EventHandlerRegistration,
    ) -> None:
        handler_type = registration.handler_type

        if handler_type in self._cache:
            raise RuntimeError(
                "Event handler type is already cached. "
                "This usually means duplicate registration. "
                f"Handler={handler_type.__module__}.{handler_type.__qualname__}."
            )

        if self._uses_execution_dependency_types(handler_type):
            return

        self._cache[handler_type] = self._create_handler(
            handler_type=handler_type,
            overrides=None,
        )

    def _resolve_handler(
        self,
        *,
        registration: EventHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> EventHandler:
        handler_type = registration.handler_type

        cached_handler = self._cache.get(handler_type)
        if cached_handler is not None:
            return cached_handler

        return self._create_handler(
            handler_type=handler_type,
            overrides=overrides,
        )

    def _validate_handler(
        self,
        *,
        registration: EventHandlerRegistration,
    ) -> None:
        self._resolve_init_kwargs(
            handler_type=registration.handler_type,
            overrides=None,
        )

    def _create_handler(
        self,
        *,
        handler_type: type[EventHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> EventHandler:
        kwargs = self._resolve_init_kwargs(
            handler_type=handler_type,
            overrides=overrides,
        )

        return handler_type(**kwargs)

    def _resolve_init_kwargs(
        self,
        *,
        handler_type: type[EventHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        for name, dependency_type in self._iter_init_dependencies(handler_type):
            if overrides is not None and dependency_type in overrides:
                kwargs[name] = overrides[dependency_type]
                continue

            kwargs[name] = self._container.get(dependency_type)

        return kwargs

    def _uses_execution_dependency_types(
        self,
        handler_type: type[EventHandler],
    ) -> bool:
        if not self._execution_dependency_types:
            return False

        dependency_types = self._get_init_dependency_types(handler_type)

        return any(
            dependency_type in self._execution_dependency_types
            for dependency_type in dependency_types
        )

    def _get_init_dependency_types(
        self,
        handler_type: type[EventHandler],
    ) -> set[type[Any]]:
        return {
            dependency_type
            for _, dependency_type in self._iter_init_dependencies(handler_type)
        }

    def _iter_init_dependencies(
        self,
        handler_type: type[EventHandler],
    ) -> list[tuple[str, type[Any]]]:
        signature = inspect.signature(handler_type.__init__)
        hints = get_type_hints(handler_type.__init__)

        dependencies: list[tuple[str, type[Any]]] = []

        for name, parameter in signature.parameters.items():
            if name == "self":
                continue

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            annotation = hints.get(name)

            if annotation is None:
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} must have a resolvable "
                    "type annotation."
                )

            if not isinstance(annotation, type):
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} annotation must be a type, "
                    f"got {annotation!r}."
                )

            dependencies.append((name, annotation))

        return dependencies