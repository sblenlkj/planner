from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, TypeVar

from direttore.orchestration.base_types.command_handler import (
    CommandHandler,
    CommandHandlerConfig,
)
from direttore.orchestration.base_types.message import Command


class HandlerGroup(StrEnum):
    REST = "rest"
    CONSUMER = "consumer"
    INTERNAL = "internal"


HandlerGroupName = HandlerGroup | str | None


TCommandHandler = TypeVar(
    "TCommandHandler",
    bound=type[CommandHandler],
)


@dataclass(frozen=True, slots=True)
class CommandHandlerRegistration:
    command_type: type[Command]
    handler_type: type[CommandHandler]
    group: str | None = None # TODO we do not use the group
    key: str | None = None
    source_name: str | None = None
    config: CommandHandlerConfig = field(default_factory=CommandHandlerConfig)


class CommandHandlerRegistryPort(Protocol):
    def get_registration(
        self,
        command: Command,
    ) -> CommandHandlerRegistration:
        raise NotImplementedError

    def get_registration_by_command_type(
        self,
        command_type: type[Command],
    ) -> CommandHandlerRegistration:
        raise NotImplementedError

    def get_registration_by_key(
        self,
        key: str,
    ) -> CommandHandlerRegistration:
        raise NotImplementedError

    def iter_registrations(
        self,
        *,
        group: HandlerGroupName = None,
    ) -> list[CommandHandlerRegistration]:
        raise NotImplementedError

    def iter_handler_types(
        self,
        *,
        group: HandlerGroupName = None,
    ) -> list[type[CommandHandler]]:
        raise NotImplementedError


class CommandHandlerRegistry(CommandHandlerRegistryPort):
    def __init__(
        self,
        *,
        source_name: str | None = None,
    ) -> None:
        self.source_name = source_name

        self._registrations_by_command: dict[
            type[Command],
            CommandHandlerRegistration,
        ] = {}

        self._registrations_by_key: dict[
            str,
            CommandHandlerRegistration,
        ] = {}

        self._registrations_by_group: dict[
            str | None,
            list[CommandHandlerRegistration],
        ] = defaultdict(list)

        self._registrations: list[CommandHandlerRegistration] = []

    def handler(
        self,
        command_type: type[Command],
        *,
        group: HandlerGroupName = None,
        key: str | None = None,
        register_key: bool = False,
        config: CommandHandlerConfig | None = None,
    ):
        self._validate_command_type(command_type)

        def decorator(handler_type: TCommandHandler) -> TCommandHandler:
            self.register(
                command_type=command_type,
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
        command_type: type[Command],
        handler_type: type[CommandHandler],
        group: HandlerGroupName = None,
        key: str | None = None,
        register_key: bool = False,
        config: CommandHandlerConfig | None = None,
    ) -> None:
        self._validate_command_type(command_type)
        self._validate_handler_type(handler_type)

        resolved_key = self._resolve_key(
            handler_type=handler_type,
            key=key,
            register_key=register_key,
        )

        self._add_registration(
            CommandHandlerRegistration(
                command_type=command_type,
                handler_type=handler_type,
                group=self._normalize_group(group),
                key=resolved_key,
                source_name=self.source_name,
                config=config or CommandHandlerConfig(),
            )
        )

    def get_registration(
        self,
        command: Command,
    ) -> CommandHandlerRegistration:
        return self.get_registration_by_command_type(type(command))

    def get_registration_by_command_type(
        self,
        command_type: type[Command],
    ) -> CommandHandlerRegistration:
        self._validate_command_type(command_type)

        registration = self._registrations_by_command.get(command_type)

        if registration is None:
            raise LookupError(
                f"No command handler registered for command "
                f"{command_type.__module__}.{command_type.__qualname__}."
            )

        return registration

    def get_registration_by_key(
        self,
        key: str,
    ) -> CommandHandlerRegistration:
        if not key:
            raise ValueError("Command handler key must not be empty.")

        registration = self._registrations_by_key.get(key)

        if registration is None:
            raise LookupError(
                f"No command handler registered for key {key!r}."
            )

        return registration

    def get_handler_type(
        self,
        command: Command,
    ) -> type[CommandHandler]:
        return self.get_registration(command).handler_type

    def get_handler_type_by_command_type(
        self,
        command_type: type[Command],
    ) -> type[CommandHandler]:
        return self.get_registration_by_command_type(command_type).handler_type

    def get_handler_type_by_key(
        self,
        key: str,
    ) -> type[CommandHandler]:
        return self.get_registration_by_key(key).handler_type

    def iter_registrations(
        self,
        *,
        group: HandlerGroupName = None,
    ) -> list[CommandHandlerRegistration]:
        normalized_group = self._normalize_group(group)

        if normalized_group is not None:
            return list(self._registrations_by_group.get(normalized_group, []))

        return list(self._registrations)

    def iter_handler_types(
        self,
        *,
        group: HandlerGroupName = None,
    ) -> list[type[CommandHandler]]:
        return [
            registration.handler_type
            for registration in self.iter_registrations(group=group)
        ]

    def iter_command_types(
        self,
        *,
        group: HandlerGroupName = None,
    ) -> list[type[Command]]:
        return [
            registration.command_type
            for registration in self.iter_registrations(group=group)
        ]

    def filter_by_group(
        self,
        group: HandlerGroupName,
        *,
        source_name: str | None = None,
    ) -> CommandHandlerRegistry:
        filtered = CommandHandlerRegistry(
            source_name=source_name,
        )

        for registration in self.iter_registrations(group=group):
            filtered._add_registration(registration)

        return filtered

    @classmethod
    def from_mapping(
        cls,
        mapping: dict[type[Command], type[CommandHandler]],
        *,
        source_name: str | None = None,
        group: HandlerGroupName = None,
        register_key: bool = False,
        config: CommandHandlerConfig | None = None,
    ) -> CommandHandlerRegistry:
        registry = cls(
            source_name=source_name,
        )

        for command_type, handler_type in mapping.items():
            registry.register(
                command_type=command_type,
                handler_type=handler_type,
                group=group,
                register_key=register_key,
                config=config,
            )

        return registry

    @classmethod
    def merge_many(
        cls,
        registries: Iterable[CommandHandlerRegistry],
        *,
        source_name: str | None = None,
    ) -> CommandHandlerRegistry:
        merged = cls(source_name=source_name)

        for registry in registries:
            for registration in registry.iter_registrations():
                merged._add_registration(registration)

        return merged

    def _add_registration(
        self,
        registration: CommandHandlerRegistration,
    ) -> None:
        existing_command_registration = self._registrations_by_command.get(
            registration.command_type
        )

        if existing_command_registration is not None:
            raise ValueError(
                "Duplicate command handler registration. "
                f"Command={registration.command_type.__module__}."
                f"{registration.command_type.__qualname__}, "
                f"existing_handler={existing_command_registration.handler_type.__module__}."
                f"{existing_command_registration.handler_type.__qualname__}, "
                f"new_handler={registration.handler_type.__module__}."
                f"{registration.handler_type.__qualname__}, "
                f"existing_source={existing_command_registration.source_name!r}, "
                f"new_source={registration.source_name!r}."
            )

        if registration.key is not None:
            existing_key_registration = self._registrations_by_key.get(
                registration.key
            )

            if existing_key_registration is not None:
                raise ValueError(
                    "Duplicate command handler key registration. "
                    f"Key={registration.key!r}, "
                    f"existing_command={existing_key_registration.command_type.__module__}."
                    f"{existing_key_registration.command_type.__qualname__}, "
                    f"new_command={registration.command_type.__module__}."
                    f"{registration.command_type.__qualname__}, "
                    f"existing_handler={existing_key_registration.handler_type.__module__}."
                    f"{existing_key_registration.handler_type.__qualname__}, "
                    f"new_handler={registration.handler_type.__module__}."
                    f"{registration.handler_type.__qualname__}, "
                    f"existing_source={existing_key_registration.source_name!r}, "
                    f"new_source={registration.source_name!r}."
                )

            self._registrations_by_key[registration.key] = registration

        self._registrations_by_command[registration.command_type] = registration
        self._registrations_by_group[registration.group].append(registration)
        self._registrations.append(registration)

    def _resolve_key(
        self,
        *,
        handler_type: type[CommandHandler],
        key: str | None,
        register_key: bool,
    ) -> str | None:
        if key is not None:
            if not key:
                raise ValueError("Command handler key must not be empty.")

            return key

        if not register_key:
            return None

        handler_key = handler_type.command_handler_key

        if handler_key is None:
            raise ValueError(
                f"{handler_type.__module__}.{handler_type.__qualname__} "
                "cannot be registered by key because command_handler_key is not set."
            )

        if not handler_key:
            raise ValueError(
                f"{handler_type.__module__}.{handler_type.__qualname__} "
                "has an empty command_handler_key."
            )

        return handler_key

    def _validate_command_type(
        self,
        command_type: type[Command],
    ) -> None:
        if not isinstance(command_type, type):
            raise TypeError(f"Command type must be a type, got {command_type!r}.")

        if not issubclass(command_type, Command):
            raise TypeError(
                f"{command_type.__name__} must inherit from Command."
            )

    def _validate_handler_type(
        self,
        handler_type: type[CommandHandler],
    ) -> None:
        if not isinstance(handler_type, type):
            raise TypeError(f"Handler type must be a type, got {handler_type!r}.")

        if not issubclass(handler_type, CommandHandler):
            raise TypeError(
                f"{handler_type.__name__} must inherit from CommandHandler."
            )

        if inspect.isabstract(handler_type):
            raise TypeError(
                f"{handler_type.__name__} is abstract and cannot be registered."
            )

    def _normalize_group(
        self,
        group: HandlerGroupName,
    ) -> str | None:
        if group is None:
            return None

        return str(group)