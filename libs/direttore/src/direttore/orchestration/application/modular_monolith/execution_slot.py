from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, cast, Mapping

from direttore.orchestration.auth import (
    AccessCheckerPort,
    AuthResolverPort,
)
from direttore.orchestration.base_types.message import Command, Query
from direttore.orchestration.engines.command_executor_engines.modular_engine import (
    ModularMonolithCommandExecutionEngine,
)
from direttore.orchestration.engines.query_executor_engines.modular_engine import (
    ModularMonolithQueryExecutionEngine,
)
from direttore.orchestration.event_queue import EventQueue
from direttore.orchestration.modular_monolith.coordinator import (
    ModularUnitOfWorkCoordinator,
)
from direttore.orchestration.modular_monolith.execution_dependencies import (
    ModularMonolithExecutionDependencyContext,
    ModularMonolithExecutionDependencyRegistry,
)
from direttore.orchestration.modular_monolith.execution_runtime import (
    ModularMonolithExecutionRuntime,
)
from direttore.orchestration.resolvers.modular_monolith.modular_command_handler_resolver import (
    ModularMonolithCommandHandlerResolver,
)
from direttore.orchestration.resolvers.modular_monolith.modular_query_handler_resolver import (
    ModularMonolithQueryHandlerResolver,
)
from direttore.orchestration.tracing import (
    TraceResolverPort,
    TraceSpanFactoryPort,
)


AuthInputT = TypeVar("AuthInputT")
AuthInputContraT = TypeVar("AuthInputContraT", contravariant=True)
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceInputContraT = TypeVar("TraceInputContraT", contravariant=True)
TraceT = TypeVar("TraceT")


class ModularMonolithExecutionSlotPort(
    Protocol[AuthInputContraT, TraceInputContraT],
):
    async def handle(
        self,
        command: Command,
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

    async def handle_query(
        self,
        query: Query,
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

    def reset(self) -> None:
        raise NotImplementedError


class ModularMonolithExecutionSlot(
    ModularMonolithExecutionSlotPort[AuthInputT, TraceInputT],
    Generic[AuthInputT, AuthT, TraceInputT, TraceT],
):
    def __init__(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        command_engine: ModularMonolithCommandExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ],
        command_handler_resolver: ModularMonolithCommandHandlerResolver,
        query_engine: ModularMonolithQueryExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ]
        | None = None,
        query_handler_resolver: ModularMonolithQueryHandlerResolver | None = None,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ) = None,
        access_checker: AccessCheckerPort[AuthT] | None = None,
        trace_resolver: TraceResolverPort[TraceInputT, TraceT] | None = None,
        trace_span_factory: TraceSpanFactoryPort[TraceT] | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._command_engine = command_engine
        self._query_engine = query_engine
        self._command_handler_resolver = command_handler_resolver
        self._query_handler_resolver = query_handler_resolver
        self._event_queue = EventQueue()
        self._access_checker = access_checker
        self._trace_resolver = trace_resolver
        self._trace_span_factory = trace_span_factory

        self._runtime = ModularMonolithExecutionRuntime[AuthT, TraceT](
            coordinator=self._coordinator,
            event_queue=self._event_queue,
            command_handler_resolver=self._command_handler_resolver,
            query_handler_resolver=self._query_handler_resolver,
            access_checker=self._access_checker,
            trace_span_factory=self._trace_span_factory,
        )

        self._overrides = self._build_dependency_overrides(
            execution_dependency_registry
        )
        self._runtime.set_dependency_overrides(self._overrides)

        self._auth_resolver = self._get_auth_resolver(self._overrides)

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        resolved = self._command_handler_resolver.resolve(
            command,
            overrides=self._overrides,
        )

        trace = self._resolve_trace(trace_input)
        self._runtime.set_trace(trace)

        root_uow = self._coordinator.get_command_uow(
            resolved.config.root_uow_type,
        )

        return await self._command_engine.handle(
            command=command,
            handler=resolved.handler,
            coordinator=self._coordinator,
            uow=root_uow,
            event_queue=self._event_queue,
            source_name=resolved.config.source_name,
            auth_resolver=self._auth_resolver,
            auth_input=auth_input,
            execution_mode=resolved.config.execution_mode,
            dependency_overrides=self._overrides,
            allowed_access_tags=resolved.config.allowed_access_tags,
            set_runtime_auth=self._runtime.set_auth,
            trace=trace,
        )
    
    async def handle_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        resolved = self._command_handler_resolver.resolve_by_key(key, overrides=self._overrides)

        command = self._build_command_from_payload(
            key=key,
            payload=payload,
            command_type=resolved.config.command_type,
        )

        trace = self._resolve_trace(trace_input)
        self._runtime.set_trace(trace)

        root_uow = self._coordinator.get_command_uow(
            resolved.config.root_uow_type,
        )

        return await self._command_engine.handle(
            command=command,
            handler=resolved.handler,
            coordinator=self._coordinator,
            uow=root_uow,
            event_queue=self._event_queue,
            source_name=resolved.config.source_name,
            auth_resolver=self._auth_resolver,
            auth_input=auth_input,
            execution_mode=resolved.config.execution_mode,
            dependency_overrides=self._overrides,
            allowed_access_tags=resolved.config.allowed_access_tags,
            set_runtime_auth=self._runtime.set_auth,
            trace=trace,
        )

    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        if self._query_engine is None or self._query_handler_resolver is None:
            raise RuntimeError(
                "Modular query execution is not configured. "
                "Provide query_handler_registry and query_root_uow_type "
                "in at least one ModularDirettoreContext to enable "
                "handle_query(...)."
            )

        resolved = self._query_handler_resolver.resolve(
            query,
            overrides=self._overrides,
        )

        trace = self._resolve_trace(trace_input)
        self._runtime.set_trace(trace)

        root_uow = self._coordinator.get_query_uow(
            resolved.config.root_uow_type,
        )

        return await self._query_engine.handle(
            query=query,
            handler=resolved.handler,
            uow=root_uow,
            source_name=resolved.config.source_name,
            auth_resolver=self._auth_resolver,
            auth_input=auth_input,
            allowed_access_tags=resolved.config.allowed_access_tags,
            trace=trace,
        )
    
    async def handle_query_by_key(
        self,
        key: str,
        payload: Mapping[str, Any],
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        if self._query_engine is None or self._query_handler_resolver is None:
            raise RuntimeError(
                "Modular query execution is not configured. "
                "Provide query_handler_registry and query_root_uow_type "
                "in at least one ModularDirettoreContext to enable "
                "handle_query_by_key(...)."
            )

        resolved = self._query_handler_resolver.resolve_by_key(key)

        query = self._build_query_from_payload(
            key=key,
            payload=payload,
            query_type=resolved.config.query_type,
        )

        trace = self._resolve_trace(trace_input)
        self._runtime.set_trace(trace)

        root_uow = self._coordinator.get_query_uow(
            resolved.config.root_uow_type,
        )

        return await self._query_engine.handle(
            query=query,
            handler=resolved.handler,
            uow=root_uow,
            source_name=resolved.config.source_name,
            auth_resolver=self._auth_resolver,
            auth_input=auth_input,
            allowed_access_tags=resolved.config.allowed_access_tags,
            trace=trace,
        )

    def reset(self) -> None:
        self._runtime.clear_auth()
        self._runtime.clear_trace()
        self._event_queue.clear()
        self._coordinator.reset()

    def _resolve_trace(
        self,
        trace_input: TraceInputT | None,
    ) -> TraceT | None:
        if self._trace_resolver is None:
            if trace_input is not None:
                raise RuntimeError(
                    "trace_input was provided, but trace resolver is not "
                    "configured."
                )

            return None

        return self._trace_resolver.resolve_trace(trace_input)

    def _build_dependency_overrides(
        self,
        execution_dependency_registry: (
            ModularMonolithExecutionDependencyRegistry | None
        ),
    ) -> dict[type[Any], Any] | None:
        if execution_dependency_registry is None:
            return None

        return dict(
            execution_dependency_registry.build_overrides(
                context=ModularMonolithExecutionDependencyContext(
                    runtime=self._runtime,
                ),
            )
        )

    def _get_auth_resolver(
        self,
        overrides: dict[type[Any], Any] | None,
    ) -> AuthResolverPort[AuthInputT, AuthT] | None:
        if overrides is None:
            return None

        auth_resolver = overrides.get(AuthResolverPort)

        if auth_resolver is None:
            return None

        return cast(AuthResolverPort[AuthInputT, AuthT], auth_resolver)
    
    def _build_command_from_payload(
        self,
        *,
        key: str,
        payload: Mapping[str, Any],
        command_type: type[Command],
    ) -> Command:
        try:
            command = command_type.from_payload(payload)
        except Exception as exc:
            raise RuntimeError(
                "Failed to create command from payload. "
                f"Key={key!r}, "
                f"command_type={command_type.__module__}.{command_type.__qualname__}, "
                f"payload={dict(payload)!r}."
            ) from exc

        if not isinstance(command, command_type):
            raise TypeError(
                "Command.from_payload(...) returned wrong command type. "
                f"Key={key!r}, "
                f"expected={command_type.__module__}.{command_type.__qualname__}, "
                f"actual={type(command).__module__}.{type(command).__qualname__}."
            )

        return command
    

    def _build_query_from_payload(
        self,
        *,
        key: str,
        payload: Mapping[str, Any],
        query_type: type[Query],
    ) -> Query:
        try:
            query = query_type.from_payload(payload)
        except Exception as exc:
            raise RuntimeError(
                "Failed to create query from payload. "
                f"Key={key!r}, "
                f"query_type={query_type.__module__}.{query_type.__qualname__}, "
                f"payload={dict(payload)!r}."
            ) from exc

        if not isinstance(query, query_type):
            raise TypeError(
                "Query.from_payload(...) returned wrong query type. "
                f"Key={key!r}, "
                f"expected={query_type.__module__}.{query_type.__qualname__}, "
                f"actual={type(query).__module__}.{type(query).__qualname__}."
            )

        return query