from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any

from direttore.orchestration.tracing.ports import TraceResolverPort, TraceSpanPort, TraceSpanFactoryPort


class NoopTraceResolver(TraceResolverPort[Any, Any]):
    """
    Trace resolver used when tracing is disabled.

    It accepts any trace input and always returns None. This allows Direttore
    and engines to keep tracing optional without requiring every application to
    configure tracing.
    """

    def resolve_trace(
        self,
        trace_input: Any | None,
    ) -> Any | None:
        return None


class NoopTraceSpan(TraceSpanPort):
    """
    No-op span implementation.

    It satisfies TraceSpanPort but records nothing. It is useful as a safe
    default when tracing is disabled or when code wants to avoid repeated
    conditional checks around span creation.
    """

    async def __aenter__(self) -> TraceSpanPort:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None

    def add_event(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        return None

    def set_attribute(
        self,
        key: str,
        value: Any,
    ) -> None:
        return None


class NoopTraceSpanFactory(TraceSpanFactoryPort[Any]):
    """
    Span factory used when tracing is disabled.

    It always returns NoopTraceSpan. This lets framework components open spans
    unconditionally if they want a simpler execution path.
    """

    def start_span(
        self,
        *,
        trace: Any | None,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        return NoopTraceSpan()