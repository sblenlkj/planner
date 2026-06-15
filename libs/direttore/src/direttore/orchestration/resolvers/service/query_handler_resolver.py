from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, get_type_hints

from direttore.orchestration.base_types.message import Query
from direttore.orchestration.base_types.query_handler import (
    QueryHandler,
)
from direttore.orchestration.registries.service.query_handler_registry import (
    QueryHandlerGroupName,
    QueryHandlerRegistration,
    QueryHandlerRegistryPort,
)
from direttore.orchestration.resolvers.container import Container


@dataclass(frozen=True, slots=True)
class ResolvedQueryHandlerConfig:
    query_type: type[Query]
    allowed_access_tags: frozenset[str] | None = None
    source_name: str | None = None
    key: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedQueryHandler:
    handler: QueryHandler
    config: ResolvedQueryHandlerConfig 


class QueryHandlerResolverPort(Protocol):
    def validate_query_handlers(
        self,
        *,
        group: QueryHandlerGroupName = None,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        raise NotImplementedError

    def resolve(
        self,
        query: Query,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedQueryHandler:
        raise NotImplementedError

    def resolve_by_key(
        self,
        key: str,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedQueryHandler:
        raise NotImplementedError


class AbstractQueryHandlerResolver(QueryHandlerResolverPort, ABC):
    def __init__(self, registry: QueryHandlerRegistryPort) -> None:
        self._registry = registry

    @property
    def registry(self) -> QueryHandlerRegistryPort:
        return self._registry

    def validate_query_handlers(
        self,
        *,
        group: QueryHandlerGroupName = None,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        seen: set[type[QueryHandler]] = set()

        for registration in self._registry.iter_registrations(group=group):
            handler_type = registration.handler_type

            if handler_type in seen:
                continue

            self._validate_registration(registration)
            self._validate_handler(
                registration=registration,
                overrides=overrides,
            )
            seen.add(handler_type)

    def resolve(
        self,
        query: Query,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedQueryHandler:
        registration = self._registry.get_registration_by_query_type(
            type(query),
        )

        return self._resolve_registration(
            registration=registration,
            overrides=overrides,
        )

    def resolve_by_key(
        self,
        key: str,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedQueryHandler:
        registration = self._registry.get_registration_by_key(key)

        return self._resolve_registration(
            registration=registration,
            overrides=overrides,
        )

    def _resolve_registration(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None,
    ) -> ResolvedQueryHandler:
        self._validate_registration(registration)

        return ResolvedQueryHandler(
            handler=self._resolve_handler(
                registration=registration,
                overrides=overrides,
            ),
            config=ResolvedQueryHandlerConfig(
                query_type=registration.query_type,
                allowed_access_tags=registration.config.allowed_access_tags,
                source_name=registration.source_name,
                key=registration.key,
            ),
        )

    def _validate_registration(
        self,
        registration: QueryHandlerRegistration,
    ) -> None:
        return 

        if registration.allowed_access_tags is None:
            raise RuntimeError(
                "Query handler registration has no allowed_access_tags. "
                f"Query={registration.query_type.__module__}."
                f"{registration.query_type.__qualname__}, "
                f"handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}."
            )

        if not registration.allowed_access_tags:
            raise RuntimeError(
                "Query handler registration has empty allowed_access_tags. "
                f"Query={registration.query_type.__module__}."
                f"{registration.query_type.__qualname__}, "
                f"handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}."
            )

    @abstractmethod
    def _resolve_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> QueryHandler:
        raise NotImplementedError

    @abstractmethod
    def _validate_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        raise NotImplementedError


class ContainerQueryHandlerResolver(AbstractQueryHandlerResolver):
    def __init__(
        self,
        *,
        registry: QueryHandlerRegistryPort,
        container: Container,
    ) -> None:
        super().__init__(registry)
        self._container = container

    def _resolve_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> QueryHandler:
        if overrides is not None:
            raise RuntimeError(
                "ContainerQueryHandlerResolver does not support execution "
                "dependency overrides. Use AutoWiringQueryHandlerResolver."
            )

        return self._container.get(registration.handler_type)

    def _validate_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        if overrides is not None:
            raise RuntimeError(
                "ContainerQueryHandlerResolver does not support execution "
                "dependency overrides. Use AutoWiringQueryHandlerResolver."
            )

        self._container.get(registration.handler_type)


class AutoWiringQueryHandlerResolver(AbstractQueryHandlerResolver):
    def __init__(
        self,
        *,
        registry: QueryHandlerRegistryPort,
        container: Container,
    ) -> None:
        super().__init__(registry)
        self._container = container
        self._cache: dict[type[QueryHandler], QueryHandler] = {}

    def _resolve_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> QueryHandler:
        handler_type = registration.handler_type

        cached_handler = self._cache.get(handler_type)
        if cached_handler is not None:
            return cached_handler

        uses_overrides = self._uses_overrides(
            handler_type=handler_type,
            overrides=overrides,
        )

        if registration.config.cache_handler and not uses_overrides:
            handler = self._create_handler(
                handler_type=handler_type,
                overrides=None,
            )
            self._cache[handler_type] = handler

            return handler

        return self._create_handler(
            handler_type=handler_type,
            overrides=overrides if uses_overrides else None,
        )

    def _validate_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        self._get_init_dependency_types(registration.handler_type)

        self._resolve_init_kwargs(
            handler_type=registration.handler_type,
            overrides=overrides,
        )

    def _uses_overrides(
        self,
        *,
        handler_type: type[QueryHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> bool:
        if not overrides:
            return False

        dependency_types = self._get_init_dependency_types(handler_type)

        return any(
            dependency_type in overrides
            for dependency_type in dependency_types
        )

    def _create_handler(
        self,
        *,
        handler_type: type[QueryHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> QueryHandler:
        kwargs = self._resolve_init_kwargs(
            handler_type=handler_type,
            overrides=overrides,
        )

        return handler_type(**kwargs)

    def _resolve_init_kwargs(
        self,
        *,
        handler_type: type[QueryHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        for name, dependency_type in self._iter_init_dependencies(handler_type):
            if overrides is not None and dependency_type in overrides:
                kwargs[name] = overrides[dependency_type]
                continue

            kwargs[name] = self._container.get(dependency_type)

        return kwargs

    def _get_init_dependency_types(
        self,
        handler_type: type[QueryHandler],
    ) -> set[type[Any]]:
        return {
            dependency_type
            for _, dependency_type in self._iter_init_dependencies(handler_type)
        }

    def _iter_init_dependencies(
        self,
        handler_type: type[QueryHandler],
    ) -> list[tuple[str, type[Any]]]:
        signature = inspect.signature(handler_type.__init__)
        hints = get_type_hints(handler_type.__init__)

        dependencies: list[tuple[str, type[Any]]] = []

        for name, parameter in signature.parameters.items():
            if name == "self":
                continue

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            annotation = hints.get(name)

            if annotation is None:
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} must have a resolvable "
                    "type annotation."
                )

            if not isinstance(annotation, type):
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} annotation must be a type, "
                    f"got {annotation!r}."
                )

            dependencies.append((name, annotation))

        return dependencies


class WarmUpCacheAutoWiringQueryHandlerResolver(
    AbstractQueryHandlerResolver,
):
    def __init__(
        self,
        *,
        registry: QueryHandlerRegistryPort,
        container: Container,
        execution_dependency_types: set[type[Any]] | None = None,
    ) -> None:
        super().__init__(registry)
        self._container = container
        self._execution_dependency_types = execution_dependency_types or set()
        self._cache: dict[type[QueryHandler], QueryHandler] = {}

        self.warm_up_cache()

    def warm_up_cache(self) -> None:
        for registration in self._registry.iter_registrations():
            self._warm_up_registration_cache(registration)

    def _warm_up_registration_cache(
        self,
        registration: QueryHandlerRegistration,
    ) -> None:
        self._validate_registration(registration)

        handler_type = registration.handler_type

        if not registration.config.cache_handler:
            return

        if handler_type in self._cache:
            raise RuntimeError(
                f"Handler type {handler_type} is already cached. "
                "Double registration problem."
            )

        if self._uses_execution_dependency_types(handler_type):
            return

        self._cache[handler_type] = self._create_handler(
            handler_type=handler_type,
            overrides=None,
        )

    def _resolve_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> QueryHandler:
        handler_type = registration.handler_type

        cached_handler = self._cache.get(handler_type)

        if cached_handler is not None:
            return cached_handler

        return self._create_handler(
            handler_type=handler_type,
            overrides=overrides,
        )

    def _validate_handler(
        self,
        *,
        registration: QueryHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        self._resolve_init_kwargs(
            handler_type=registration.handler_type,
            overrides=overrides,
        )

    def _create_handler(
        self,
        *,
        handler_type: type[QueryHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> QueryHandler:
        kwargs = self._resolve_init_kwargs(
            handler_type=handler_type,
            overrides=overrides,
        )

        return handler_type(**kwargs)

    def _resolve_init_kwargs(
        self,
        *,
        handler_type: type[QueryHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        for name, dependency_type in self._iter_init_dependencies(handler_type):
            if overrides is not None and dependency_type in overrides:
                kwargs[name] = overrides[dependency_type]
                continue

            kwargs[name] = self._container.get(dependency_type)

        return kwargs

    def _uses_execution_dependency_types(
        self,
        handler_type: type[QueryHandler],
    ) -> bool:
        if not self._execution_dependency_types:
            return False

        dependency_types = self._get_init_dependency_types(handler_type)

        return any(
            dependency_type in self._execution_dependency_types
            for dependency_type in dependency_types
        )

    def _get_init_dependency_types(
        self,
        handler_type: type[QueryHandler],
    ) -> set[type[Any]]:
        return {
            dependency_type
            for _, dependency_type in self._iter_init_dependencies(handler_type)
        }

    def _iter_init_dependencies(
        self,
        handler_type: type[QueryHandler],
    ) -> list[tuple[str, type[Any]]]:
        signature = inspect.signature(handler_type.__init__)
        hints = get_type_hints(handler_type.__init__)

        dependencies: list[tuple[str, type[Any]]] = []

        for name, parameter in signature.parameters.items():
            if name == "self":
                continue

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            annotation = hints.get(name)

            if annotation is None:
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} must have a resolvable "
                    "type annotation."
                )

            if not isinstance(annotation, type):
                raise TypeError(
                    f"{handler_type.__module__}.{handler_type.__qualname__}"
                    f".__init__ parameter {name!r} annotation must be a type, "
                    f"got {annotation!r}."
                )

            dependencies.append((name, annotation))

        return dependencies