from __future__ import annotations

from typing import Protocol
from uuid import UUID
from datetime import datetime

from backend.context.user.application.dto import UpdateUserDTO
from backend.context.user.domain.user import User
from backend.context.user.domain.user_preferences import UserPreferences
from backend.context.user.domain.user_runtime_profile import (
    UserRuntimeProfile,
    UserRuntimeStatus,
)


class UserRepository(Protocol):
    async def add_user(
        self,
        *,
        user: User,
        utc_offset_minutes: int,
    ) -> None:
        raise NotImplementedError

    async def add_admin(
        self,
        *,
        admin: User,
    ) -> None:
        raise NotImplementedError

    async def get_user_by_id(
        self,
        *,
        user_id: UUID,
    ) -> User | None:
        raise NotImplementedError

    async def get_user_by_login(
        self,
        *,
        login: str,
    ) -> User | None:
        raise NotImplementedError

    async def get_preferences_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> UserPreferences | None:
        raise NotImplementedError

    async def update_user(
        self,
        *,
        update: UpdateUserDTO,
    ) -> None:
        raise NotImplementedError

    async def change_user_utc_offset_minutes(
        self,
        *,
        user_id: UUID,
        utc_offset_minutes: int,
    ) -> None:
        raise NotImplementedError

    async def get_runtime_profile_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> UserRuntimeProfile | None:
        raise NotImplementedError

    async def update_runtime_status(
        self,
        *,
        user_id: UUID,
        status: UserRuntimeStatus,
    ) -> None:
        raise NotImplementedError
    
    async def update_last_session_at(
        self,
        *,
        user_id: UUID,
        last_session_at: datetime,
    ) -> None:
        raise NotImplementedError
    
    async def list_ready_user_ids(self) -> tuple[UUID, ...]:
        raise NotImplementedError