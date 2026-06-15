from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from direttore.orchestration.base_classes.uow import (
    AbstractCommandUnitOfWork,
)
from direttore.orchestration.base_types.message import Event


@dataclass(slots=True)
class EventHandlerContext:
    command_uow: AbstractCommandUnitOfWork | None = None


class EventHandlerKind(StrEnum):
    EVENT = "event"
    CONTEXT_EVENT = "context_event"


class EventHandler:
    event_handler_kind: ClassVar[EventHandlerKind]


class AbstractEventHandler(EventHandler, ABC):
    event_handler_kind = EventHandlerKind.EVENT

    @abstractmethod
    async def __call__(self, event: Event) -> None:
        raise NotImplementedError


class AbstractContextEventHandler(EventHandler, ABC):
    event_handler_kind = EventHandlerKind.CONTEXT_EVENT

    @abstractmethod
    async def __call__(
        self,
        event: Event,
        context: EventHandlerContext,
    ) -> None:
        raise NotImplementedError