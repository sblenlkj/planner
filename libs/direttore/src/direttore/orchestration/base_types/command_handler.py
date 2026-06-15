from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, Generic, TypeVar

from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
)
from direttore.orchestration.base_types.message import Command
from direttore.orchestration.event_queue import EventQueue


AuthT = TypeVar("AuthT")


@dataclass(slots=True)
class CommandHandlerContext(Generic[AuthT]):
    """
Runtime context passed to every AbstractCommandHandler.

This context represents the command-side execution boundary for a single
command handler call. It is created by the command execution engine and should
be treated as framework-owned runtime state.

Attributes:
    uow:
        Current command Unit of Work.

        The concrete type is application-specific. In a bounded context, users
        normally narrow this field in their own context subclass:

            class WarehouseCommandHandlerContext(
                CommandHandlerContext[ExampleAuth],
            ):
                uow: WarehouseCommandUnitOfWork

        Command handlers use this UoW to access write-side repositories, load
        state needed for command decisions, persist aggregates/entities, and
        participate in the current transaction/session boundary.

        Handlers must not call commit(), rollback(), enter_session(), or
        exit_session() manually. The command execution engine owns the UoW
        lifecycle.

    queue:
        Application event queue for the current command execution.

        Command handlers may push application-level events into this queue when
        orchestration logic explicitly needs to schedule follow-up work:

            context.queue.push(StockReserved(...))

        Domain events should usually be recorded on aggregates and collected
        through TrackingRepository / CommandUnitOfWork. The queue is mainly for
        application/orchestration events created by use-case logic.

    auth:
        Resolved auth object for the current execution, or None when the auth
        pipeline is disabled.

        The concrete auth type is user-defined. A project can narrow it in its
        own context subclass:

            class WarehouseCommandHandlerContext(
                CommandHandlerContext[ExampleAuth],
            ):
                auth: ExampleAuth | None

        If a handler requires authenticated data, it should handle the None case
        explicitly or rely on allowed_access_tags plus a configured access
        checker to reject unauthenticated execution before the handler is called.

CommandHandlerContext is intentionally small. It carries only the execution
objects a command handler needs: write-side UoW, application event queue, and
resolved auth. Dependency-injected services should normally be passed through
the handler constructor, not added to this context.
"""
    uow: AbstractCommandUnitOfWork
    queue: EventQueue
    auth: AuthT | None = None


class CommandHandlerExecutionMode(StrEnum):
    IN_TRANSACTION = "in_transaction"
    AFTER_EXECUTION = "after_execution"


@dataclass(frozen=True, slots=True)
class CommandHandlerConfig:
    execution_mode: CommandHandlerExecutionMode = (
        CommandHandlerExecutionMode.IN_TRANSACTION
    )
    cache_handler: bool = False
    allowed_access_tags: frozenset[str] | None = None


class CommandHandler:
    command_handler_key: ClassVar[str | None] = None


class AbstractCommandHandler(CommandHandler, ABC):
    """
    Base class for regular command handlers.

    Implement this class when a handler executes application write-side logic
    for a Command.

    A command handler is always executed with CommandHandlerContext. The context
    contains the current command Unit of Work, the execution event queue, and the
    resolved auth object for the current request.

    Implementations must override __call__ with this signature:

        async def __call__(
            self,
            command: Command,
            context: CommandHandlerContext[Any],
        ) -> Any:
            ...

    Typical implementation:

        class CreateOrderHandler(AbstractCommandHandler):
            async def __call__(
                self,
                command: CreateOrder,
                context: CommandHandlerContext[AppAuth],
            ) -> CreateOrderResult:
                order = Order.create(...)
                context.uow.orders.add(order)
                return CreateOrderResult(order_id=order.id)

    The handler should not open, commit, rollback, or close sessions manually.
    Transaction/session lifecycle is owned by the execution engine through the
    root CommandUnitOfWork.

    Domain events should be recorded on aggregates or pushed into
    context.queue when explicit application-level event scheduling is required.
    Event dispatching is owned by the command execution engine.
    """

    @abstractmethod
    async def __call__(
        self,
        command: Command,
        context: CommandHandlerContext[Any],
    ) -> Any:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CommandHandlerResult:
    pass


TCommand = TypeVar("TCommand", bound=Command)


class AbstractSagaCommandHandler(ABC, Generic[TCommand]):
    @abstractmethod
    async def __call__(
        self,
        command: TCommand,
        context: CommandHandlerContext[Any],
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def compensate(
        self,
        command: TCommand,
        context: CommandHandlerContext[Any],
    ) -> None:
        raise NotImplementedError