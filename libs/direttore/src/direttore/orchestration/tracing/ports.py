from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, Protocol, TypeVar


TraceInputContraT = TypeVar("TraceInputContraT", contravariant=True)
TraceCovaT = TypeVar("TraceCovaT", covariant=True)
TraceContraT = TypeVar("TraceContraT", contravariant=True)


class TraceResolverPort(Protocol[TraceInputContraT, TraceCovaT]):
    """
    Resolves external trace input into an execution trace object.

    This port is the tracing analogue of AuthResolverPort:

        trace_input -> TraceResolverPort.resolve_trace(...) -> trace

    The trace input is provided by the caller of Direttore.handle(...) or
    Direttore.handle_query(...). It can be anything the final application needs:

        - HTTP headers containing distributed tracing context;
        - OpenTelemetry context extracted by an endpoint;
        - an existing in-memory trace object in tests;
        - None, when tracing starts from a new root execution.

    The resolved trace object is also application-specific. For OpenTelemetry it
    can be a context/span wrapper. For tests it can be an in-memory trace model.
    The framework stores the resolved trace on the current execution/runtime and
    passes it to TraceSpanFactoryPort when it needs to open framework-level
    spans.
    """

    def resolve_trace(
        self,
        trace_input: TraceInputContraT | None,
    ) -> TraceCovaT | None:
        raise NotImplementedError


class TraceSpanPort(Protocol):
    """
    Minimal async span protocol used by the orchestration framework.

    A span represents one measured operation in the execution pipeline, for
    example:

        - command execution;
        - query execution;
        - command handler call;
        - event dispatch;
        - event handler call;
        - modular runtime.invoke(...);
        - modular runtime.invoke_query(...).

    Implementations may wrap OpenTelemetry spans, custom tracing spans, or fake
    spans used in tests.

    The span is an async context manager because the framework execution path is
    async. Implementations may record errors in __aexit__, set attributes, and
    add events.
    """

    async def __aenter__(self) -> TraceSpanPort:
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        raise NotImplementedError

    def add_event(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        raise NotImplementedError

    def set_attribute(
        self,
        key: str,
        value: Any,
    ) -> None:
        raise NotImplementedError


class TraceSpanFactoryPort(Protocol[TraceContraT]):
    """
    Creates spans from the resolved execution trace object.

    TraceResolverPort only resolves trace input. This factory is responsible for
    opening spans around framework operations.

    This split mirrors the auth model:

        AuthResolverPort:
            resolves auth_input into auth.

        AccessCheckerPort:
            performs access checks using resolved auth.

        TraceResolverPort:
            resolves trace_input into trace.

        TraceSpanFactoryPort:
            opens spans using resolved trace.

    For OpenTelemetry, this factory can call start_as_current_span(...) and rely
    on OpenTelemetry context propagation. For tests, it can append span records
    to an in-memory trace object.

    The trace argument may be None. Implementations should either create a new
    root trace/span, use a no-op span, or apply their own application-specific
    default behavior.
    """

    def start_span(
        self,
        *,
        trace: TraceContraT | None,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        raise NotImplementedError