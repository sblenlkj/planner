from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from direttore.orchestration.base_classes.uow import (
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Query
from direttore.orchestration.base_types.query_handler import QueryHandler
from direttore.orchestration.registries.modular_monolith.modular_query_handler_registry import (
    ModularMonolithQueryHandlerRegistry,
)
from direttore.orchestration.resolvers.service.query_handler_resolver import (
    QueryHandlerResolverPort,
)


@dataclass(frozen=True, slots=True)
class ResolvedModularQueryHandlerConfig:
    root_uow_type: type[AbstractQueryUnitOfWork]
    query_type: type[Query]
    allowed_access_tags: frozenset[str] | None = None
    source_name: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedModularQueryHandler:
    handler: QueryHandler
    config: ResolvedModularQueryHandlerConfig


class ModularMonolithQueryHandlerResolverPort(Protocol):
    def validate_query_handlers(self) -> None:
        raise NotImplementedError

    def resolve(
        self,
        query: Query,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularQueryHandler:
        raise NotImplementedError


class ModularMonolithQueryHandlerResolver(
    ModularMonolithQueryHandlerResolverPort,
):
    """
    Adds modular-monolith routing metadata to a normal query handler resolver.

    The wrapped resolver is responsible for creating query handler instances.
    The modular registry is responsible for mapping query types to root query
    UoW types.
    """

    def __init__(
        self,
        *,
        query_handler_resolver: QueryHandlerResolverPort,
        registry: ModularMonolithQueryHandlerRegistry,
    ) -> None:
        self._query_handler_resolver = query_handler_resolver
        self._registry = registry

    def validate_query_handlers(self) -> None:
        self._query_handler_resolver.validate_query_handlers()

    def resolve(
        self,
        query: Query,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularQueryHandler:
        resolved = self._query_handler_resolver.resolve(
            query,
            overrides=overrides,
        )

        return ResolvedModularQueryHandler(
            handler=resolved.handler,
            config=ResolvedModularQueryHandlerConfig(
                allowed_access_tags=resolved.config.allowed_access_tags,
                query_type=type(query),
                root_uow_type=self._registry.get_root_uow_type(query),
                source_name=resolved.config.source_name,
            ),
        )
    

    def resolve_by_key(
        self,
        key: str,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularQueryHandler:
        resolved = self._query_handler_resolver.resolve_by_key(
            key,
            overrides=overrides,
        )

        return ResolvedModularQueryHandler(
            handler=resolved.handler,
            config=ResolvedModularQueryHandlerConfig(
                allowed_access_tags=resolved.config.allowed_access_tags,
                query_type=resolved.config.query_type,
                root_uow_type=self._registry.get_root_uow_type_by_query_type(resolved.config.query_type),
                source_name=resolved.config.source_name,
            ),
        )