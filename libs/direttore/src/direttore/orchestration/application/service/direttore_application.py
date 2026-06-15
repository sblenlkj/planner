from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar, Mapping

from direttore.orchestration.application.service.config import (
    ServiceAuthConfig,
    ServiceQueryConfig,
    ServiceTracingConfig,
)
from direttore.orchestration.application.service.execution_slot import (
    ServiceExecutionSlot,
)
from direttore.orchestration.base_classes.execution_resource_holder import (
    ExecutionSessionHolder,
)
from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Command, Query
from direttore.orchestration.engines.command_executor_engines.config import (
    ExecutionEngineConfig,
)
from direttore.orchestration.engines.command_executor_engines.engine import (
    CommandExecutionEngine,
)
from direttore.orchestration.engines.query_executor_engines.engine import (
    QueryExecutionEngine,
)
from direttore.orchestration.event_dispatchers.event_dispatcher import (
    EventDispatcher,
)
from direttore.orchestration.registries.service.command_handler_registry import (
    CommandHandlerRegistry,
)
from direttore.orchestration.registries.service.event_handler_registry import (
    EventHandlerRegistry,
)
from direttore.orchestration.resolvers.container import Container
from direttore.orchestration.resolvers.service.command_handler_resolver import (
    WarmUpCacheAutoWiringCommandHandlerResolver,
)
from direttore.orchestration.resolvers.service.event_handler_resolver import (
    WarmUpCacheAutoWiringEventHandlerResolver,
)
from direttore.orchestration.resolvers.service.query_handler_resolver import (
    QueryHandlerResolverPort,
    WarmUpCacheAutoWiringQueryHandlerResolver,
)


TSession = TypeVar("TSession")

AuthInputT = TypeVar("AuthInputT")
AuthInputContraT = TypeVar("AuthInputContraT", contravariant=True)
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceInputContraT = TypeVar("TraceInputContraT", contravariant=True)
TraceT = TypeVar("TraceT")

TCommandUnitOfWork = TypeVar(
    "TCommandUnitOfWork",
    bound=AbstractCommandUnitOfWork,
)
TQueryUnitOfWork = TypeVar(
    "TQueryUnitOfWork",
    bound=AbstractQueryUnitOfWork,
)


@dataclass(slots=True)
class ActiveServiceSimpleExecutionSlot(
    Generic[AuthInputT, AuthT, TraceInputT, TraceT],
):
    slot: ServiceExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]


@dataclass(slots=True)
class ActiveServiceSessionHolderExecutionSlot(
    Generic[AuthInputT, AuthT, TraceInputT, TraceT],
):
    session_holder: ExecutionSessionHolder[Any]
    slot: ServiceExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]


class ServiceDirettoreApplicationPort(
    Protocol[AuthInputContraT, TraceInputContraT],
):
    def validate_command_handlers(self) -> None:
        raise NotImplementedError

    def validate_query_handlers(self) -> None:
        raise NotImplementedError

    def validate_event_handlers(self) -> None:
        raise NotImplementedError

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputContraT | None = None,
        trace_input: TraceInputContraT | None = None,
    ) -> Any:
        raise NotImplementedError

    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputContraT | None = None,
        trace_input: TraceInputContraT | None = None,
    ) -> Any:
        raise NotImplementedError
    
    async def handle_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputContraT | None = None,
        trace_input: TraceInputContraT | None = None,
    ) -> Any:
        raise NotImplementedError

    async def handle_query_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputContraT | None = None,
        trace_input: TraceInputContraT | None = None,
    ) -> Any:
        raise NotImplementedError


class ServiceDirettoreWithSimpleSession(
    ServiceDirettoreApplicationPort[AuthInputT, TraceInputT],
    Generic[
        TSession,
        TCommandUnitOfWork,
        TQueryUnitOfWork,
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ],
):
    """
    Service-profile Direttore that creates one session per root execution.

    This class is used when one bounded context is executed as a standalone
    service-like application.

    Generic parameters:
        TSession:
            Concrete execution session created by session_factory.
            Example: SQLAlchemy AsyncSession, Django transaction object,
            custom FakeSession.

        TCommandUnitOfWork:
            Concrete command UoW created from TSession and passed to command
            handlers.

        TQueryUnitOfWork:
            Concrete query UoW created from TSession and passed to query
            handlers. If query_config is not provided, query execution is
            disabled.

        AuthInputT:
            External auth input accepted by handle(...).
            Example: HTTP headers, token string, ExampleAuthInput.

        AuthT:
            Resolved auth object stored in handler context.
            Example: ExampleAuth, CurrentUser, AuthContext.

        TraceInputT:
            External trace input accepted by handle(...).
            Example: OpenTelemetry extracted context, trace headers,
            InMemoryTrace.

        TraceT:
            Resolved trace object used by span factory.
            Example: OpenTelemetry trace context wrapper, InMemoryTrace.

    __init__ arguments:
        session_factory:
            Creates a new execution session for each root command/query.

        command_uow_factory:
            Builds command UoW from the created session.

        command_handler_registry:
            Registry of command handlers for this service profile.

        event_handler_registry:
            Registry of event handlers for this service profile.

        container:
            Application container used for handler dependencies.

        auth_config:
            Optional auth/authz capability. If omitted, auth is disabled.

        tracing_config:
            Optional tracing capability. If omitted, tracing is disabled.

        query_config:
            Optional query capability. If omitted, handle_query(...) is disabled.

        execution_engine_config:
            Optional command engine config, for example execution mode and
            event draining limits.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], TSession],
        command_uow_factory: Callable[
            [TSession],
            TCommandUnitOfWork,
        ],
        command_handler_registry: CommandHandlerRegistry,
        event_handler_registry: EventHandlerRegistry,
        container: Container,
        auth_config: ServiceAuthConfig[AuthInputT, AuthT] | None = None,
        tracing_config: ServiceTracingConfig[TraceInputT, TraceT] | None = None,
        query_config: ServiceQueryConfig[TSession, TQueryUnitOfWork]
        | None = None,
        execution_engine_config: ExecutionEngineConfig | None = None,
    ) -> None:
        auth_resolver = (
            auth_config.auth_resolver
            if auth_config is not None
            else None
        )
        access_checker = (
            auth_config.access_checker
            if auth_config is not None
            else None
        )
        trace_resolver = (
            tracing_config.trace_resolver
            if tracing_config is not None
            else None
        )
        trace_span_factory = (
            tracing_config.trace_span_factory
            if tracing_config is not None
            else None
        )

        self._session_factory = session_factory
        self._command_uow_factory = command_uow_factory
        self._query_uow_factory = (
            query_config.query_uow_factory
            if query_config is not None
            else None
        )
        self._trace_resolver = trace_resolver

        self._command_handler_resolver = WarmUpCacheAutoWiringCommandHandlerResolver(
            registry=command_handler_registry,
            container=container,
        )

        self._query_handler_resolver = self._build_query_handler_resolver(
            query_config=query_config,
            container=container,
        )

        event_handler_resolver = WarmUpCacheAutoWiringEventHandlerResolver(
            registry=event_handler_registry,
            container=container,
        )

        self._event_dispatcher = EventDispatcher(
            resolver=event_handler_resolver,
            trace_span_factory=trace_span_factory,
        )

        self._command_engine = CommandExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ](
            event_dispatcher=self._event_dispatcher,
            auth_resolver=auth_resolver,
            access_checker=access_checker,
            config=execution_engine_config,
            trace_span_factory=trace_span_factory,
        )

        self._query_engine = (
            QueryExecutionEngine[
                AuthInputT,
                AuthT,
                TraceT,
            ](
                auth_resolver=auth_resolver,
                access_checker=access_checker,
                trace_span_factory=trace_span_factory,
            )
            if self._query_handler_resolver is not None
            else None
        )

    def validate_command_handlers(self) -> None:
        self._command_handler_resolver.validate_command_handlers()

    def validate_query_handlers(self) -> None:
        if self._query_handler_resolver is None:
            return

        self._query_handler_resolver.validate_query_handlers()

    def validate_event_handlers(self) -> None:
        self._event_dispatcher.validate_event_handlers()

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()

        try:
            return await active_slot.slot.handle(
                command,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()

    async def handle_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()

        try:
            return await active_slot.slot.handle_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()


    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()

        try:
            return await active_slot.slot.handle_query(
                query,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()

    async def handle_query_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()

        try:
            return await active_slot.slot.handle_query_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()

    def _create_active_slot(
        self,
    ) -> ActiveServiceSimpleExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]:
        session = self._session_factory()

        command_uow = self._command_uow_factory(session)
        query_uow = (
            self._query_uow_factory(session)
            if self._query_uow_factory is not None
            else None
        )

        slot = ServiceExecutionSlot[
            AuthInputT,
            AuthT,
            TraceInputT,
            TraceT,
        ](
            command_uow=command_uow,
            query_uow=query_uow,
            command_handler_resolver=self._command_handler_resolver,
            query_handler_resolver=self._query_handler_resolver,
            command_engine=self._command_engine,
            query_engine=self._query_engine,
            trace_resolver=self._trace_resolver,
        )

        return ActiveServiceSimpleExecutionSlot(
            slot=slot,
        )

    def _build_query_handler_resolver(
        self,
        *,
        query_config: ServiceQueryConfig[TSession, TQueryUnitOfWork]
        | None,
        container: Container,
    ) -> QueryHandlerResolverPort | None:
        if query_config is None:
            return None

        return WarmUpCacheAutoWiringQueryHandlerResolver(
            registry=query_config.query_handler_registry,
            container=container,
        )


class ServiceDirettoreWithSessionHolder(
    ServiceDirettoreApplicationPort[AuthInputT, TraceInputT],
    Generic[
        TSession,
        TCommandUnitOfWork,
        TQueryUnitOfWork,
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ],
):
    """
    Service-profile Direttore that exposes the current session through a holder.

    This version is useful when UoW factories or repositories should receive a
    stable holder object first, while the actual session is attached only during
    root execution.

    Generic parameters:
        TSession:
            Concrete execution session attached to ExecutionSessionHolder.

        TCommandUnitOfWork:
            Concrete command UoW created from ExecutionSessionHolder[TSession].

        TQueryUnitOfWork:
            Concrete query UoW created from ExecutionSessionHolder[TSession].
            If query_config is omitted, query execution is disabled.

        AuthInputT:
            External auth input accepted by handle(...).

        AuthT:
            Resolved auth object passed to handlers.

        TraceInputT:
            External trace input accepted by handle(...).

        TraceT:
            Resolved trace object used by span factory.
    
    __init__ arguments:
        session_factory:
            Creates a new concrete session for each root execution.

        command_uow_factory:
            Builds command UoW from ExecutionSessionHolder[TSession].

        command_handler_registry:
            Registry of command handlers.

        event_handler_registry:
            Registry of event handlers.

        container:
            Application container used for handler dependencies.

        auth_config:
            Optional auth/authz capability.

        tracing_config:
            Optional tracing capability.

        query_config:
            Optional query capability. Its factory receives
            ExecutionSessionHolder[TSession].

        execution_engine_config:
            Optional command engine config.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], TSession],
        command_uow_factory: Callable[
            [ExecutionSessionHolder[TSession]],
            TCommandUnitOfWork,
        ],
        command_handler_registry: CommandHandlerRegistry,
        event_handler_registry: EventHandlerRegistry,
        container: Container,
        auth_config: ServiceAuthConfig[AuthInputT, AuthT] | None = None,
        tracing_config: ServiceTracingConfig[TraceInputT, TraceT] | None = None,
        query_config: ServiceQueryConfig[
            ExecutionSessionHolder[TSession],
            TQueryUnitOfWork,
        ]
        | None = None,
        execution_engine_config: ExecutionEngineConfig | None = None,
    ) -> None:
        auth_resolver = (
            auth_config.auth_resolver
            if auth_config is not None
            else None
        )
        access_checker = (
            auth_config.access_checker
            if auth_config is not None
            else None
        )
        trace_resolver = (
            tracing_config.trace_resolver
            if tracing_config is not None
            else None
        )
        trace_span_factory = (
            tracing_config.trace_span_factory
            if tracing_config is not None
            else None
        )

        self._session_factory = session_factory
        self._command_uow_factory = command_uow_factory
        self._query_uow_factory = (
            query_config.query_uow_factory
            if query_config is not None
            else None
        )
        self._trace_resolver = trace_resolver

        self._command_handler_resolver = WarmUpCacheAutoWiringCommandHandlerResolver(
            registry=command_handler_registry,
            container=container,
        )

        self._query_handler_resolver = self._build_query_handler_resolver(
            query_config=query_config,
            container=container,
        )

        event_handler_resolver = WarmUpCacheAutoWiringEventHandlerResolver(
            registry=event_handler_registry,
            container=container,
        )

        self._event_dispatcher = EventDispatcher(
            resolver=event_handler_resolver,
            trace_span_factory=trace_span_factory,
        )

        self._command_engine = CommandExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ](
            event_dispatcher=self._event_dispatcher,
            auth_resolver=auth_resolver,
            access_checker=access_checker,
            config=execution_engine_config,
            trace_span_factory=trace_span_factory,
        )

        self._query_engine = (
            QueryExecutionEngine[
                AuthInputT,
                AuthT,
                TraceT,
            ](
                auth_resolver=auth_resolver,
                access_checker=access_checker,
                trace_span_factory=trace_span_factory,
            )
            if self._query_handler_resolver is not None
            else None
        )

    def validate_command_handlers(self) -> None:
        self._command_handler_resolver.validate_command_handlers()

    def validate_query_handlers(self) -> None:
        if self._query_handler_resolver is None:
            return

        self._query_handler_resolver.validate_query_handlers()

    def validate_event_handlers(self) -> None:
        self._event_dispatcher.validate_event_handlers()

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()
        session = self._session_factory()

        active_slot.session_holder.attach(session)

        try:
            return await active_slot.slot.handle(
                command,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()
            active_slot.session_holder.detach()

    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()
        session = self._session_factory()

        active_slot.session_holder.attach(session)

        try:
            return await active_slot.slot.handle_query(
                query,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()
            active_slot.session_holder.detach()

    def _create_active_slot(
        self,
    ) -> ActiveServiceSessionHolderExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]:
        session_holder = ExecutionSessionHolder()

        command_uow = self._command_uow_factory(session_holder)
        query_uow = (
            self._query_uow_factory(session_holder)
            if self._query_uow_factory is not None
            else None
        )

        slot = ServiceExecutionSlot[
            AuthInputT,
            AuthT,
            TraceInputT,
            TraceT,
        ](
            command_uow=command_uow,
            query_uow=query_uow,
            command_handler_resolver=self._command_handler_resolver,
            query_handler_resolver=self._query_handler_resolver,
            command_engine=self._command_engine,
            query_engine=self._query_engine,
            trace_resolver=self._trace_resolver,
        )

        return ActiveServiceSessionHolderExecutionSlot(
            session_holder=session_holder,
            slot=slot,
        )

    def _build_query_handler_resolver(
        self,
        *,
        query_config: ServiceQueryConfig[
            ExecutionSessionHolder[TSession],
            TQueryUnitOfWork,
        ]
        | None,
        container: Container,
    ) -> QueryHandlerResolverPort | None:
        if query_config is None:
            return None

        return WarmUpCacheAutoWiringQueryHandlerResolver(
            registry=query_config.query_handler_registry,
            container=container,
        )
