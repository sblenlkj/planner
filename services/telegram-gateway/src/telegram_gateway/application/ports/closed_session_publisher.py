from typing import Protocol

from telegram_gateway.domain.events import ClosedSessionEvent


class ClosedSessionPublisher(Protocol):
    async def publish_closed_session(
        self,
        event: ClosedSessionEvent,
    ) -> None:
        raise NotImplementedError
