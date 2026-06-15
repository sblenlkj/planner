from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, cast

from direttore.orchestration.modular_monolith.execution_runtime import (
    ModularMonolithExecutionRuntime,
)


TDependency = TypeVar("TDependency", covariant=True)


@dataclass(frozen=True, slots=True)
class ModularMonolithExecutionDependencyContext:
    """
    Runtime context passed to execution-scoped dependency factories.

    Execution-scoped dependencies are created for a concrete modular-monolith
    execution slot. They are used when an application dependency must call other
    bounded contexts in-process instead of going through an external transport.

    Attributes:
        runtime:
            Current modular-monolith runtime.

            In-process clients and facades should use this runtime to call other
            command/query handlers inside the same execution boundary:

                await runtime.invoke(SomeCommand(...))
                await runtime.invoke_query(SomeQuery(...))

            The runtime preserves the current auth context, event queue,
            dependency overrides, and Unit of Work coordinator. This allows a
            dependency such as WarehouseClient to behave like a service client
            while still participating in the current modular-monolith execution.
    """

    runtime: ModularMonolithExecutionRuntime


class ModularMonolithExecutionDependencyFactory(Protocol[TDependency]):
    def __call__(
        self,
        context: ModularMonolithExecutionDependencyContext,
    ) -> TDependency:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ModularMonolithExecutionDependencyRegistration:
    dependency_type: type[Any]
    factory: ModularMonolithExecutionDependencyFactory[Any]


class ModularMonolithExecutionDependencyRegistry:
    """
    Registry for modular-monolith execution-scoped dependency overrides.

    This registry is used by the modular execution slot to build dependencies
    that must be bound to the current execution runtime.

    Typical use case:
        In production, Orders depends on a WarehouseClient that calls Warehouse
        over HTTP/gRPC/message bus.

        In a modular monolith, Orders can depend on the same WarehouseClient
        port, but the implementation is an in-process adapter built from the
        current ModularMonolithExecutionRuntime.

    Example:

        registry = ModularMonolithExecutionDependencyRegistry()

        @registry.override(WarehouseClient)
        def build_warehouse_client(
            context: ModularMonolithExecutionDependencyContext,
        ) -> WarehouseClient:
            return InProcessWarehouseClient(
                facade=WarehouseInProcessFacade(
                    runtime=context.runtime,
                ),
            )

    At runtime:
        1. Execution slot creates ModularMonolithExecutionRuntime.
        2. Execution slot calls build_overrides(...).
        3. Resolver uses these overrides before falling back to the application
           container.
        4. Handlers receive execution-scoped in-process clients through normal
           constructor autowiring.

    Dependencies registered here should usually be lightweight wrappers around
    runtime. App-scope dependencies that do not need runtime should stay in the
    regular Container.
    """

    def __init__(self) -> None:
        self._registrations: dict[
            type[Any],
            ModularMonolithExecutionDependencyRegistration,
        ] = {}

    def override(
        self,
        dependency_type: type[TDependency],
    ) -> Callable[
        [ModularMonolithExecutionDependencyFactory[TDependency]],
        ModularMonolithExecutionDependencyFactory[TDependency],
    ]:
        self._validate_dependency_type(dependency_type)

        def decorator(
            factory: ModularMonolithExecutionDependencyFactory[TDependency],
        ) -> ModularMonolithExecutionDependencyFactory[TDependency]:
            self.register(
                dependency_type=dependency_type,
                factory=factory,
            )
            return factory

        return decorator

    def register(
        self,
        *,
        dependency_type: type[TDependency],
        factory: ModularMonolithExecutionDependencyFactory[TDependency],
    ) -> None:
        self._validate_dependency_type(dependency_type)

        if dependency_type in self._registrations:
            raise ValueError(
                "Execution dependency override is already registered. "
                f"Dependency={dependency_type.__module__}."
                f"{dependency_type.__qualname__}."
            )

        self._registrations[dependency_type] = (
            ModularMonolithExecutionDependencyRegistration(
                dependency_type=dependency_type,
                factory=cast(
                    ModularMonolithExecutionDependencyFactory[Any],
                    factory,
                ),
            )
        )

    def build_overrides(
        self,
        *,
        context: ModularMonolithExecutionDependencyContext,
    ) -> Mapping[type[Any], Any]:
        return {
            dependency_type: registration.factory(context)
            for dependency_type, registration in self._registrations.items()
        }

    def iter_dependency_types(self) -> list[type[Any]]:
        return list(self._registrations.keys())

    def _validate_dependency_type(
        self,
        dependency_type: type[Any],
    ) -> None:
        if not isinstance(dependency_type, type):
            raise TypeError(
                f"Dependency type must be a type, got {dependency_type!r}."
            )