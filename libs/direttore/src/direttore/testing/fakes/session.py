from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count


_session_counter = count(1)


class FakeSessionError(RuntimeError):
    pass


@dataclass(slots=True)
class FakeSession:
    session_number: int = field(default_factory=lambda: next(_session_counter))

    is_committed: bool = False
    is_rolled_back: bool = False
    is_closed: bool = False

    commit_count: int = 0
    rollback_count: int = 0
    close_count: int = 0

    def __post_init__(self) -> None:
        print(
            "####### FakeSession created: "
            f"number={self.session_number}, id={id(self)}"
        )

    async def commit(self) -> None:
        if self.is_closed:
            raise FakeSessionError("Cannot commit closed session.")

        if self.is_committed:
            raise FakeSessionError("Session has already been committed.")

        if self.is_rolled_back:
            raise FakeSessionError("Cannot commit rolled back session.")

        self.is_committed = True
        self.commit_count += 1

    async def rollback(self) -> None:
        if self.is_closed:
            raise FakeSessionError("Cannot rollback closed session.")

        if self.is_committed:
            raise FakeSessionError("Cannot rollback committed session.")

        if self.is_rolled_back:
            raise FakeSessionError("Session has already been rolled back.")

        self.is_rolled_back = True
        self.rollback_count += 1

    async def close(self) -> None:
        if self.is_closed:
            raise FakeSessionError("Session has already been closed.")

        self.is_closed = True
        self.close_count += 1

    def reset(self) -> None:
        self.is_committed = False
        self.is_rolled_back = False
        self.is_closed = False

        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0