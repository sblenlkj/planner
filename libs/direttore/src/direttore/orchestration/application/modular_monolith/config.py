from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from direttore.orchestration.auth import (
    AccessCheckerPort,
)
from direttore.orchestration.tracing import (
    TraceResolverPort,
    TraceSpanFactoryPort,
)


AuthInputT = TypeVar("AuthInputT")
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceT = TypeVar("TraceT")


@dataclass(frozen=True, slots=True)
class ModularAuthConfig(Generic[AuthInputT, AuthT]):
    """
    Authentication and authorization configuration for modular-monolith execution.

    Current modular behavior:
        - access_checker is configured directly on Direttore;
        - auth resolver is usually resolved as an execution dependency through
          ModularMonolithExecutionDependencyRegistry.

    Generic parameters:
        AuthInputT:
            External auth input accepted by Direttore.handle(...).
            It is kept here for type symmetry with Direttore generics, even
            though ModularAuthConfig currently stores only access_checker.

        AuthT:
            Resolved auth object used by access checker, runtime and handler
            contexts.

    Why auth_resolver is not stored here:
        In modular mode auth resolver often needs the current execution runtime
        or other execution-scoped dependencies. Because of that, it is usually
        registered in ModularMonolithExecutionDependencyRegistry and resolved
        per execution slot.

    If this config is not provided, modular Direttore runs without access checks.
    """

    access_checker: AccessCheckerPort[AuthT]


@dataclass(frozen=True, slots=True)
class ModularTracingConfig(Generic[TraceInputT, TraceT]):
    """
    Tracing configuration for modular-monolith execution.

    Generic parameters:
        TraceInputT:
            External trace input accepted by Direttore.handle(...).
            Example: OpenTelemetry context extracted by an endpoint,
            trace headers, InMemoryTrace in tests.

        TraceT:
            Resolved execution trace object used by TraceSpanFactoryPort.

    The same trace object is attached to ModularMonolithExecutionRuntime, so
    runtime-bound in-process clients can keep nested calls in the same trace.
    """

    trace_resolver: TraceResolverPort[TraceInputT, TraceT]
    trace_span_factory: TraceSpanFactoryPort[TraceT]
