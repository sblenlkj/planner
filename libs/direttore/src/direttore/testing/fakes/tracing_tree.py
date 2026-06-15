from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any
from uuid import uuid4

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
    """
    In-memory span representation.

    The span is stored in two forms at once:
    1. InMemoryTrace.spans      -- flat append-only list, useful for old tests and chronological inspection.
    2. InMemoryTrace.root_spans -- tree roots; each span can contain children.

    parent_span_id is intentionally duplicated with children:
    - children is convenient for pretty printing and nested JSON;
    - parent_span_id is convenient for flat export and debugging.
    """

    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[RecordedTraceEvent] = field(default_factory=list)
    children: list["RecordedTraceSpan"] = field(default_factory=list)
    span_id: str = field(default_factory=lambda: uuid4().hex)
    parent_span_id: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    ended: bool = False

    def to_dict(self, *, include_children: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "attributes": dict(self.attributes),
            "events": [
                {
                    "name": event.name,
                    "attributes": dict(event.attributes),
                }
                for event in self.events
            ],
            "error_type": self.error_type,
            "error_message": self.error_message,
            "ended": self.ended,
        }

        if include_children:
            data["children"] = [
                child.to_dict(include_children=True)
                for child in self.children
            ]

        return data


@dataclass(slots=True)
class InMemoryTrace:
    """
    Test/in-memory trace.

    spans:
        Flat chronological list of all opened spans.
        Keep this for compatibility with the previous implementation.

    root_spans:
        Tree roots. In a normal single request there will be one root span.
        If the same trace object is reused for several independent executions,
        there may be several roots.

    _stack:
        Internal active-span stack used by InMemoryTraceSpan.
        Framework code should not touch it directly.
    """

    spans: list[RecordedTraceSpan] = field(default_factory=list)
    root_spans: list[RecordedTraceSpan] = field(default_factory=list)
    _stack: list[RecordedTraceSpan] = field(default_factory=list, repr=False)

    def to_flat_list(self) -> list[dict[str, Any]]:
        return [
            span.to_dict(include_children=False)
            for span in self.spans
        ]

    def to_tree_list(self) -> list[dict[str, Any]]:
        return [
            span.to_dict(include_children=True)
            for span in self.root_spans
        ]


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
        parent = self._trace._stack[-1] if self._trace._stack else None

        if parent is None:
            self._trace.root_spans.append(self._span)
        else:
            self._span.parent_span_id = parent.span_id
            parent.children.append(self._span)

        # Keep the old flat chronological view as well.
        self._trace.spans.append(self._span)

        # Push after attaching to parent so nested spans can attach to this one.
        self._trace._stack.append(self._span)

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

        if not self._trace._stack:
            self._span.error_type = self._span.error_type or "TraceStackError"
            self._span.error_message = (
                self._span.error_message
                or "Cannot close trace span because active span stack is empty."
            )
            self._span.ended = True
            return None

        current = self._trace._stack.pop()

        if current is not self._span:
            self._span.error_type = self._span.error_type or "TraceStackError"
            self._span.error_message = (
                self._span.error_message
                or (
                    "Trace span stack is corrupted. "
                    f"Expected to close span_id={self._span.span_id!r}, "
                    f"but active span_id={current.span_id!r} was on top."
                )
            )

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

    It records spans in two shapes:
    - trace.spans as a flat chronological list;
    - trace.root_spans + span.children as a tree.

    If trace is None, it creates an internal temporary InMemoryTrace so the span
    still behaves as a no-output in-memory span.
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

def print_span_tree(span, indent: int = 0) -> None:
    prefix = "  " * indent
    error = f" ERROR={span.error_type}" if span.error_type else ""
    print(f"{prefix}- {span.name}{error}")

    for child in span.children:
        print_span_tree(child, indent + 1)


def print_trace_tree(trace) -> None:
    for root in trace.root_spans:
        print_span_tree(root)