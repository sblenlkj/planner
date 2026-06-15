from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar, Mapping

from direttore.orchestration.application.modular_monolith.config import (
    ModularAuthConfig,
    ModularTracingConfig,
)
from direttore.orchestration.application.modular_monolith.execution_slot import (
    ModularMonolithExecutionSlot,
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
from direttore.orchestration.engines.command_executor_engines.modular_engine import (
    ModularMonolithCommandExecutionEngine,
)
from direttore.orchestration.engines.query_executor_engines.modular_engine import (
    ModularMonolithQueryExecutionEngine,
)
from direttore.orchestration.event_dispatchers.modular_event_dispatcher import (
    ModularMonolithEventDispatcher,
)
from direttore.orchestration.modular_monolith.coordinator import (
    ModularUnitOfWorkCoordinator,
)
from direttore.orchestration.modular_monolith.execution_dependencies import (
    ModularMonolithExecutionDependencyRegistry,
)
from direttore.orchestration.registries.modular_monolith.modular_command_handler_registry import (
    ModularMonolithCommandHandlerRegistry,
)
from direttore.orchestration.registries.modular_monolith.modular_event_handler_registry import (
    ModularMonolithEventHandlerRegistry,
)
from direttore.orchestration.registries.modular_monolith.modular_query_handler_registry import (
    ModularMonolithQueryHandlerRegistry,
)
from direttore.orchestration.registries.service.command_handler_registry import (
    CommandHandlerRegistry,
)
from direttore.orchestration.registries.service.event_handler_registry import (
    EventHandlerRegistry,
)
from direttore.orchestration.registries.service.query_handler_registry import (
    QueryHandlerRegistry,
)
from direttore.orchestration.resolvers.container import Container
from direttore.orchestration.resolvers.modular_monolith.modular_command_handler_resolver import (
    ModularMonolithCommandHandlerResolver,
)
from direttore.orchestration.resolvers.modular_monolith.modular_query_handler_resolver import (
    ModularMonolithQueryHandlerResolver,
)
from direttore.orchestration.resolvers.service.command_handler_resolver import (
    WarmUpCacheAutoWiringCommandHandlerResolver,
)
from direttore.orchestration.resolvers.service.event_handler_resolver import (
    WarmUpCacheAutoWiringEventHandlerResolver,
)
from direttore.orchestration.resolvers.service.query_handler_resolver import (
    WarmUpCacheAutoWiringQueryHandlerResolver,
)


TSession = TypeVar("TSession")

AuthInputT = TypeVar("AuthInputT")
AuthInputContraT = TypeVar("AuthInputContraT", contravariant=True)
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceInputContraT = TypeVar("TraceInputContraT", contravariant=True)
TraceT = TypeVar("TraceT")


@dataclass(frozen=True, slots=True)
class ModularDirettoreContext:
    command_handler_registry: CommandHandlerRegistry
    event_handler_registry: EventHandlerRegistry
    command_root_uow_type: type[AbstractCommandUnitOfWork]
    query_handler_registry: QueryHandlerRegistry | None = None
    query_root_uow_type: type[AbstractQueryUnitOfWork] | None = None

    def __post_init__(self) -> None:
        if (
            self.query_handler_registry is not None
            and self.query_root_uow_type is None
        ):
            raise RuntimeError(
                "query_handler_registry was provided, but query_root_uow_type "
                "is not configured."
            )

        if (
            self.query_handler_registry is None
            and self.query_root_uow_type is not None
        ):
            raise RuntimeError(
                "query_root_uow_type was provided, but query_handler_registry "
                "is not configured."
            )


@dataclass(slots=True)
class ActiveModularMonolithSessionHolderExecutionSlot(
    Generic[AuthInputT, AuthT, TraceInputT, TraceT],
):
    session_holder: ExecutionSessionHolder[Any]
    slot: ModularMonolithExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]


class ModularMonolithDirettoreApplicationPort(
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


class ModularDirettoreWithSimpleSession(
    ModularMonolithDirettoreApplicationPort[AuthInputT, TraceInputT],
    Generic[TSession, AuthInputT, AuthT, TraceInputT, TraceT],
):
    """
    Modular-monolith Direttore that creates one concrete session per root execution.

    This class composes multiple service-shaped bounded contexts into one
    in-process modular-monolith runtime.

    Generic parameters:
        TSession:
            Concrete execution session created by session_factory.
            In the current modular v1 model this is usually one shared session
            for all context UoWs participating in a root execution.

        AuthInputT:
            External auth input accepted by handle(...).
            Example: ExampleAuthInput, request auth data.

        AuthT:
            Resolved auth object used by access checker, runtime.invoke(...),
            and handler contexts.

        TraceInputT:
            External trace input accepted by handle(...).

        TraceT:
            Resolved trace object attached to the modular runtime and used by
            command/query engines, event dispatcher, runtime.invoke(...) and
            runtime.invoke_query(...).

    __init__ arguments:
        session_factory:
            Creates one concrete session per root command/query.

        coordinator_factory:
            Builds ModularUnitOfWorkCoordinator from the created session.

        contexts:
            Bounded context descriptors. Each context provides service registries
            and root UoW types for command/query execution.

        container:
            Application container used for regular handler dependencies.

        execution_dependency_registry:
            Optional registry for execution-scoped dependencies. This is how
            in-process clients and modular auth resolvers usually receive the
            current ModularMonolithExecutionRuntime.

        execution_engine_config:
            Optional command engine config.

        auth_config:
            Optional auth/authz capability. In modular mode it currently stores
            access_checker. AuthResolverPort is usually provided through
            execution_dependency_registry.

        tracing_config:
            Optional tracing capability.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], TSession],
        coordinator_factory: Callable[
            [TSession],
            ModularUnitOfWorkCoordinator,
        ],
        contexts: Sequence[ModularDirettoreContext],
        container: Container,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ) = None,
        execution_engine_config: ExecutionEngineConfig | None = None,
        auth_config: ModularAuthConfig[AuthInputT, AuthT] | None = None,
        tracing_config: ModularTracingConfig[TraceInputT, TraceT]
        | None = None,
    ) -> None:
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

        modular_command_handler_registry = (
            ModularMonolithCommandHandlerRegistry.from_registries(
                (
                    (
                        context.command_handler_registry,
                        context.command_root_uow_type,
                    )
                    for context in contexts
                ),
                source_name="modular_monolith",
            )
        )

        modular_query_handler_registry = self._build_modular_query_registry(
            contexts=contexts,
        )

        modular_event_handler_registry = (
            ModularMonolithEventHandlerRegistry.from_registries(
                (
                    (
                        context.event_handler_registry,
                        context.command_root_uow_type,
                    )
                    for context in contexts
                ),
                source_name="modular_monolith",
            )
        )

        execution_dependency_types = self._get_execution_dependency_types(
            execution_dependency_registry
        )

        base_command_handler_resolver = WarmUpCacheAutoWiringCommandHandlerResolver(
            registry=modular_command_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._query_handler_resolver = self._build_query_handler_resolver(
            modular_query_handler_registry=modular_query_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._command_handler_resolver = ModularMonolithCommandHandlerResolver(
            command_handler_resolver=base_command_handler_resolver,
            registry=modular_command_handler_registry,
        )

        self._event_handler_resolver = WarmUpCacheAutoWiringEventHandlerResolver(
            registry=modular_event_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._session_factory = session_factory
        self._coordinator_factory = coordinator_factory
        self._execution_dependency_registry = execution_dependency_registry
        self._access_checker = access_checker
        self._trace_resolver = trace_resolver
        self._trace_span_factory = trace_span_factory

        event_dispatcher = ModularMonolithEventDispatcher(
            resolver=self._event_handler_resolver,
            registry=modular_event_handler_registry,
            trace_span_factory=self._trace_span_factory,
        )

        self._command_engine = ModularMonolithCommandExecutionEngine(
            event_dispatcher=event_dispatcher,
            config=execution_engine_config,
            access_checker=self._access_checker,
            trace_span_factory=self._trace_span_factory,
        )

        self._query_engine = (
            ModularMonolithQueryExecutionEngine(
                access_checker=self._access_checker,
                trace_span_factory=self._trace_span_factory,
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
        self._event_handler_resolver.validate_event_handlers()

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        session = self._session_factory()
        coordinator = self._coordinator_factory(session)
        slot = self._create_slot(coordinator)

        try:
            return await slot.handle(
                command,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            slot.reset()

    async def handle_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        session = self._session_factory()
        coordinator = self._coordinator_factory(session)
        slot = self._create_slot(coordinator)

        try:
            return await slot.handle_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            slot.reset()

    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        session = self._session_factory()
        coordinator = self._coordinator_factory(session)
        slot = self._create_slot(coordinator)

        try:
            return await slot.handle_query(
                query,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            slot.reset()


    async def handle_query_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        session = self._session_factory()
        coordinator = self._coordinator_factory(session)
        slot = self._create_slot(coordinator)

        try:
            return await slot.handle_query_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            slot.reset()

    def _create_slot(
        self,
        coordinator: ModularUnitOfWorkCoordinator,
    ) -> ModularMonolithExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]:
        return ModularMonolithExecutionSlot(
            coordinator=coordinator,
            command_engine=self._command_engine,
            query_engine=self._query_engine,
            command_handler_resolver=self._command_handler_resolver,
            query_handler_resolver=self._query_handler_resolver,
            execution_dependency_registry=self._execution_dependency_registry,
            access_checker=self._access_checker,
            trace_resolver=self._trace_resolver,
            trace_span_factory=self._trace_span_factory,
        )

    def _build_modular_query_registry(
        self,
        *,
        contexts: Sequence[ModularDirettoreContext],
    ) -> ModularMonolithQueryHandlerRegistry | None:
        query_contexts = [
            (
                context.query_handler_registry,
                context.query_root_uow_type,
            )
            for context in contexts
            if context.query_handler_registry is not None
            and context.query_root_uow_type is not None
        ]

        if not query_contexts:
            return None

        return ModularMonolithQueryHandlerRegistry.from_registries(
            query_contexts,
            source_name="modular_monolith",
        )

    def _build_query_handler_resolver(
        self,
        *,
        modular_query_handler_registry: ModularMonolithQueryHandlerRegistry | None,
        container: Container,
        execution_dependency_types: set[type[Any]],
    ) -> ModularMonolithQueryHandlerResolver | None:
        if modular_query_handler_registry is None:
            return None

        base_query_handler_resolver = WarmUpCacheAutoWiringQueryHandlerResolver(
            registry=modular_query_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        return ModularMonolithQueryHandlerResolver(
            query_handler_resolver=base_query_handler_resolver,
            registry=modular_query_handler_registry,
        )

    def _get_execution_dependency_types(
        self,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ),
    ) -> set[type[Any]]:
        if execution_dependency_registry is None:
            return set()

        return set(execution_dependency_registry.iter_dependency_types())


class ModularDirettoreWithSessionHolder(
    ModularMonolithDirettoreApplicationPort[AuthInputT, TraceInputT],
    Generic[TSession, AuthInputT, AuthT, TraceInputT, TraceT],
):
    """
    Modular-monolith Direttore that exposes the current session through a holder.

    This is the preferred modular profile when UoW factories, repositories or
    in-process dependencies should receive a stable holder object while the
    concrete session is attached only during root execution.

    Generic parameters:
        TSession:
            Concrete execution session attached to ExecutionSessionHolder.

        AuthInputT:
            External auth input accepted by handle(...).

        AuthT:
            Resolved auth object used by access checker, runtime and handler
            contexts.

        TraceInputT:
            External trace input accepted by handle(...).

        TraceT:
            Resolved trace object attached to runtime and used by span factory.
    
    __init__ arguments:
        session_factory:
            Creates one concrete session per root command/query.

        coordinator_factory:
            Builds ModularUnitOfWorkCoordinator from
            ExecutionSessionHolder[TSession].

        contexts:
            Bounded context descriptors.

        container:
            Application container used for regular handler dependencies.

        execution_dependency_registry:
            Optional execution-scoped dependency registry. This is the main
            extension point for in-process clients and modular auth resolvers.

        execution_engine_config:
            Optional command engine config.

        auth_config:
            Optional auth/authz capability.

        tracing_config:
            Optional tracing capability.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], TSession],
        coordinator_factory: Callable[
            [ExecutionSessionHolder[TSession]],
            ModularUnitOfWorkCoordinator,
        ],
        contexts: Sequence[ModularDirettoreContext],
        container: Container,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ) = None,
        execution_engine_config: ExecutionEngineConfig | None = None,
        auth_config: ModularAuthConfig[AuthInputT, AuthT] | None = None,
        tracing_config: ModularTracingConfig[TraceInputT, TraceT]
        | None = None,
    ) -> None:
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

        modular_command_handler_registry = (
            ModularMonolithCommandHandlerRegistry.from_registries(
                (
                    (
                        context.command_handler_registry,
                        context.command_root_uow_type,
                    )
                    for context in contexts
                ),
                source_name="modular_monolith",
            )
        )

        modular_query_handler_registry = self._build_modular_query_registry(
            contexts=contexts,
        )

        modular_event_handler_registry = (
            ModularMonolithEventHandlerRegistry.from_registries(
                (
                    (
                        context.event_handler_registry,
                        context.command_root_uow_type,
                    )
                    for context in contexts
                ),
                source_name="modular_monolith",
            )
        )

        execution_dependency_types = self._get_execution_dependency_types(
            execution_dependency_registry
        )

        base_command_handler_resolver = WarmUpCacheAutoWiringCommandHandlerResolver(
            registry=modular_command_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._query_handler_resolver = self._build_query_handler_resolver(
            modular_query_handler_registry=modular_query_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._command_handler_resolver = ModularMonolithCommandHandlerResolver(
            command_handler_resolver=base_command_handler_resolver,
            registry=modular_command_handler_registry,
        )

        self._event_handler_resolver = WarmUpCacheAutoWiringEventHandlerResolver(
            registry=modular_event_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        self._session_factory = session_factory
        self._coordinator_factory = coordinator_factory
        self._execution_dependency_registry = execution_dependency_registry
        self._access_checker = access_checker
        self._trace_resolver = trace_resolver
        self._trace_span_factory = trace_span_factory

        event_dispatcher = ModularMonolithEventDispatcher(
            resolver=self._event_handler_resolver,
            registry=modular_event_handler_registry,
            trace_span_factory=self._trace_span_factory,
        )

        self._command_engine = ModularMonolithCommandExecutionEngine(
            event_dispatcher=event_dispatcher,
            config=execution_engine_config,
            access_checker=self._access_checker,
            trace_span_factory=self._trace_span_factory,
        )

        self._query_engine = (
            ModularMonolithQueryExecutionEngine(
                access_checker=self._access_checker,
                trace_span_factory=self._trace_span_factory,
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
        self._event_handler_resolver.validate_event_handlers()

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


    async def handle_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()
        session = self._session_factory()

        active_slot.session_holder.attach(session)

        try:
            return await active_slot.slot.handle_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()
            active_slot.session_holder.detach()

    async def handle_query_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        active_slot = self._create_active_slot()
        session = self._session_factory()

        active_slot.session_holder.attach(session)

        try:
            return await active_slot.slot.handle_query_by_key(
                key,
                payload,
                auth_input=auth_input,
                trace_input=trace_input,
            )
        finally:
            active_slot.slot.reset()
            active_slot.session_holder.detach()

    def _create_active_slot(
        self,
    ) -> ActiveModularMonolithSessionHolderExecutionSlot[
        AuthInputT,
        AuthT,
        TraceInputT,
        TraceT,
    ]:
        session_holder = ExecutionSessionHolder()
        coordinator = self._coordinator_factory(session_holder)

        slot = ModularMonolithExecutionSlot(
            coordinator=coordinator,
            command_engine=self._command_engine,
            query_engine=self._query_engine,
            command_handler_resolver=self._command_handler_resolver,
            query_handler_resolver=self._query_handler_resolver,
            execution_dependency_registry=self._execution_dependency_registry,
            access_checker=self._access_checker,
            trace_resolver=self._trace_resolver,
            trace_span_factory=self._trace_span_factory,
        )

        return ActiveModularMonolithSessionHolderExecutionSlot(
            session_holder=session_holder,
            slot=slot,
        )

    def _build_modular_query_registry(
        self,
        *,
        contexts: Sequence[ModularDirettoreContext],
    ) -> ModularMonolithQueryHandlerRegistry | None:
        query_contexts = [
            (
                context.query_handler_registry,
                context.query_root_uow_type,
            )
            for context in contexts
            if context.query_handler_registry is not None
            and context.query_root_uow_type is not None
        ]

        if not query_contexts:
            return None

        return ModularMonolithQueryHandlerRegistry.from_registries(
            query_contexts,
            source_name="modular_monolith",
        )

    def _build_query_handler_resolver(
        self,
        *,
        modular_query_handler_registry: ModularMonolithQueryHandlerRegistry | None,
        container: Container,
        execution_dependency_types: set[type[Any]],
    ) -> ModularMonolithQueryHandlerResolver | None:
        if modular_query_handler_registry is None:
            return None

        base_query_handler_resolver = WarmUpCacheAutoWiringQueryHandlerResolver(
            registry=modular_query_handler_registry,
            container=container,
            execution_dependency_types=execution_dependency_types,
        )

        return ModularMonolithQueryHandlerResolver(
            query_handler_resolver=base_query_handler_resolver,
            registry=modular_query_handler_registry,
        )

    def _get_execution_dependency_types(
        self,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ),
    ) -> set[type[Any]]:
        if execution_dependency_registry is None:
            return set()

        return set(execution_dependency_registry.iter_dependency_types())
