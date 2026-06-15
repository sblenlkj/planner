from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, Protocol, TypeVar

from direttore.orchestration.auth import (
    AccessCheckerPort,
    AuthResolverPort,
)
from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
)
from direttore.orchestration.base_types.command_handler import (
    AbstractCommandHandler,
    CommandHandler,
    CommandHandlerContext,
    CommandHandlerExecutionMode,
)
from direttore.orchestration.base_types.message import Command, Event
from direttore.orchestration.engines.command_executor_engines.config import (
    ExecutionEngineConfig,
)
from direttore.orchestration.engines.command_executor_engines.exceptions import (
    EventDrainCycleLimitExceeded,
    EventProcessingLimitExceeded,
    UnsupportedCommandExecutionMode,
)
from direttore.orchestration.event_dispatchers.modular_event_dispatcher import (
    ModularMonolithEventDispatcherPort,
)
from direttore.orchestration.event_queue import EventQueue
from direttore.orchestration.modular_monolith.coordinator import (
    ModularUnitOfWorkCoordinator,
)
from direttore.orchestration.tracing import (
    TraceSpanFactoryPort,
    TraceSpanPort,
)


AuthInputT = TypeVar("AuthInputT")
AuthT = TypeVar("AuthT")
TraceT = TypeVar("TraceT")


class ModularMonolithCommandExecutionEnginePort(Protocol):
    def validate_event_handlers(self) -> None:
        raise NotImplementedError

    def reset(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError

    async def handle(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None = None,
        auth_resolver: AuthResolverPort[Any, Any] | None = None,
        auth_input: Any | None = None,
        execution_mode: CommandHandlerExecutionMode | None = None,
        dependency_overrides: Mapping[type[Any], Any] | None = None,
        allowed_access_tags: frozenset[str] | None = None,
        set_runtime_auth: Callable[[Any | None], None] | None = None,
        trace: Any | None = None,
    ) -> Any:
        raise NotImplementedError


class ModularMonolithCommandExecutionEngine(
    ModularMonolithCommandExecutionEnginePort,
    Generic[AuthInputT, AuthT, TraceT],
):
    def __init__(
        self,
        *,
        event_dispatcher: ModularMonolithEventDispatcherPort,
        config: ExecutionEngineConfig | None = None,
        access_checker: AccessCheckerPort[AuthT] | None = None,
        trace_span_factory: TraceSpanFactoryPort[TraceT] | None = None,
    ) -> None:
        self._event_dispatcher = event_dispatcher
        self._config = config or ExecutionEngineConfig()
        self._access_checker = access_checker
        self._trace_span_factory = trace_span_factory

    def validate_event_handlers(self) -> None:
        self._event_dispatcher.validate_event_handlers()

    def reset(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        event_queue: EventQueue,
    ) -> None:
        event_queue.clear()
        coordinator.clear_tracking()

    async def handle(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None = None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None = None,
        auth_input: AuthInputT | None = None,
        execution_mode: CommandHandlerExecutionMode | None = None,
        dependency_overrides: Mapping[type[Any], Any] | None = None,
        allowed_access_tags: frozenset[str] | None = None,
        set_runtime_auth: Callable[[AuthT | None], None] | None = None,
        trace: TraceT | None = None,
    ) -> Any:
        self._validate_auth_configuration(auth_resolver=auth_resolver)

        if self._trace_span_factory is None:
            return await self._handle_without_root_span(
                command=command,
                handler=handler,
                coordinator=coordinator,
                uow=uow,
                event_queue=event_queue,
                source_name=source_name,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                execution_mode=execution_mode,
                dependency_overrides=dependency_overrides,
                allowed_access_tags=allowed_access_tags,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

        return await self._handle_with_root_span(
            command=command,
            handler=handler,
            coordinator=coordinator,
            uow=uow,
            event_queue=event_queue,
            source_name=source_name,
            auth_resolver=auth_resolver,
            auth_input=auth_input,
            execution_mode=execution_mode,
            dependency_overrides=dependency_overrides,
            allowed_access_tags=allowed_access_tags,
            set_runtime_auth=set_runtime_auth,
            trace=trace,
        )

    async def _handle_with_root_span(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        execution_mode: CommandHandlerExecutionMode | None,
        dependency_overrides: Mapping[type[Any], Any] | None,
        allowed_access_tags: frozenset[str] | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
        trace: TraceT | None,
    ) -> Any:
        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="command",
                source_name=source_name,
                message=command,
            ),
            attributes=self._build_command_span_attributes(
                command=command,
                handler=handler,
                source_name=source_name,
            ),
        ):
            return await self._handle_without_root_span(
                command=command,
                handler=handler,
                coordinator=coordinator,
                uow=uow,
                event_queue=event_queue,
                source_name=source_name,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                execution_mode=execution_mode,
                dependency_overrides=dependency_overrides,
                allowed_access_tags=allowed_access_tags,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

    async def _handle_without_root_span(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        execution_mode: CommandHandlerExecutionMode | None,
        dependency_overrides: Mapping[type[Any], Any] | None,
        allowed_access_tags: frozenset[str] | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
        trace: TraceT | None,
    ) -> Any:
        effective_execution_mode = execution_mode or self._config.execution_mode

        if effective_execution_mode == CommandHandlerExecutionMode.IN_TRANSACTION:
            return await self._handle_in_transaction(
                command=command,
                handler=handler,
                coordinator=coordinator,
                uow=uow,
                event_queue=event_queue,
                source_name=source_name,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                dependency_overrides=dependency_overrides,
                allowed_access_tags=allowed_access_tags,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

        if effective_execution_mode == CommandHandlerExecutionMode.AFTER_EXECUTION:
            return await self._handle_after_execution(
                command=command,
                handler=handler,
                coordinator=coordinator,
                uow=uow,
                event_queue=event_queue,
                source_name=source_name,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                dependency_overrides=dependency_overrides,
                allowed_access_tags=allowed_access_tags,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

        raise UnsupportedCommandExecutionMode(
            f"Unsupported command execution mode: {effective_execution_mode!r}."
        )

    def _validate_auth_configuration(
        self,
        *,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
    ) -> None:
        if auth_resolver is None and self._access_checker is not None:
            raise RuntimeError(
                "Access checker is configured, but auth resolver is not configured."
            )

        if auth_resolver is not None and self._access_checker is None:
            raise RuntimeError(
                "Auth resolver is configured, but access checker is not configured."
            )

    async def _prepare_auth(
        self,
        *,
        command: Command,
        source_name: str | None,
        allowed_access_tags: frozenset[str] | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
        trace: TraceT | None,
    ) -> AuthT | None:
        if self._trace_span_factory is None:
            return await self._prepare_auth_without_span(
                command=command,
                allowed_access_tags=allowed_access_tags,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                set_runtime_auth=set_runtime_auth,
            )

        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="auth",
                source_name=source_name,
                message=command,
            ),
            attributes={
                "orchestration.source": source_name,
                "message.kind": "command",
                "message.type": type(command).__qualname__,
                "message.module": type(command).__module__,
                "auth.configured": auth_resolver is not None,
                "access.tags.required": allowed_access_tags is not None,
            },
        ):
            return await self._prepare_auth_without_span(
                command=command,
                allowed_access_tags=allowed_access_tags,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                set_runtime_auth=set_runtime_auth,
            )

    async def _prepare_auth_without_span(
        self,
        *,
        command: Command,
        allowed_access_tags: frozenset[str] | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
    ) -> AuthT | None:
        if auth_resolver is None:
            if auth_input is not None:
                raise RuntimeError(
                    "auth_input was provided, but auth pipeline is not configured."
                )

            if allowed_access_tags is not None:
                raise RuntimeError(
                    "Command requires access tags, but auth pipeline is not "
                    "configured. "
                    f"Command={type(command).__module__}."
                    f"{type(command).__qualname__}."
                )

            if set_runtime_auth is not None:
                set_runtime_auth(None)

            return None

        if auth_input is None:
            raise RuntimeError(
                "Auth resolver is configured, but auth_input was not provided."
            )

        auth = await auth_resolver.resolve_auth(auth_input)

        if auth is None:
            raise RuntimeError(
                "AuthResolver returned None. "
                "Return an explicit public/anonymous auth object instead of None."
            )

        if self._access_checker is None:
            raise RuntimeError(
                "Auth was resolved, but access checker is not configured."
            )

        self._access_checker.check(
            allowed_access_tags=allowed_access_tags,
            auth=auth,
            message=command,
        )

        if set_runtime_auth is not None:
            set_runtime_auth(auth)

        return auth

    async def _handle_in_transaction(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        dependency_overrides: Mapping[type[Any], Any] | None,
        allowed_access_tags: frozenset[str] | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
        trace: TraceT | None,
    ) -> Any:
        async with uow:
            auth = await self._prepare_auth(
                command=command,
                source_name=source_name,
                allowed_access_tags=allowed_access_tags,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

            result = await self._call_handler(
                command=command,
                handler=handler,
                uow=uow,
                event_queue=event_queue,
                auth=auth,
                source_name=source_name,
                trace=trace,
            )

            await self._drain_with_coordinator(
                coordinator=coordinator,
                event_queue=event_queue,
                dependency_overrides=dependency_overrides,
                trace=trace,
            )

            return result

    async def _handle_after_execution(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        coordinator: ModularUnitOfWorkCoordinator,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        source_name: str | None,
        auth_resolver: AuthResolverPort[AuthInputT, AuthT] | None,
        auth_input: AuthInputT | None,
        dependency_overrides: Mapping[type[Any], Any] | None,
        allowed_access_tags: frozenset[str] | None,
        set_runtime_auth: Callable[[AuthT | None], None] | None,
        trace: TraceT | None,
    ) -> Any:
        async with uow:
            auth = await self._prepare_auth(
                command=command,
                source_name=source_name,
                allowed_access_tags=allowed_access_tags,
                auth_resolver=auth_resolver,
                auth_input=auth_input,
                set_runtime_auth=set_runtime_auth,
                trace=trace,
            )

            result = await self._call_handler(
                command=command,
                handler=handler,
                uow=uow,
                event_queue=event_queue,
                auth=auth,
                source_name=source_name,
                trace=trace,
            )

        event_queue.push_many(
            coordinator.collect_new_events()
        )

        await self._drain_queue_only(
            coordinator=coordinator,
            event_queue=event_queue,
            dependency_overrides=dependency_overrides,
            trace=trace,
        )

        return result

    async def _call_handler(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        auth: AuthT | None,
        source_name: str | None,
        trace: TraceT | None,
    ) -> Any:
        if self._trace_span_factory is None:
            return await self._call_handler_without_span(
                command=command,
                handler=handler,
                uow=uow,
                event_queue=event_queue,
                auth=auth,
            )

        async with self._start_span(
            trace=trace,
            name=self._build_span_name(
                operation="command_handler",
                source_name=source_name,
                message=command,
            ),
            attributes=self._build_command_span_attributes(
                command=command,
                handler=handler,
                source_name=source_name,
            ),
        ):
            return await self._call_handler_without_span(
                command=command,
                handler=handler,
                uow=uow,
                event_queue=event_queue,
                auth=auth,
            )

    async def _call_handler_without_span(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        uow: AbstractCommandUnitOfWork,
        event_queue: EventQueue,
        auth: AuthT | None,
    ) -> Any:
        if not isinstance(handler, AbstractCommandHandler):
            raise RuntimeError(
                "Unsupported command handler type. "
                "ModularMonolithCommandExecutionEngine currently supports only "
                "AbstractCommandHandler. "
                f"Handler={type(handler).__module__}."
                f"{type(handler).__qualname__}."
            )

        context = CommandHandlerContext(
            uow=uow,
            queue=event_queue,
            auth=auth,
        )

        return await handler(command, context)

    async def _drain_with_coordinator(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        event_queue: EventQueue,
        dependency_overrides: Mapping[type[Any], Any] | None,
        trace: TraceT | None,
    ) -> None:
        processed_events = 0
        drain_cycles = 0

        while True:
            drain_cycles += 1

            if drain_cycles > self._config.max_drain_cycles:
                raise EventDrainCycleLimitExceeded(
                    "Event drain cycle limit exceeded. "
                    f"Limit={self._config.max_drain_cycles}."
                )

            event_queue.push_many(
                coordinator.collect_new_events()
            )

            if event_queue.is_empty:
                break

            while not event_queue.is_empty:
                processed_events += 1

                if processed_events > self._config.max_processed_events:
                    raise EventProcessingLimitExceeded(
                        "Processed event limit exceeded. "
                        f"Limit={self._config.max_processed_events}."
                    )

                event = event_queue.pop()

                if event is None:
                    break

                await self._dispatch_event(
                    event=event,
                    coordinator=coordinator,
                    dependency_overrides=dependency_overrides,
                    trace=trace,
                )

    async def _drain_queue_only(
        self,
        *,
        coordinator: ModularUnitOfWorkCoordinator,
        event_queue: EventQueue,
        dependency_overrides: Mapping[type[Any], Any] | None,
        trace: TraceT | None,
    ) -> None:
        processed_events = 0

        while not event_queue.is_empty:
            processed_events += 1

            if processed_events > self._config.max_processed_events:
                raise EventProcessingLimitExceeded(
                    "Processed event limit exceeded. "
                    f"Limit={self._config.max_processed_events}."
                )

            event = event_queue.pop()

            if event is None:
                return

            await self._dispatch_event(
                event=event,
                coordinator=coordinator,
                dependency_overrides=dependency_overrides,
                trace=trace,
            )

    async def _dispatch_event(
        self,
        *,
        event: Event,
        coordinator: ModularUnitOfWorkCoordinator,
        dependency_overrides: Mapping[type[Any], Any] | None,
        trace: TraceT | None,
    ) -> None:
        await self._event_dispatcher.dispatch(
            event=event,
            coordinator=coordinator,
            overrides=dependency_overrides,
            trace=trace,
        )

    def _start_span(
        self,
        *,
        trace: TraceT | None,
        name: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[TraceSpanPort]:
        if self._trace_span_factory is None:
            raise RuntimeError(
                "Trace span factory is not configured."
            )

        return self._trace_span_factory.start_span(
            trace=trace,
            name=name,
            attributes=dict(attributes or {}),
        )

    def _build_span_name(
        self,
        *,
        operation: str,
        source_name: str | None,
        message: Command | Event,
    ) -> str:
        message_name = type(message).__qualname__

        if source_name is None:
            return f"orchestration.{operation} {message_name}"

        return f"orchestration.{operation} {source_name}.{message_name}"

    def _build_command_span_attributes(
        self,
        *,
        command: Command,
        handler: CommandHandler,
        source_name: str | None,
    ) -> Mapping[str, Any]:
        return {
            "orchestration.source": source_name,
            "message.kind": "command",
            "message.type": type(command).__qualname__,
            "message.module": type(command).__module__,
            "handler.type": type(handler).__qualname__,
            "handler.module": type(handler).__module__,
        }