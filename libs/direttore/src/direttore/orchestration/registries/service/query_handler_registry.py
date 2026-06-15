from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, TypeVar

from direttore.orchestration.base_types.message import Query
from direttore.orchestration.base_types.query_handler import (
    QueryHandler,
    QueryHandlerConfig,
)


class QueryHandlerGroup(StrEnum):
    REST = "rest"
    INTERNAL = "internal"


QueryHandlerGroupName = QueryHandlerGroup | str | None


TQueryHandler = TypeVar(
    "TQueryHandler",
    bound=type[QueryHandler],
)


@dataclass(frozen=True, slots=True)
class QueryHandlerRegistration:
    query_type: type[Query]
    handler_type: type[QueryHandler]
    group: str | None = None
    key: str | None = None
    source_name: str | None = None
    config: QueryHandlerConfig = field(default_factory=QueryHandlerConfig)


class QueryHandlerRegistryPort(Protocol):
    def get_registration(
        self,
        query: Query,
    ) -> QueryHandlerRegistration:
        raise NotImplementedError

    def get_registration_by_query_type(
        self,
        query_type: type[Query],
    ) -> QueryHandlerRegistration:
        raise NotImplementedError

    def get_registration_by_key(
        self,
        key: str,
    ) -> QueryHandlerRegistration:
        raise NotImplementedError

    def iter_registrations(
        self,
        *,
        group: QueryHandlerGroupName = None,
    ) -> list[QueryHandlerRegistration]:
        raise NotImplementedError

    def iter_handler_types(
        self,
        *,
        group: QueryHandlerGroupName = None,
    ) -> list[type[QueryHandler]]:
        raise NotImplementedError


class QueryHandlerRegistry(QueryHandlerRegistryPort):
    def __init__(
        self,
        *,
        source_name: str | None = None,
    ) -> None:
        self.source_name = source_name

        self._registrations_by_query: dict[
            type[Query],
            QueryHandlerRegistration,
        ] = {}

        self._registrations_by_key: dict[
            str,
            QueryHandlerRegistration,
        ] = {}

        self._registrations_by_group: dict[
            str | None,
            list[QueryHandlerRegistration],
        ] = defaultdict(list)

        self._registrations: list[QueryHandlerRegistration] = []

    def handler(
        self,
        query_type: type[Query],
        *,
        group: QueryHandlerGroupName = None,
        key: str | None = None,
        register_key: bool = False,
        config: QueryHandlerConfig | None = None,
    ):
        self._validate_query_type(query_type)

        def decorator(handler_type: TQueryHandler) -> TQueryHandler:
            self.register(
                query_type=query_type,
                handler_type=handler_type,
                group=group,
                key=key,
                register_key=register_key,
                config=config,
            )
            return handler_type

        return decorator

    def register(
        self,
        *,
        query_type: type[Query],
        handler_type: type[QueryHandler],
        group: QueryHandlerGroupName = None,
        key: str | None = None,
        register_key: bool = False,
        config: QueryHandlerConfig | None = None,
    ) -> None:
        self._validate_query_type(query_type)
        self._validate_handler_type(handler_type)

        resolved_key = self._resolve_key(
            handler_type=handler_type,
            key=key,
            register_key=register_key,
        )

        self._add_registration(
            QueryHandlerRegistration(
                query_type=query_type,
                handler_type=handler_type,
                group=self._normalize_group(group),
                key=resolved_key,
                source_name=self.source_name,
                config=config or QueryHandlerConfig(),
            )
        )

    def get_registration(
        self,
        query: Query,
    ) -> QueryHandlerRegistration:
        return self.get_registration_by_query_type(type(query))

    def get_registration_by_query_type(
        self,
        query_type: type[Query],
    ) -> QueryHandlerRegistration:
        self._validate_query_type(query_type)

        registration = self._registrations_by_query.get(query_type)

        if registration is None:
            raise LookupError(
                f"No query handler registered for query "
                f"{query_type.__module__}.{query_type.__qualname__}."
            )

        return registration

    def get_registration_by_key(
        self,
        key: str,
    ) -> QueryHandlerRegistration:
        if not key:
            raise ValueError("Query handler key must not be empty.")

        registration = self._registrations_by_key.get(key)

        if registration is None:
            raise LookupError(
                f"No query handler registered for key {key!r}."
            )

        return registration

    def get_handler_type(
        self,
        query: Query,
    ) -> type[QueryHandler]:
        return self.get_registration(query).handler_type

    def get_handler_type_by_query_type(
        self,
        query_type: type[Query],
    ) -> type[QueryHandler]:
        return self.get_registration_by_query_type(query_type).handler_type

    def get_handler_type_by_key(
        self,
        key: str,
    ) -> type[QueryHandler]:
        return self.get_registration_by_key(key).handler_type

    def iter_registrations(
        self,
        *,
        group: QueryHandlerGroupName = None,
    ) -> list[QueryHandlerRegistration]:
        normalized_group = self._normalize_group(group)

        if normalized_group is not None:
            return list(self._registrations_by_group.get(normalized_group, []))

        return list(self._registrations)

    def iter_handler_types(
        self,
        *,
        group: QueryHandlerGroupName = None,
    ) -> list[type[QueryHandler]]:
        return [
            registration.handler_type
            for registration in self.iter_registrations(group=group)
        ]

    def iter_query_types(
        self,
        *,
        group: QueryHandlerGroupName = None,
    ) -> list[type[Query]]:
        return [
            registration.query_type
            for registration in self.iter_registrations(group=group)
        ]

    def filter_by_group(
        self,
        group: QueryHandlerGroupName,
        *,
        source_name: str | None = None,
    ) -> QueryHandlerRegistry:
        filtered = QueryHandlerRegistry(
            source_name=source_name,
        )

        for registration in self.iter_registrations(group=group):
            filtered._add_registration(registration)

        return filtered

    @classmethod
    def from_mapping(
        cls,
        mapping: dict[type[Query], type[QueryHandler]],
        *,
        source_name: str | None = None,
        group: QueryHandlerGroupName = None,
        register_key: bool = False,
        config: QueryHandlerConfig | None = None,
    ) -> QueryHandlerRegistry:
        registry = cls(
            source_name=source_name,
        )

        for query_type, handler_type in mapping.items():
            registry.register(
                query_type=query_type,
                handler_type=handler_type,
                group=group,
                register_key=register_key,
                config=config,
            )

        return registry

    @classmethod
    def merge_many(
        cls,
        registries: Iterable[QueryHandlerRegistry],
        *,
        source_name: str | None = None,
    ) -> QueryHandlerRegistry:
        merged = cls(source_name=source_name)

        for registry in registries:
            for registration in registry.iter_registrations():
                merged._add_registration(registration)

        return merged

    def _add_registration(
        self,
        registration: QueryHandlerRegistration,
    ) -> None:
        existing_query_registration = self._registrations_by_query.get(
            registration.query_type
        )

        if existing_query_registration is not None:
            raise ValueError(
                "Duplicate query handler registration. "
                f"Query={registration.query_type.__module__}."
                f"{registration.query_type.__qualname__}, "
                f"existing_handler={existing_query_registration.handler_type.__module__}."
                f"{existing_query_registration.handler_type.__qualname__}, "
                f"new_handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}, "
                f"existing_source={existing_query_registration.source_name!r}, "
                f"new_source={registration.source_name!r}."
            )

        if registration.key is not None:
            existing_key_registration = self._registrations_by_key.get(
                registration.key
            )

            if existing_key_registration is not None:
                raise ValueError(
                    "Duplicate query handler key registration. "
                    f"Key={registration.key!r}, "
                    f"existing_query={existing_key_registration.query_type.__module__}."
                    f"{existing_key_registration.query_type.__qualname__}, "
                    f"new_query={registration.query_type.__module__}."
                    f"{registration.query_type.__qualname__}, "
                    f"existing_handler={existing_key_registration.handler_type.__module__}."
                    f"{existing_key_registration.handler_type.__qualname__}, "
                    f"new_handler={registration.handler_type.__module__}."
                    f"{registration.handler_type.__qualname__}, "
                    f"existing_source={existing_key_registration.source_name!r}, "
                    f"new_source={registration.source_name!r}."
                )

            self._registrations_by_key[registration.key] = registration

        self._registrations_by_query[registration.query_type] = registration
        self._registrations_by_group[registration.group].append(registration)
        self._registrations.append(registration)

    def _resolve_key(
        self,
        *,
        handler_type: type[QueryHandler],
        key: str | None,
        register_key: bool,
    ) -> str | None:
        if key is not None:
            if not key:
                raise ValueError("Query handler key must not be empty.")

            return key

        if not register_key:
            return None

        handler_key = handler_type.query_handler_key

        if handler_key is None:
            raise ValueError(
                f"{handler_type.__module__}.{handler_type.__qualname__} "
                "cannot be registered by key because query_handler_key is not set."
            )

        if not handler_key:
            raise ValueError(
                f"{handler_type.__module__}.{handler_type.__qualname__} "
                "has an empty query_handler_key."
            )

        return handler_key

    def _validate_query_type(
        self,
        query_type: type[Query],
    ) -> None:
        if not isinstance(query_type, type):
            raise TypeError(f"Query type must be a type, got {query_type!r}.")

        if not issubclass(query_type, Query):
            raise TypeError(
                f"{query_type.__name__} must inherit from Query."
            )

    def _validate_handler_type(
        self,
        handler_type: type[QueryHandler],
    ) -> None:
        if not isinstance(handler_type, type):
            raise TypeError(f"Handler type must be a type, got {handler_type!r}.")

        if not issubclass(handler_type, QueryHandler):
            raise TypeError(
                f"{handler_type.__name__} must inherit from QueryHandler."
            )

        if inspect.isabstract(handler_type):
            raise TypeError(
                f"{handler_type.__name__} is abstract and cannot be registered."
            )

    def _normalize_group(
        self,
        group: QueryHandlerGroupName,
    ) -> str | None:
        if group is None:
            return None

        return str(group)