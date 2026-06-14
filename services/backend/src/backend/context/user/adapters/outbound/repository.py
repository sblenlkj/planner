from __future__ import annotations

from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update as update_sql
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.user.adapters.outbound.models import (
    UserPreferencesRow,
    UserRuntimeProfileRow,
    UserRow,
)
from backend.context.user.application.dto import UpdateUserDTO
from backend.context.user.application.ports import UserRepository
from backend.context.user.domain.user import User, UserRole
from backend.context.user.domain.user_preferences import UserPreferences
from backend.context.user.domain.user_runtime_profile import (
    UserRuntimeProfile,
    UserRuntimeStatus,
)


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_user(
        self,
        *,
        user: User,
    ) -> None:
        if user.role != UserRole.USER:
            raise ValueError("Only regular users can be persisted through add_user.")

        self._session.add(self._to_user_row(user))

        runtime_profile = UserRuntimeProfile.create_for_user(user_id=user.id)
        self._session.add(self._to_runtime_profile_row(runtime_profile))

    async def add_admin(
        self,
        *,
        admin: User,
    ) -> None:
        if admin.role != UserRole.ADMIN:
            raise ValueError("Only admin users can be persisted through add_admin.")

        self._session.add(self._to_user_row(admin))

    async def get_user_by_id(
        self,
        *,
        user_id: UUID,
    ) -> User | None:
        result = await self._session.execute(
            select(UserRow).where(UserRow.id == user_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_user(row)

    async def get_user_by_login(
        self,
        *,
        login: str,
    ) -> User | None:
        normalized_login = login.strip().lower()

        result = await self._session.execute(
            select(UserRow).where(UserRow.login == normalized_login)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_user(row)

    async def get_preferences_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> UserPreferences | None:
        result = await self._session.execute(
            select(UserPreferencesRow).where(
                UserPreferencesRow.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_preferences(row)

    async def update_user(
        self,
        *,
        update: UpdateUserDTO,
    ) -> None:
        user = await self.get_user_by_id(user_id=update.user_id)

        if user is None:
            raise ValueError("User does not exist.")

        user_values: dict[str, str | None] = {}

        if update.login is not None:
            user.change_login(update.login)
            user_values["login"] = user.login

        if update.name is not None:
            user.rename(update.name)
            user_values["name"] = user.name

        if user_values:
            await self._session.execute(
                update_sql(UserRow)
                .where(UserRow.id == update.user_id)
                .values(**user_values)
            )

        has_preferences_update = (
            update.language is not None
            or update.utc_offset_minutes is not None
            or update.region is not None
        )

        if not has_preferences_update:
            return

        preferences = await self.get_preferences_by_user_id(
            user_id=update.user_id,
        )

        if preferences is None:
            if update.utc_offset_minutes is None:
                raise ValueError(
                    "User UTC offset is required to create user preferences."
                )

            created_preferences = UserPreferences.create(
                user_id=update.user_id,
                language=update.language,
                utc_offset_minutes=update.utc_offset_minutes,
                region=update.region,
            )
            self._session.add(self._to_preferences_row(created_preferences))
            return

        updated_preferences = UserPreferences.create(
            user_id=update.user_id,
            language=update.language or preferences.language,
            utc_offset_minutes=(
                update.utc_offset_minutes
                if update.utc_offset_minutes is not None
                else preferences.utc_offset_minutes
            ),
            region=update.region if update.region is not None else preferences.region,
        )

        await self._session.execute(
            update_sql(UserPreferencesRow)
            .where(UserPreferencesRow.user_id == update.user_id)
            .values(
                language=updated_preferences.language,
                utc_offset_minutes=updated_preferences.utc_offset_minutes,
                region=updated_preferences.region,
            )
        )

    async def change_user_utc_offset_minutes(
        self,
        *,
        user_id: UUID,
        utc_offset_minutes: int,
    ) -> None:
        preferences = await self.get_preferences_by_user_id(user_id=user_id)

        if preferences is None:
            raise ValueError("User preferences do not exist.")

        updated_preferences = UserPreferences.create(
            user_id=preferences.user_id,
            language=preferences.language,
            utc_offset_minutes=utc_offset_minutes,
            region=preferences.region,
        )

        await self._session.execute(
            update_sql(UserPreferencesRow)
            .where(UserPreferencesRow.user_id == user_id)
            .values(utc_offset_minutes=updated_preferences.utc_offset_minutes)
        )

    async def get_runtime_profile_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> UserRuntimeProfile | None:
        result = await self._session.execute(
            select(UserRuntimeProfileRow).where(
                UserRuntimeProfileRow.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_runtime_profile(row)

    async def update_runtime_status(
        self,
        *,
        user_id: UUID,
        status: UserRuntimeStatus,
    ) -> None:
        runtime_profile = await self.get_runtime_profile_by_user_id(
            user_id=user_id,
        )

        if runtime_profile is None:
            raise ValueError("User runtime profile does not exist.")

        match status:
            case UserRuntimeStatus.READY:
                runtime_profile.mark_ready()
            case UserRuntimeStatus.NOT_READY:
                runtime_profile.mark_not_ready()
            case UserRuntimeStatus.DISABLED:
                runtime_profile.disable()

        await self._session.execute(
            update_sql(UserRuntimeProfileRow)
            .where(UserRuntimeProfileRow.user_id == user_id)
            .values(status=runtime_profile.status.value)
        )

    async def update_last_session_at(
        self,
        *,
        user_id: UUID,
        last_session_at: datetime,
    ) -> None:
        runtime_profile = await self.get_runtime_profile_by_user_id(
            user_id=user_id,
        )

        if runtime_profile is None:
            raise ValueError("User runtime profile does not exist.")

        runtime_profile.register_session(happened_at=last_session_at)

        await self._session.execute(
            update_sql(UserRuntimeProfileRow)
            .where(UserRuntimeProfileRow.user_id == user_id)
            .values(last_session_at=runtime_profile.last_session_at)
        )

    async def list_ready_user_ids(self) -> tuple[UUID, ...]:
        result = await self._session.execute(
            select(UserRuntimeProfileRow.user_id).where(
                UserRuntimeProfileRow.status == UserRuntimeStatus.READY.value,
            )
        )

        return tuple(result.scalars().all())

    @staticmethod
    def _to_user(row: UserRow) -> User:
        return User(
            id=row.id,
            login=row.login,
            name=row.name,
            password_hash=row.password_hash,
            role=UserRole(row.role),
        )

    @staticmethod
    def _to_preferences(row: UserPreferencesRow) -> UserPreferences:
        return UserPreferences(
            user_id=row.user_id,
            language=row.language,
            utc_offset_minutes=row.utc_offset_minutes,
            region=row.region,
        )

    @staticmethod
    def _to_runtime_profile(row: UserRuntimeProfileRow) -> UserRuntimeProfile:
        return UserRuntimeProfile(
            user_id=row.user_id,
            status=UserRuntimeStatus(row.status),
            last_session_at=row.last_session_at,
        )

    @staticmethod
    def _to_user_row(user: User) -> UserRow:
        return UserRow(
            id=user.id,
            login=user.login,
            name=user.name,
            password_hash=user.password_hash,
            role=user.role.value,
        )

    @staticmethod
    def _to_preferences_row(preferences: UserPreferences) -> UserPreferencesRow:
        return UserPreferencesRow(
            user_id=preferences.user_id,
            language=preferences.language,
            utc_offset_minutes=preferences.utc_offset_minutes,
            region=preferences.region,
        )

    @staticmethod
    def _to_runtime_profile_row(
        runtime_profile: UserRuntimeProfile,
    ) -> UserRuntimeProfileRow:
        return UserRuntimeProfileRow(
            user_id=runtime_profile.user_id,
            status=runtime_profile.status.value,
            last_session_at=runtime_profile.last_session_at,
        )