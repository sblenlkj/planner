from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from direttore.orchestration.auth import (
    AccessCheckerPort,
    AuthResolverPort,
)
from direttore.orchestration.base_classes.execution_resource_holder import (
    ExecutionSessionHolder,
)
from direttore.orchestration.base_classes.uow import (
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.registries.service.query_handler_registry import (
    QueryHandlerRegistry,
)
from direttore.orchestration.tracing import (
    TraceResolverPort,
    TraceSpanFactoryPort,
)


TSession = TypeVar("TSession")
TQueryFactoryInput = TypeVar("TQueryFactoryInput")
TQueryUnitOfWork = TypeVar(
    "TQueryUnitOfWork",
    bound=AbstractQueryUnitOfWork,
)

AuthInputT = TypeVar("AuthInputT")
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceT = TypeVar("TraceT")


@dataclass(frozen=True, slots=True)
class ServiceAuthConfig(Generic[AuthInputT, AuthT]):
    """
    Authentication and authorization configuration for service execution.

    Service mode resolves auth directly inside command/query engines.

    Generic parameters:
        AuthInputT:
            External auth input accepted by Direttore.handle(...).
            Example: HTTP headers, token string, user session object,
            ExampleAuthInput.

        AuthT:
            Resolved auth object passed to handlers and access checker.
            Example: ExampleAuth, CurrentUser, RequestAuthContext.

    If this config is not provided, service Direttore runs without auth.
    In that case auth_input must not be passed to handle(...) / handle_query(...),
    and registered handlers must not require allowed access tags.
    """

    auth_resolver: AuthResolverPort[AuthInputT, AuthT]
    access_checker: AccessCheckerPort[AuthT]


@dataclass(frozen=True, slots=True)
class ServiceTracingConfig(Generic[TraceInputT, TraceT]):
    """
    Tracing configuration for service execution.

    Generic parameters:
        TraceInputT:
            External trace input accepted by Direttore.handle(...).
            Example: HTTP tracing headers, OpenTelemetry context,
            InMemoryTrace in tests.

        TraceT:
            Resolved execution trace object used by TraceSpanFactoryPort.
            Example: OpenTelemetry context wrapper, InMemoryTrace.

    If this config is not provided, service Direttore runs without tracing.
    In that case trace_input must not be passed to handle(...) / handle_query(...).
    """

    trace_resolver: TraceResolverPort[TraceInputT, TraceT]
    trace_span_factory: TraceSpanFactoryPort[TraceT]


@dataclass(frozen=True, slots=True)
class ServiceQueryConfig(Generic[TQueryFactoryInput, TQueryUnitOfWork]):
    """
    Query support configuration for service execution.

    Generic parameters:
        TQueryFactoryInput:
            Input accepted by query_uow_factory.

            For ServiceDirettoreWithSimpleSession this is usually TSession.

            For ServiceDirettoreWithSessionHolder this is usually
            ExecutionSessionHolder[TSession].

        TQueryUnitOfWork:
            Concrete query UoW used by query handlers.

    If this config is not provided, handle_query(...) is disabled.
    """

    query_handler_registry: QueryHandlerRegistry
    query_uow_factory: Callable[[TQueryFactoryInput], TQueryUnitOfWork]


ServiceSimpleQueryConfig = ServiceQueryConfig[TSession, TQueryUnitOfWork]
ServiceSessionHolderQueryConfig = ServiceQueryConfig[
    ExecutionSessionHolder[TSession],
    TQueryUnitOfWork,
]
