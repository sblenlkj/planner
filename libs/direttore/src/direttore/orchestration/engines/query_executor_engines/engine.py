from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, Protocol, TypeVar

from direttore.orchestration.auth import (
    AccessCheckerPort,
    AuthResolverPort,
)
from direttore.orchestration.base_classes.uow import (
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Query
from direttore.orchestration.base_types.query_handler import (
    AbstractQueryHandler,
    QueryHandler,
    QueryHandlerContext,
)
from direttore.orchestration.tracing import (
    TraceSpanFactoryPort,
    TraceSpanPort,
)


AuthInputT = TypeVar("AuthInputT")
AuthT = TypeVar("AuthT")
TraceT = TypeVar("TraceT")


class QueryExecutionEnginePort(Protocol):
    async def handle(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        source_name: str | None = None,
        auth_input: Any | None = None,
        allowed_access_tags: frozenset[str] | None = None,
        trace: Any | None = None,
    ) -> Any:
        raise NotImplementedError


class QueryExecutionEngine(
    QueryExecutionEnginePort,
    Generic[AuthInputT, AuthT, TraceT],
):
    def __init__(
        self,
        *,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None = None,
        access_checker: AccessCheckerPort[AuthT] | None = None,
        trace_span_factory: TraceSpanFactoryPort[TraceT] | None = None,
    ) -> None:
        self._validate_auth_configuration(
            auth_resolver=auth_resolver,
            access_checker=access_checker,
        )

        self._auth_resolver = auth_resolver
        self._access_checker = access_checker
        self._trace_span_factory = trace_span_factory

    async def handle(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        source_name: str | None = None,
        auth_input: AuthInputT | None = None,
        allowed_access_tags: frozenset[str] | None = None,
        trace: TraceT | None = None,
    ) -> Any:
        if self._trace_span_factory is None:
            return await self._handle_without_root_span(
                query=query,
                handler=handler,
                uow=uow,
                source_name=source_name,
                auth_input=auth_input,
                allowed_access_tags=allowed_access_tags,
                trace=trace,
            )

        return await self._handle_with_root_span(
            query=query,
            handler=handler,
            uow=uow,
            source_name=source_name,
            auth_input=auth_input,
            allowed_access_tags=allowed_access_tags,
            trace=trace,
        )

    async def _handle_with_root_span(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        source_name: str | None,
        auth_input: AuthInputT | None,
        allowed_access_tags: frozenset[str] | None,
        trace: TraceT | None,
    ) -> Any:
        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="query",
                source_name=source_name,
                query=query,
            ),
            attributes=self._build_query_span_attributes(
                query=query,
                handler=handler,
                source_name=source_name,
            ),
        ):
            return await self._handle_without_root_span(
                query=query,
                handler=handler,
                uow=uow,
                source_name=source_name,
                auth_input=auth_input,
                allowed_access_tags=allowed_access_tags,
                trace=trace,
            )

    async def _handle_without_root_span(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        source_name: str | None,
        auth_input: AuthInputT | None,
        allowed_access_tags: frozenset[str] | None,
        trace: TraceT | None,
    ) -> Any:
        async with uow:
            auth = await self._prepare_auth(
                query=query,
                source_name=source_name,
                auth_input=auth_input,
                allowed_access_tags=allowed_access_tags,
                trace=trace,
            )

            return await self._call_handler(
                query=query,
                handler=handler,
                uow=uow,
                auth=auth,
                source_name=source_name,
                trace=trace,
            )

    def _validate_auth_configuration(
        self,
        *,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        access_checker: AccessCheckerPort[AuthT] | None,
    ) -> None:
        if auth_resolver is None and access_checker is not None:
            raise RuntimeError(
                "Access checker is configured, but auth resolver is not configured."
            )

        if auth_resolver is not None and access_checker is None:
            raise RuntimeError(
                "Auth resolver is configured, but access checker is not configured."
            )

    async def _prepare_auth(
        self,
        *,
        query: Query,
        source_name: str | None,
        auth_input: AuthInputT | None,
        allowed_access_tags: frozenset[str] | None,
        trace: TraceT | None,
    ) -> AuthT | None:
        if self._trace_span_factory is None:
            return await self._prepare_auth_without_span(
                query=query,
                auth_input=auth_input,
                allowed_access_tags=allowed_access_tags,
            )

        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="auth",
                source_name=source_name,
                query=query,
            ),
            attributes={
                "orchestration.source": source_name,
                "message.kind": "query",
                "message.type": type(query).__qualname__,
                "message.module": type(query).__module__,
                "auth.configured": self._auth_resolver is not None,
                "access.tags.required": allowed_access_tags is not None,
            },
        ):
            return await self._prepare_auth_without_span(
                query=query,
                auth_input=auth_input,
                allowed_access_tags=allowed_access_tags,
            )

    async def _prepare_auth_without_span(
        self,
        *,
        query: Query,
        auth_input: AuthInputT | None,
        allowed_access_tags: frozenset[str] | None,
    ) -> AuthT | None:
        if self._auth_resolver is None:
            if auth_input is not None:
                raise RuntimeError(
                    "auth_input was provided, but auth pipeline is not configured."
                )

            if allowed_access_tags is not None:
                raise RuntimeError(
                    "Query requires access tags, but auth pipeline is not "
                    "configured. "
                    f"Query={type(query).__module__}."
                    f"{type(query).__qualname__}."
                )

            return None

        if auth_input is None:
            raise RuntimeError(
                "Auth resolver is configured, but auth_input was not provided."
            )

        auth = await self._auth_resolver.resolve_auth(auth_input)

        if auth is None:
            raise RuntimeError(
                "AuthResolver returned None. "
                "Return an explicit public/anonymous auth object instead of None."
            )

        if self._access_checker is None:
            raise RuntimeError(
                "Auth was resolved, but access checker is not configured."
            )

        self._access_checker.check(
            allowed_access_tags=allowed_access_tags,
            auth=auth,
            message=query,
        )

        return auth

    async def _call_handler(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        auth: AuthT | None,
        source_name: str | None,
        trace: TraceT | None,
    ) -> Any:
        if self._trace_span_factory is None:
            return await self._call_handler_without_span(
                query=query,
                handler=handler,
                uow=uow,
                auth=auth,
            )

        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="query_handler",
                source_name=source_name,
                query=query,
            ),
            attributes=self._build_query_span_attributes(
                query=query,
                handler=handler,
                source_name=source_name,
            ),
        ):
            return await self._call_handler_without_span(
                query=query,
                handler=handler,
                uow=uow,
                auth=auth,
            )

    async def _call_handler_without_span(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        uow: AbstractQueryUnitOfWork,
        auth: AuthT | None,
    ) -> Any:
        if not isinstance(handler, AbstractQueryHandler):
            raise RuntimeError(
                "Unsupported query handler type. "
                "QueryExecutionEngine currently supports only "
                "AbstractQueryHandler. "
                f"Handler={type(handler).__module__}."
                f"{type(handler).__qualname__}."
            )

        context = QueryHandlerContext(
            uow=uow,
            auth=auth,
        )

        return await handler(query, context)

    def _start_span(
        self,
        *,
        trace: TraceT | None,
        name: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        if self._trace_span_factory is None:
            raise RuntimeError(
                "Trace span factory is not configured."
            )

        return self._trace_span_factory.start_span(
            trace=trace,
            name=name,
            attributes=dict(attributes or {}),
        )

    def _build_span_name(
        self,
        *,
        operation: str,
        source_name: str | None,
        query: Query,
    ) -> str:
        query_name = type(query).__qualname__

        if source_name is None:
            return f"orchestration.{operation} {query_name}"

        return f"orchestration.{operation} {source_name}.{query_name}"

    def _build_query_span_attributes(
        self,
        *,
        query: Query,
        handler: QueryHandler,
        source_name: str | None,
    ) -> Mapping[str, Any]:
        return {
            "orchestration.source": source_name,
            "message.kind": "query",
            "message.type": type(query).__qualname__,
            "message.module": type(query).__module__,
            "handler.type": type(handler).__qualname__,
            "handler.module": type(handler).__module__,
        }