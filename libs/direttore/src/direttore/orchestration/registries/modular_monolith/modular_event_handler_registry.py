from __future__ import annotations

from collections.abc import Iterable

from direttore.orchestration.base_classes import (
    AbstractCommandUnitOfWork,
)
from direttore.orchestration.base_types.event_handler import (
    EventHandler,
)
from direttore.orchestration.registries.service.event_handler_registry import (
    EventHandlerRegistry,
)


class ModularMonolithEventHandlerRegistry(EventHandlerRegistry):
    """
    Internal modular-monolith event registry.

    User code should normally register event handlers in a regular
    EventHandlerRegistry.

    Modular runtime converts regular registries into this registry by attaching
    root UoW metadata for every event handler registration.
    """

    def __init__(self, *, source_name: str | None = None) -> None:
        super().__init__(source_name=source_name)
        self._root_uow_type_by_handler_type: dict[
            type[EventHandler],
            type[AbstractCommandUnitOfWork],
        ] = {}

    @classmethod
    def from_registry(
        cls,
        *,
        registry: EventHandlerRegistry,
        root_uow_type: type[AbstractCommandUnitOfWork],
        source_name: str | None = None,
    ) -> ModularMonolithEventHandlerRegistry:
        cls._validate_static_uow_type(root_uow_type)

        modular_registry = cls(
            source_name=source_name or registry.source_name,
        )

        for registration in registry.iter_registrations(
            include_not_ready=True,
        ):
            modular_registry._add_registration(registration)
            modular_registry._add_root_uow_type(
                handler_type=registration.handler_type,
                root_uow_type=root_uow_type,
            )

        return modular_registry

    @classmethod
    def merge_many(
        cls,
        registries: Iterable[ModularMonolithEventHandlerRegistry],
        *,
        source_name: str | None = None,
    ) -> ModularMonolithEventHandlerRegistry:
        merged = cls(source_name=source_name)

        for registry in registries:
            for registration in registry.iter_registrations(
                include_not_ready=True,
            ):
                merged._add_registration(registration)

            for handler_type, root_uow_type in (
                registry._root_uow_type_by_handler_type.items()
            ):
                merged._add_root_uow_type(
                    handler_type=handler_type,
                    root_uow_type=root_uow_type,
                )

        return merged

    @classmethod
    def from_registries(
        cls,
        contexts: Iterable[
            tuple[EventHandlerRegistry, type[AbstractCommandUnitOfWork]]
        ],
        *,
        source_name: str | None = None,
    ) -> ModularMonolithEventHandlerRegistry:
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

    def get_root_uow_type_by_handler_type(
        self,
        handler_type: type[EventHandler],
    ) -> type[AbstractCommandUnitOfWork]:
        self._validate_handler_type(handler_type)

        root_uow_type = self._root_uow_type_by_handler_type.get(handler_type)

        if root_uow_type is None:
            raise LookupError(
                "No root unit-of-work type registered for event handler. "
                f"Handler={handler_type.__module__}.{handler_type.__qualname__}."
            )

        return root_uow_type

    def get_root_uow_type_by_handler(
        self,
        handler: EventHandler,
    ) -> type[AbstractCommandUnitOfWork]:
        return self.get_root_uow_type_by_handler_type(type(handler))

    def _add_root_uow_type(
        self,
        *,
        handler_type: type[EventHandler],
        root_uow_type: type[AbstractCommandUnitOfWork],
    ) -> None:
        self._validate_handler_type(handler_type)
        self._validate_uow_type(root_uow_type)

        existing_root_uow_type = self._root_uow_type_by_handler_type.get(
            handler_type
        )

        if (
            existing_root_uow_type is not None
            and existing_root_uow_type is not root_uow_type
        ):
            raise ValueError(
                "Duplicate root unit-of-work type registration for event handler. "
                f"Handler={handler_type.__module__}.{handler_type.__qualname__}, "
                f"existing_uow={existing_root_uow_type.__module__}."
                f"{existing_root_uow_type.__qualname__}, "
                f"new_uow={root_uow_type.__module__}.{root_uow_type.__qualname__}."
            )

        self._root_uow_type_by_handler_type[handler_type] = root_uow_type

    def _validate_uow_type(
        self,
        uow_type: type[AbstractCommandUnitOfWork],
    ) -> None:
        self._validate_static_uow_type(uow_type)

    @staticmethod
    def _validate_static_uow_type(
        uow_type: type[AbstractCommandUnitOfWork],
    ) -> None:
        if not isinstance(uow_type, type):
            raise TypeError(f"UoW type must be a type, got {uow_type!r}.")

        if not issubclass(uow_type, AbstractCommandUnitOfWork):
            raise TypeError(
                f"{uow_type.__module__}.{uow_type.__qualname__} "
                "must inherit from AbstractOrchestrationUnitOfWork."
            )