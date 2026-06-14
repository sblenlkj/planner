from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class UserRuntimeStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"
    DISABLED = "disabled"


@dataclass(slots=True)
class UserRuntimeProfile:
    user_id: UUID
    status: UserRuntimeStatus = UserRuntimeStatus.NOT_READY
    last_session_at: datetime | None = None

    @classmethod
    def create_for_user(
        cls,
        *,
        user_id: UUID,
        status: UserRuntimeStatus = UserRuntimeStatus.NOT_READY,
        last_session_at: datetime | None = None,
    ) -> "UserRuntimeProfile":
        return cls(
            user_id=user_id,
            status=status,
            last_session_at=last_session_at,
        )

    def mark_ready(self) -> None:
        self.status = UserRuntimeStatus.READY

    def mark_not_ready(self) -> None:
        self.status = UserRuntimeStatus.NOT_READY

    def disable(self) -> None:
        self.status = UserRuntimeStatus.DISABLED

    def register_session(
        self,
        *,
        happened_at: datetime,
    ) -> None:
        self.last_session_at = happened_at

    @property
    def is_ready(self) -> bool:
        return self.status == UserRuntimeStatus.READY

    @property
    def is_disabled(self) -> bool:
        return self.status == UserRuntimeStatus.DISABLED