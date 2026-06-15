from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from direttore.orchestration.base_types.message import Event

class EventQueue:
    """
    Queue for post-command event orchestration.
    """
    def __init__(self) -> None:
        self._queue = deque()

    def publish(self, message: object) -> None:
        self._queue.append(message)

    push = publish

    def publish_many(self, messages: Iterable[object]) -> None:
        self._queue.extend(messages)

    push_many = publish_many

    def pop(self) -> Event | None:
        if not self.is_empty:
            return self._queue.popleft()
        return None

    @property
    def is_empty(self) -> bool:
        return not self._queue

    def clear(self) -> None:
        self._queue.clear()
