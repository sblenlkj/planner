"""DEPRECATED - use tracing_tree instead"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from direttore.orchestration.tracing import (
    TraceResolverPort,
    TraceSpanFactoryPort,
    TraceSpanPort,
)


@dataclass(slots=True)
class RecordedTraceEvent:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RecordedTraceSpan:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[RecordedTraceEvent] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    ended: bool = False


@dataclass(slots=True)
class InMemoryTrace:
    spans: list[RecordedTraceSpan] = field(default_factory=list)


class InMemoryTraceResolver(
    TraceResolverPort[InMemoryTrace, InMemoryTrace],
):
    """
    Fake trace resolver.

    If trace_input is provided, it returns the same InMemoryTrace object.
    If trace_input is None, it creates a new InMemoryTrace.
    """

    def resolve_trace(
        self,
        trace_input: InMemoryTrace | None,
    ) -> InMemoryTrace:
        return trace_input or InMemoryTrace()


class InMemoryTraceSpan(TraceSpanPort):
    def __init__(
        self,
        *,
        trace: InMemoryTrace,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self._trace = trace
        self._span = RecordedTraceSpan(
            name=name,
            attributes=dict(attributes or {}),
        )

    async def __aenter__(self) -> TraceSpanPort:
        self._trace.spans.append(self._span)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exc_type is not None:
            self._span.error_type = exc_type.__name__

        if exc is not None:
            self._span.error_message = str(exc)

        self._span.ended = True

        return None

    def add_event(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self._span.events.append(
            RecordedTraceEvent(
                name=name,
                attributes=dict(attributes or {}),
            )
        )

    def set_attribute(
        self,
        key: str,
        value: Any,
    ) -> None:
        self._span.attributes[key] = value


class InMemoryTraceSpanFactory(TraceSpanFactoryPort[InMemoryTrace]):
    """
    Fake span factory.

    It appends every opened span to the provided InMemoryTrace. If trace is None,
    it creates an internal temporary InMemoryTrace so the span still works.
    """

    def start_span(
        self,
        *,
        trace: InMemoryTrace | None,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        return InMemoryTraceSpan(
            trace=trace or InMemoryTrace(),
            name=name,
            attributes=attributes,
        )