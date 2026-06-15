from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, Protocol, TypeVar

from direttore.orchestration.base_types.event_handler import (
    AbstractContextEventHandler,
    AbstractEventHandler,
    EventHandler,
    EventHandlerContext,
)
from direttore.orchestration.base_types.message import Event
from direttore.orchestration.modular_monolith.coordinator import (
    ModularUnitOfWorkCoordinator,
)
from direttore.orchestration.registries.modular_monolith.modular_event_handler_registry import (
    ModularMonolithEventHandlerRegistry,
)
from direttore.orchestration.resolvers.service.event_handler_resolver import (
    EventHandlerResolverPort,
    ResolvedEventHandler,
)
from direttore.orchestration.tracing import (
    TraceSpanFactoryPort,
    TraceSpanPort,
)


TraceT = TypeVar("TraceT")


class ModularMonolithEventDispatcherPort(Protocol):
    def validate_event_handlers(self) -> None:
        raise NotImplementedError

    async def dispatch(
        self,
        *,
        event: Event,
        coordinator: ModularUnitOfWorkCoordinator,
        overrides: Mapping[type[Any], Any] | None = None,
        trace: Any | None = None,
    ) -> None:
        raise NotImplementedError


class ModularMonolithEventDispatcher(
    ModularMonolithEventDispatcherPort,
    Generic[TraceT],
):
    """
    Event dispatcher for modular-monolith execution.

    The dispatcher is stateless. The coordinator is execution-scoped and is
    passed to dispatch(...).

    Each context event handler receives the UoW of the context where that
    handler was registered, not the root command UoW.
    """

    def __init__(
        self,
        *,
        resolver: EventHandlerResolverPort,
        registry: ModularMonolithEventHandlerRegistry,
        trace_span_factory: TraceSpanFactoryPort[TraceT] | None = None,
    ) -> None:
        self._resolver = resolver
        self._registry = registry
        self._trace_span_factory = trace_span_factory

    def validate_event_handlers(self) -> None:
        self._resolver.validate_event_handlers()

    async def dispatch(
        self,
        *,
        event: Event,
        coordinator: ModularUnitOfWorkCoordinator,
        overrides: Mapping[type[Any], Any] | None = None,
        trace: TraceT | None = None,
    ) -> None:
        resolved_handlers = self._resolver.resolve(
            event,
            overrides=overrides,
        )

        for resolved_handler in resolved_handlers:
            await self._dispatch_resolved_handler(
                event=event,
                resolved_handler=resolved_handler,
                coordinator=coordinator,
                trace=trace,
            )

    async def _dispatch_resolved_handler(
        self,
        *,
        event: Event,
        resolved_handler: ResolvedEventHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        trace: TraceT | None,
    ) -> None:
        if self._trace_span_factory is None:
            await self._dispatch_handler(
                event=event,
                handler=resolved_handler.handler,
                coordinator=coordinator,
            )
            return

        async with self._start_span(
            trace=trace,
            event=event,
            handler=resolved_handler.handler,
            source_name=resolved_handler.config.source_name,
        ):
            await self._dispatch_handler(
                event=event,
                handler=resolved_handler.handler,
                coordinator=coordinator,
            )

    async def _dispatch_handler(
        self,
        *,
        event: Event,
        handler: EventHandler,
        coordinator: ModularUnitOfWorkCoordinator,
    ) -> None:
        if isinstance(handler, AbstractContextEventHandler):
            root_uow_type = self._registry.get_root_uow_type_by_handler(handler)
            handler_uow = coordinator.get_command_uow(root_uow_type)

            await handler(
                event,
                EventHandlerContext(
                    command_uow=handler_uow,
                ),
            )
            return

        if isinstance(handler, AbstractEventHandler):
            await handler(event)
            return

        raise RuntimeError(
            f"Unknown event handler kind {handler.event_handler_kind!r} "
            f"for {type(handler).__module__}."
            f"{type(handler).__qualname__}."
        )

    def _start_span(
        self,
        *,
        trace: TraceT | None,
        event: Event,
        handler: EventHandler,
        source_name: str | None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        if self._trace_span_factory is None:
            raise RuntimeError("Trace span factory is not configured.")

        return self._trace_span_factory.start_span(
            trace=trace,
            name=self._build_span_name(
                operation="event_handler",
                source_name=source_name,
                event=event,
            ),
            attributes=self._build_span_attributes(
                event=event,
                handler=handler,
                source_name=source_name,
            ),
        )

    def _build_span_name(
        self,
        *,
        operation: str,
        source_name: str | None,
        event: Event,
    ) -> str:
        event_name = type(event).__qualname__

        if source_name is None:
            return f"orchestration.{operation} {event_name}"

        return f"orchestration.{operation} {source_name}.{event_name}"

    def _build_span_attributes(
        self,
        *,
        event: Event,
        handler: EventHandler,
        source_name: str | None,
    ) -> dict[str, Any]:
        return {
            "orchestration.source": source_name,
            "message.kind": "event",
            "message.type": type(event).__qualname__,
            "message.module": type(event).__module__,
            "handler.type": type(handler).__qualname__,
            "handler.module": type(handler).__module__,
        }