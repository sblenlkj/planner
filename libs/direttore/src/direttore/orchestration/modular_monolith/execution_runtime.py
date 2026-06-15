from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, Mapping, TypeVar

from direttore.orchestration.auth import (
    AccessCheckContext,
    AccessCheckerPort,
    AccessInvocationKind,
)
from direttore.orchestration.base_types.command_handler import (
    AbstractCommandHandler,
    CommandHandlerContext,
)
from direttore.orchestration.base_types.message import Command, Query
from direttore.orchestration.base_types.query_handler import (
    AbstractQueryHandler,
    QueryHandlerContext,
)
from direttore.orchestration.event_queue import EventQueue
from direttore.orchestration.modular_monolith.coordinator import (
    ModularUnitOfWorkCoordinator,
)
from direttore.orchestration.resolvers.modular_monolith.modular_command_handler_resolver import (
    ModularMonolithCommandHandlerResolver,
)
from direttore.orchestration.resolvers.modular_monolith.modular_query_handler_resolver import (
    ModularMonolithQueryHandlerResolver,
)
from direttore.orchestration.tracing import (
    NoopTraceSpan,
    TraceSpanFactoryPort,
    TraceSpanPort,
)


AuthT = TypeVar("AuthT")
TraceT = TypeVar("TraceT")


class ModularMonolithExecutionRuntime(Generic[AuthT, TraceT]):
    def __init__(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        event_queue: EventQueue,
        command_handler_resolver: ModularMonolithCommandHandlerResolver,
        query_handler_resolver: ModularMonolithQueryHandlerResolver | None = None,
        access_checker: AccessCheckerPort[AuthT] | None = None,
        trace_span_factory: TraceSpanFactoryPort[TraceT] | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._event_queue = event_queue
        self._command_handler_resolver = command_handler_resolver
        self._query_handler_resolver = query_handler_resolver
        self._access_checker = access_checker
        self._trace_span_factory = trace_span_factory

        self._dependency_overrides: Mapping[type[Any], Any] | None = None
        self._auth: AuthT | None = None
        self._trace: TraceT | None = None

    @property
    def auth(self) -> AuthT | None:
        return self._auth

    @property
    def trace(self) -> TraceT | None:
        return self._trace

    def set_auth(
        self,
        auth: AuthT | None,
    ) -> None:
        self._auth = auth

    def clear_auth(self) -> None:
        self._auth = None

    def set_trace(
        self,
        trace: TraceT | None,
    ) -> None:
        self._trace = trace

    def clear_trace(self) -> None:
        self._trace = None

    def set_dependency_overrides(
        self,
        overrides: Mapping[type[Any], Any] | None,
    ) -> None:
        self._dependency_overrides = overrides

    async def invoke(
        self,
        command: Command,
    ) -> Any:
        resolved = self._command_handler_resolver.resolve(
            command,
            overrides=self._dependency_overrides,
        )

        source_name = resolved.config.source_name

        async with self._start_span(
            name=self._build_span_name(
                operation="runtime.invoke",
                source_name=source_name,
                message=command,
            ),
            attributes=self._build_command_span_attributes(
                command=command,
                handler=resolved.handler,
                source_name=source_name,
            ),
        ):
            auth = self._get_auth_for_access_policy(
                allowed_access_tags=resolved.config.allowed_access_tags,
                message=command,
            )

            root_uow = self._coordinator.get_command_uow(
                resolved.config.root_uow_type,
            )

            context = CommandHandlerContext(
                uow=root_uow,
                queue=self._event_queue,
                auth=auth,
            )

            handler = resolved.handler

            if not isinstance(handler, AbstractCommandHandler):
                raise RuntimeError(
                    "Unsupported command handler type. "
                    "ModularMonolithExecutionRuntime currently supports only "
                    "AbstractCommandHandler for runtime.invoke(...). "
                    f"Handler={type(handler).__module__}."
                    f"{type(handler).__qualname__}."
                )

            return await handler(command, context)

    async def invoke_query(
        self,
        query: Query,
    ) -> Any:
        query_handler_resolver = self._require_query_handler_resolver()

        resolved = query_handler_resolver.resolve(
            query,
            overrides=self._dependency_overrides,
        )

        source_name = resolved.config.source_name

        async with self._start_span(
            name=self._build_span_name(
                operation="runtime.invoke_query",
                source_name=source_name,
                message=query,
            ),
            attributes=self._build_query_span_attributes(
                query=query,
                handler=resolved.handler,
                source_name=source_name,
            ),
        ):
            auth = self._get_auth_for_access_policy(
                allowed_access_tags=resolved.config.allowed_access_tags,
                message=query,
            )

            root_uow = self._coordinator.get_query_uow(
                resolved.config.root_uow_type,
            )

            context = QueryHandlerContext(
                uow=root_uow,
                auth=auth,
            )

            handler = resolved.handler

            if not isinstance(handler, AbstractQueryHandler):
                raise RuntimeError(
                    "Unsupported query handler type. "
                    "ModularMonolithExecutionRuntime currently supports only "
                    "AbstractQueryHandler for runtime.invoke_query(...). "
                    f"Handler={type(handler).__module__}."
                    f"{type(handler).__qualname__}."
                )

            return await handler(query, context)

    def _get_auth_for_access_policy(
        self,
        *,
        allowed_access_tags: frozenset[str] | None,
        message: Command | Query,
    ) -> AuthT | None:
        auth = self._auth

        if allowed_access_tags is None:
            return auth

        if auth is None:
            raise RuntimeError(
                "Runtime invocation requires access tags, but root execution "
                "has no auth context. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        if self._access_checker is None:
            raise RuntimeError(
                "Runtime invocation requires access tags, but access checker "
                "is not configured. "
                f"Message={type(message).__module__}.{type(message).__qualname__}."
            )

        self._access_checker.check(
            allowed_access_tags=allowed_access_tags,
            auth=auth,
            message=message,
            context=AccessCheckContext(
                invocation_kind=AccessInvocationKind.SYSTEM_INVOKE,
            ),
        )

        return auth

    def _require_query_handler_resolver(
        self,
    ) -> ModularMonolithQueryHandlerResolver:
        if self._query_handler_resolver is None:
            raise RuntimeError(
                "Modular query execution is not configured. "
                "runtime.invoke_query(...) requires query_handler_registry and "
                "query_root_uow_type in at least one ModularDirettoreContext."
            )

        return self._query_handler_resolver

    def _start_span(
        self,
        *,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        if self._trace_span_factory is None:
            return NoopTraceSpan()

        return self._trace_span_factory.start_span(
            trace=self._trace,
            name=name,
            attributes=attributes,
        )

    def _build_span_name(
        self,
        *,
        operation: str,
        source_name: str | None,
        message: Command | Query,
    ) -> str:
        message_name = type(message).__qualname__

        if source_name is None:
            return f"orchestration.{operation} {message_name}"

        return f"orchestration.{operation} {source_name}.{message_name}"

    def _build_command_span_attributes(
        self,
        *,
        command: Command,
        handler: Any,
        source_name: str | None,
    ) -> dict[str, Any]:
        return {
            "orchestration.source": source_name,
            "message.kind": "command",
            "message.type": type(command).__qualname__,
            "message.module": type(command).__module__,
            "handler.type": type(handler).__qualname__,
            "handler.module": type(handler).__module__,
            "invocation.kind": "system_invoke",
        }

    def _build_query_span_attributes(
        self,
        *,
        query: Query,
        handler: Any,
        source_name: str | None,
    ) -> dict[str, Any]:
        return {
            "orchestration.source": source_name,
            "message.kind": "query",
            "message.type": type(query).__qualname__,
            "message.module": type(query).__module__,
            "handler.type": type(handler).__qualname__,
            "handler.module": type(handler).__module__,
            "invocation.kind": "system_invoke",
        }