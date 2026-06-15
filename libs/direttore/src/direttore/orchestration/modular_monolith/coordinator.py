from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar, cast

from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
    AbstractQueryUnitOfWork,
    AbstractUnitOfWork,
)
from direttore.orchestration.base_types.message import DomainEvent


TCommandUnitOfWork = TypeVar(
    "TCommandUnitOfWork",
    bound=AbstractCommandUnitOfWork,
)
TQueryUnitOfWork = TypeVar(
    "TQueryUnitOfWork",
    bound=AbstractQueryUnitOfWork,
)


class ModularUnitOfWorkCoordinator:
    def __init__(self) -> None:
        self._command_uow_factories: dict[
            type[AbstractCommandUnitOfWork],
            Callable[[], AbstractCommandUnitOfWork],
        ] = {}
        self._query_uow_factories: dict[
            type[AbstractQueryUnitOfWork],
            Callable[[], AbstractQueryUnitOfWork],
        ] = {}

        self._command_uows: dict[
            type[AbstractCommandUnitOfWork],
            AbstractCommandUnitOfWork,
        ] = {}
        self._query_uows: dict[
            type[AbstractQueryUnitOfWork],
            AbstractQueryUnitOfWork,
        ] = {}

    def set_command_uow_factory(
        self,
        uow_type: type[TCommandUnitOfWork],
        factory: Callable[[], TCommandUnitOfWork],
    ) -> None:
        self._validate_command_uow_type(uow_type)

        existing_factory = self._command_uow_factories.get(uow_type)

        if existing_factory is not None:
            raise ValueError(
                "Command unit-of-work factory is already registered. "
                f"UoW={uow_type.__module__}.{uow_type.__qualname__}."
            )

        self._command_uow_factories[uow_type] = factory

    def set_query_uow_factory(
        self,
        uow_type: type[TQueryUnitOfWork],
        factory: Callable[[], TQueryUnitOfWork],
    ) -> None:
        self._validate_query_uow_type(uow_type)

        existing_factory = self._query_uow_factories.get(uow_type)

        if existing_factory is not None:
            raise ValueError(
                "Query unit-of-work factory is already registered. "
                f"UoW={uow_type.__module__}.{uow_type.__qualname__}."
            )

        self._query_uow_factories[uow_type] = factory

    def get_command_uow(
        self,
        uow_type: type[TCommandUnitOfWork],
    ) -> TCommandUnitOfWork:
        self._validate_command_uow_type(uow_type)

        uow = self._command_uows.get(uow_type)

        if uow is not None:
            return cast(TCommandUnitOfWork, uow)

        factory = self._command_uow_factories.get(uow_type)

        if factory is None:
            raise LookupError(
                "No command unit-of-work factory registered. "
                f"UoW={uow_type.__module__}.{uow_type.__qualname__}."
            )

        created_uow = factory()
        self._command_uows[type(created_uow)] = created_uow

        return cast(TCommandUnitOfWork, created_uow)

    def get_query_uow(
        self,
        uow_type: type[TQueryUnitOfWork],
    ) -> TQueryUnitOfWork:
        self._validate_query_uow_type(uow_type)

        uow = self._query_uows.get(uow_type)

        if uow is not None:
            return cast(TQueryUnitOfWork, uow)

        factory = self._query_uow_factories.get(uow_type)

        if factory is None:
            raise LookupError(
                "No query unit-of-work factory registered. "
                f"UoW={uow_type.__module__}.{uow_type.__qualname__}."
            )

        created_uow = factory()
        self._query_uows[type(created_uow)] = created_uow

        return cast(TQueryUnitOfWork, created_uow)

    def iter_command_unit_of_works(
        self,
    ) -> Iterable[AbstractCommandUnitOfWork]:
        return self._command_uows.values()

    def iter_query_unit_of_works(
        self,
    ) -> Iterable[AbstractQueryUnitOfWork]:
        return self._query_uows.values()

    def iter_unit_of_works(self) -> Iterable[AbstractUnitOfWork]:
        yield from self._command_uows.values()
        yield from self._query_uows.values()

    def collect_new_events(self) -> list[DomainEvent]:
        """
        Collect events from all command UoWs participating in modular execution.

        Query UoWs are intentionally excluded: they do not track aggregates and
        cannot produce domain events.
        """
        events: list[DomainEvent] = []

        for uow in self.iter_command_unit_of_works():
            events.extend(
                uow._collect_new_events_from_tracking_repositories()
            )

        return events

    def clear_tracking(self) -> None:
        """
        Clear tracking state from all command UoWs participating in modular
        execution.

        Query UoWs are intentionally excluded because they do not track
        aggregates.
        """
        for uow in self.iter_command_unit_of_works():
            uow._clear_tracking_repositories()

    def reset(self) -> None:
        self.clear_tracking()
        self._command_uows.clear()
        self._query_uows.clear()

    def _validate_command_uow_type(
        self,
        uow_type: type[AbstractCommandUnitOfWork],
    ) -> None:
        if not isinstance(uow_type, type):
            raise TypeError(f"UoW type must be a type, got {uow_type!r}.")

        if not issubclass(uow_type, AbstractCommandUnitOfWork):
            raise TypeError(
                f"{uow_type.__module__}.{uow_type.__qualname__} "
                "must inherit from AbstractCommandUnitOfWork."
            )

    def _validate_query_uow_type(
        self,
        uow_type: type[AbstractQueryUnitOfWork],
    ) -> None:
        if not isinstance(uow_type, type):
            raise TypeError(f"UoW type must be a type, got {uow_type!r}.")

        if not issubclass(uow_type, AbstractQueryUnitOfWork):
            raise TypeError(
                f"{uow_type.__module__}.{uow_type.__qualname__} "
                "must inherit from AbstractQueryUnitOfWork."
            )