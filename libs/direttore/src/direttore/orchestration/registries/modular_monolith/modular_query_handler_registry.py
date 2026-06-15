from __future__ import annotations

from collections.abc import Iterable

from direttore.orchestration.base_classes.uow import (
    AbstractQueryUnitOfWork,
)
from direttore.orchestration.base_types.message import Query
from direttore.orchestration.registries.service.query_handler_registry import (
    QueryHandlerRegistry,
)


class ModularMonolithQueryHandlerRegistry(QueryHandlerRegistry):
    """
    Internal modular-monolith query registry.

    User code should normally register query handlers in a regular
    QueryHandlerRegistry.

    Modular runtime converts regular registries into this registry by attaching
    root query UoW metadata for every query registration.
    """

    def __init__(self, *, source_name: str | None = None) -> None:
        super().__init__(source_name=source_name)
        self._root_uow_type_by_query_type: dict[
            type[Query],
            type[AbstractQueryUnitOfWork],
        ] = {}

    @classmethod
    def from_registry(
        cls,
        *,
        registry: QueryHandlerRegistry,
        root_uow_type: type[AbstractQueryUnitOfWork],
        source_name: str | None = None,
    ) -> ModularMonolithQueryHandlerRegistry:
        cls._validate_static_uow_type(root_uow_type)

        modular_registry = cls(
            source_name=source_name or registry.source_name,
        )

        for registration in registry.iter_registrations():
            modular_registry._add_registration(registration)
            modular_registry._add_root_uow_type(
                query_type=registration.query_type,
                root_uow_type=root_uow_type,
            )

        return modular_registry

    @classmethod
    def merge_many(
        cls,
        registries: Iterable[ModularMonolithQueryHandlerRegistry],
        *,
        source_name: str | None = None,
    ) -> ModularMonolithQueryHandlerRegistry:
        merged = cls(source_name=source_name)

        for registry in registries:
            for registration in registry.iter_registrations():
                merged._add_registration(registration)

            for query_type, root_uow_type in (
                registry._root_uow_type_by_query_type.items()
            ):
                merged._add_root_uow_type(
                    query_type=query_type,
                    root_uow_type=root_uow_type,
                )

        return merged

    @classmethod
    def from_registries(
        cls,
        contexts: Iterable[
            tuple[QueryHandlerRegistry, type[AbstractQueryUnitOfWork]]
        ],
        *,
        source_name: str | None = None,
    ) -> ModularMonolithQueryHandlerRegistry:
        return cls.merge_many(
            (
                cls.from_registry(
                    registry=registry,
                    root_uow_type=root_uow_type,
                )
                for registry, root_uow_type in contexts
            ),
            source_name=source_name,
        )

    def get_root_uow_type_by_query_type(
        self,
        query_type: type[Query],
    ) -> type[AbstractQueryUnitOfWork]:
        self._validate_query_type(query_type)

        root_uow_type = self._root_uow_type_by_query_type.get(query_type)

        if root_uow_type is None:
            raise LookupError(
                "No root query unit-of-work type registered for query. "
                f"Query={query_type.__module__}.{query_type.__qualname__}."
            )

        return root_uow_type

    def get_root_uow_type(
        self,
        query: Query,
    ) -> type[AbstractQueryUnitOfWork]:
        return self.get_root_uow_type_by_query_type(type(query))

    def _add_root_uow_type(
        self,
        *,
        query_type: type[Query],
        root_uow_type: type[AbstractQueryUnitOfWork],
    ) -> None:
        self._validate_query_type(query_type)
        self._validate_uow_type(root_uow_type)

        existing_root_uow_type = self._root_uow_type_by_query_type.get(
            query_type
        )

        if (
            existing_root_uow_type is not None
            and existing_root_uow_type is not root_uow_type
        ):
            raise ValueError(
                "Duplicate root query unit-of-work type registration. "
                f"Query={query_type.__module__}.{query_type.__qualname__}, "
                f"existing_uow={existing_root_uow_type.__module__}."
                f"{existing_root_uow_type.__qualname__}, "
                f"new_uow={root_uow_type.__module__}.{root_uow_type.__qualname__}."
            )

        self._root_uow_type_by_query_type[query_type] = root_uow_type

    def _validate_uow_type(
        self,
        uow_type: type[AbstractQueryUnitOfWork],
    ) -> None:
        self._validate_static_uow_type(uow_type)

    @staticmethod
    def _validate_static_uow_type(
        uow_type: type[AbstractQueryUnitOfWork],
    ) -> None:
        if not isinstance(uow_type, type):
            raise TypeError(f"UoW type must be a type, got {uow_type!r}.")

        if not issubclass(uow_type, AbstractQueryUnitOfWork):
            raise TypeError(
                f"{uow_type.__module__}.{uow_type.__qualname__} "
                "must inherit from AbstractQueryUnitOfWork."
            )