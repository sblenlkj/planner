from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, Mapping

from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Command, Query
from direttore.orchestration.engines.command_executor_engines.engine import (
    CommandExecutionEngine,
)
from direttore.orchestration.engines.query_executor_engines.engine import (
    QueryExecutionEngine,
)
from direttore.orchestration.event_queue import EventQueue
from direttore.orchestration.resolvers.service.command_handler_resolver import (
    CommandHandlerResolverPort,
)
from direttore.orchestration.resolvers.service.query_handler_resolver import (
    QueryHandlerResolverPort,
)
from direttore.orchestration.tracing import (
    TraceResolverPort,
)


AuthInputT = TypeVar("AuthInputT")
AuthInputContraT = TypeVar("AuthInputContraT", contravariant=True)
AuthT = TypeVar("AuthT")

TraceInputT = TypeVar("TraceInputT")
TraceInputContraT = TypeVar("TraceInputContraT", contravariant=True)
TraceT = TypeVar("TraceT")


class ServiceExecutionSlotPort(
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


class ServiceExecutionSlot(
    ServiceExecutionSlotPort[AuthInputT, TraceInputT],
    Generic[AuthInputT, AuthT, TraceInputT, TraceT],
):
    def __init__(
        self,
        *,
        command_uow: AbstractCommandUnitOfWork,
        command_handler_resolver: CommandHandlerResolverPort,
        command_engine: CommandExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ],
        query_uow: AbstractQueryUnitOfWork | None = None,
        query_handler_resolver: QueryHandlerResolverPort | None = None,
        query_engine: QueryExecutionEngine[
            AuthInputT,
            AuthT,
            TraceT,
        ]
        | None = None,
        trace_resolver: TraceResolverPort[TraceInputT, TraceT] | None = None,
    ) -> None:
        self._command_uow = command_uow
        self._query_uow = query_uow
        self._command_handler_resolver = command_handler_resolver
        self._query_handler_resolver = query_handler_resolver
        self._event_queue = EventQueue()
        self._command_engine = command_engine
        self._query_engine = query_engine
        self._trace_resolver = trace_resolver

    async def handle(
        self,
        command: Command,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        resolved = self._command_handler_resolver.resolve(command)
        trace = self._resolve_trace(trace_input)

        return await self._command_engine.handle(
            command=command,
            handler=resolved.handler,
            uow=self._command_uow,
            event_queue=self._event_queue,
            source_name=resolved.config.source_name,
            auth_input=auth_input,
            execution_mode=resolved.config.execution_mode,
            allowed_access_tags=resolved.config.allowed_access_tags,
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
        resolved = self._command_handler_resolver.resolve_by_key(key)

        command = self._build_command_from_payload(
            key=key,
            payload=payload,
            command_type=resolved.config.command_type,
        )

        trace = self._resolve_trace(trace_input)

        return await self._command_engine.handle(
            command=command,
            handler=resolved.handler,
            uow=self._command_uow,
            event_queue=self._event_queue,
            source_name=resolved.config.source_name,
            auth_input=auth_input,
            execution_mode=resolved.config.execution_mode,
            allowed_access_tags=resolved.config.allowed_access_tags,
            trace=trace,
        )


    async def handle_query(
        self,
        query: Query,
        *,
        auth_input: AuthInputT | None = None,
        trace_input: TraceInputT | None = None,
    ) -> Any:
        if (
            self._query_uow is None
            or self._query_handler_resolver is None
            or self._query_engine is None
        ):
            raise RuntimeError(
                "Service query execution is not configured. "
                "Provide query_handler_registry and query_uow_factory "
                "to enable handle_query(...)."
            )

        resolved = self._query_handler_resolver.resolve(query)
        trace = self._resolve_trace(trace_input)

        return await self._query_engine.handle(
            query=query,
            handler=resolved.handler,
            uow=self._query_uow,
            source_name=resolved.config.source_name,
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
        if (
            self._query_uow is None
            or self._query_handler_resolver is None
            or self._query_engine is None
        ):
            raise RuntimeError(
                "Service query execution is not configured. "
                "Provide query_handler_registry and query_uow_factory "
                "to enable handle_query(...)."
            )

        resolved = self._query_handler_resolver.resolve_by_key(key)

        query = self._build_query_from_payload(
            key=key,
            payload=payload,
            query_type=resolved.config.query_type,
        )

        trace = self._resolve_trace(trace_input)

        return await self._query_engine.handle(
            query=query,
            handler=resolved.handler,
            uow=self._query_uow,
            source_name=resolved.config.source_name,
            auth_input=auth_input,
            allowed_access_tags=resolved.config.allowed_access_tags,
            trace=trace,
        )

    def reset(self) -> None:
        self._event_queue.clear()
        self._command_uow.clear_tracking()

        if self._query_uow is not None:
            self._query_uow.clear_tracking()

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