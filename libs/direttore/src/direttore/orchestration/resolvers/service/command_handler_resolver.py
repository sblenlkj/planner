from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, get_type_hints

from direttore.orchestration.base_types.command_handler import (
    CommandHandler,
    CommandHandlerExecutionMode,
)
from direttore.orchestration.base_types.message import Command
from direttore.orchestration.registries.service.command_handler_registry import (
    CommandHandlerRegistration,
    CommandHandlerRegistryPort,
    HandlerGroupName,
)
from direttore.orchestration.resolvers.container import Container


TCommandHandler = TypeVar("TCommandHandler", bound=CommandHandler)


@dataclass(frozen=True, slots=True)
class ResolvedCommandHandlerConfig:
    command_type: type[Command]
    execution_mode: CommandHandlerExecutionMode
    allowed_access_tags: frozenset[str] | None = None
    source_name: str | None = None
    key: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedCommandHandler:
    handler: CommandHandler
    config: ResolvedCommandHandlerConfig


class CommandHandlerResolverPort(Protocol):
    def validate_command_handlers(
        self,
        *,
        group: HandlerGroupName = None,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        raise NotImplementedError

    def resolve(
        self,
        command: Command,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedCommandHandler:
        raise NotImplementedError

    def resolve_by_key(
        self,
        key: str,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedCommandHandler:
        raise NotImplementedError


class AbstractCommandHandlerResolver(CommandHandlerResolverPort, ABC):
    def __init__(self, registry: CommandHandlerRegistryPort) -> None:
        self._registry = registry

    @property
    def registry(self) -> CommandHandlerRegistryPort:
        return self._registry

    def validate_command_handlers(
        self,
        *,
        group: HandlerGroupName = None,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        seen: set[type[CommandHandler]] = set()
        print(overrides)

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
        command: Command,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedCommandHandler:
        registration = self._registry.get_registration_by_command_type(
            type(command),
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
    ) -> ResolvedCommandHandler:
        registration = self._registry.get_registration_by_key(key)

        return self._resolve_registration(
            registration=registration,
            overrides=overrides,
        )

    def _resolve_registration(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None,
    ) -> ResolvedCommandHandler:
        self._validate_registration(registration)

        registration.source_name

        return ResolvedCommandHandler(
            handler=self._resolve_handler(
                registration=registration,
                overrides=overrides,
            ),
            config=ResolvedCommandHandlerConfig(
                command_type=registration.command_type,
                execution_mode=registration.config.execution_mode,
                allowed_access_tags=registration.config.allowed_access_tags,
                source_name=registration.source_name,
                key=registration.key,
            ),
        )

    def _validate_registration(
        self,
        registration: CommandHandlerRegistration,
    ) -> None:
        return 

        if registration.allowed_access_tags is None:
            raise RuntimeError(
                "Command handler registration has no allowed_access_tags. "
                f"Command={registration.command_type.__module__}."
                f"{registration.command_type.__qualname__}, "
                f"handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}."
            )

        if not registration.allowed_access_tags:
            raise RuntimeError(
                "Command handler registration has empty allowed_access_tags. "
                f"Command={registration.command_type.__module__}."
                f"{registration.command_type.__qualname__}, "
                f"handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}."
            )

    @abstractmethod
    def _resolve_handler(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> CommandHandler:
        raise NotImplementedError

    @abstractmethod
    def _validate_handler(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        raise NotImplementedError


class ContainerCommandHandlerResolver(AbstractCommandHandlerResolver):
    def __init__(
        self,
        *,
        registry: CommandHandlerRegistryPort,
        container: Container,
    ) -> None:
        super().__init__(registry)
        self._container = container

    def _resolve_handler(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> CommandHandler:
        if overrides is not None:
            raise RuntimeError(
                "ContainerCommandHandlerResolver does not support execution "
                "dependency overrides. Use AutoWiringCommandHandlerResolver."
            )

        return self._container.get(registration.handler_type)

    def _validate_handler(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        if overrides is not None:
            raise RuntimeError(
                "ContainerCommandHandlerResolver does not support execution "
                "dependency overrides. Use AutoWiringCommandHandlerResolver."
            )

        self._container.get(registration.handler_type)


class AutoWiringCommandHandlerResolver(AbstractCommandHandlerResolver):
    def __init__(
        self,
        *,
        registry: CommandHandlerRegistryPort,
        container: Container,
    ) -> None:
        super().__init__(registry)
        self._container = container
        self._cache: dict[type[CommandHandler], CommandHandler] = {}

    def _resolve_handler(
        self,
        *,
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> CommandHandler:
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
        registration: CommandHandlerRegistration,
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
        handler_type: type[CommandHandler],
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
        handler_type: type[CommandHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> CommandHandler:
        kwargs = self._resolve_init_kwargs(
            handler_type=handler_type,
            overrides=overrides,
        )

        return handler_type(**kwargs)

    def _resolve_init_kwargs(
        self,
        *,
        handler_type: type[CommandHandler],
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
        handler_type: type[CommandHandler],
    ) -> set[type[Any]]:
        return {
            dependency_type
            for _, dependency_type in self._iter_init_dependencies(handler_type)
        }

    def _iter_init_dependencies(
        self,
        handler_type: type[CommandHandler],
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


class WarmUpCacheAutoWiringCommandHandlerResolver(
    AbstractCommandHandlerResolver,
):
    """
    Auto-wiring resolver with eager cache warm-up.

    This resolver always warms up cache for all handlers that are explicitly
    marked as cacheable and do not depend on execution-scoped dependency types.

    Runtime resolve path is intentionally simple:

    - if handler was warmed up and cached, return it;
    - otherwise build a new handler instance.

    It does not decide at runtime whether a handler should be cached. Cache
    eligibility is decided during warm-up.
    """

    def __init__(
        self,
        *,
        registry: CommandHandlerRegistryPort,
        container: Container,
        execution_dependency_types: set[type[Any]] | None = None,
    ) -> None:
        super().__init__(registry)
        self._container = container
        self._execution_dependency_types = execution_dependency_types or set()
        self._cache: dict[type[CommandHandler], CommandHandler] = {}

        self.__bug = {k: None for k in self._execution_dependency_types}
        # Full validation may require execution-scoped overrides.
        # It should be called by the composition/runtime layer when overrides are available.
        # self.validate_command_handlers()

        self.warm_up_cache()

    def warm_up_cache(self) -> None:
        for registration in self._registry.iter_registrations():
            self._warm_up_registration_cache(registration)

    def _warm_up_registration_cache(
        self,
        registration: CommandHandlerRegistration,
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
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> CommandHandler:
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
        registration: CommandHandlerRegistration,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> None:
        self._resolve_init_kwargs(
            handler_type=registration.handler_type,
            overrides=self.__bug,
        )

    def _create_handler(
        self,
        *,
        handler_type: type[CommandHandler],
        overrides: Mapping[type[Any], Any] | None,
    ) -> CommandHandler:
        kwargs = self._resolve_init_kwargs(
            handler_type=handler_type,
            overrides=overrides,
        )

        return handler_type(**kwargs)

    def _resolve_init_kwargs(
        self,
        *,
        handler_type: type[CommandHandler],
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
        handler_type: type[CommandHandler],
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
        handler_type: type[CommandHandler],
    ) -> set[type[Any]]:
        return {
            dependency_type
            for _, dependency_type in self._iter_init_dependencies(handler_type)
        }

    def _iter_init_dependencies(
        self,
        handler_type: type[CommandHandler],
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