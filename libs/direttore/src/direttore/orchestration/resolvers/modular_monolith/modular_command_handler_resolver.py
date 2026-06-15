from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
)
from direttore.orchestration.base_types.command_handler import (
    CommandHandler,
    CommandHandlerExecutionMode,
)
from direttore.orchestration.base_types.message import Command
from direttore.orchestration.registries.modular_monolith.modular_command_handler_registry import (
    ModularMonolithCommandHandlerRegistry,
)
from direttore.orchestration.resolvers.service.command_handler_resolver import (
    CommandHandlerResolverPort,
)


@dataclass(frozen=True, slots=True)
class ResolvedModularCommandHandlerConfig:
    execution_mode: CommandHandlerExecutionMode
    command_type: type[Command]
    root_uow_type: type[AbstractCommandUnitOfWork]
    allowed_access_tags: frozenset[str] | None = None
    source_name: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedModularCommandHandler:
    handler: CommandHandler
    config: ResolvedModularCommandHandlerConfig


class ModularMonolithCommandHandlerResolverPort(Protocol):
    def validate_command_handlers(self) -> None:
        raise NotImplementedError

    def resolve(
        self,
        command: Command,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularCommandHandler:
        raise NotImplementedError


class ModularMonolithCommandHandlerResolver(
    ModularMonolithCommandHandlerResolverPort,
):
    """
    Adds modular-monolith routing metadata to a normal command handler resolver.

    The wrapped resolver is responsible for creating command handler instances.
    The modular registry is responsible for mapping command types to root
    command UoW types.

    This resolver combines both results for the modular execution slot.
    """

    def __init__(
        self,
        *,
        command_handler_resolver: CommandHandlerResolverPort,
        registry: ModularMonolithCommandHandlerRegistry,
    ) -> None:
        self._command_handler_resolver = command_handler_resolver
        self._registry = registry

    def validate_command_handlers(self) -> None:
        self._command_handler_resolver.validate_command_handlers()

    def resolve(
        self,
        command: Command,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularCommandHandler:
        resolved = self._command_handler_resolver.resolve(
            command,
            overrides=overrides,
        )

        return ResolvedModularCommandHandler(
            handler=resolved.handler,
            config=ResolvedModularCommandHandlerConfig(
                execution_mode=resolved.config.execution_mode,
                command_type=type(command),
                root_uow_type=self._registry.get_root_uow_type(command),
                allowed_access_tags=resolved.config.allowed_access_tags,
                source_name=resolved.config.source_name,
            ),
        )
    
    def resolve_by_key(
        self,
        key: str,
        *,
        overrides: Mapping[type[Any], Any] | None = None,
    ) -> ResolvedModularCommandHandler:
        resolved = self._command_handler_resolver.resolve_by_key(
            key,
            overrides=overrides,
        )

        return ResolvedModularCommandHandler(
            handler=resolved.handler,
            config=ResolvedModularCommandHandlerConfig(
                execution_mode=resolved.config.execution_mode,
                command_type=resolved.config.command_type,
                root_uow_type=self._registry.get_root_uow_type_by_command_type(resolved.config.command_type),
                allowed_access_tags=resolved.config.allowed_access_tags,
                source_name=resolved.config.source_name,
            ),
        )