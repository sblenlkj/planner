from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from backend.shared.application import ADMIN_ACCESS_TAG, USER_ACCESS_TAG


class UserRole(StrEnum):
    USER = USER_ACCESS_TAG
    ADMIN = ADMIN_ACCESS_TAG


@dataclass(slots=True)
class User:
    id: UUID
    password_hash: str
    login: str | None = None
    name: str | None = None
    role: UserRole = UserRole.USER

    @classmethod
    def create_user(
        cls,
        *,
        password_hash: str,
        login: str | None = None,
        name: str | None = None,
        id: UUID | None = None,
    ) -> "User":
        return cls(
            id=id or uuid4(),
            login=login,
            name=name,
            password_hash=password_hash,
            role=UserRole.USER,
        )

    @classmethod
    def create_admin(
        cls,
        *,
        login: str,
        name: str,
        password_hash: str,
        id: UUID | None = None,
    ) -> "User":
        login = cls._normalize_required_text(login, "Admin login")
        name = cls._normalize_required_text(name, "Admin name")

        return cls(
            id=id or uuid4(),
            login=login,
            name=name,
            password_hash=password_hash,
            role=UserRole.ADMIN,
        )

    def __post_init__(self) -> None:
        self.login = self._normalize_login(self.login)
        self.name = self._normalize_optional_text(self.name)
        self.password_hash = self.password_hash.strip()

        if not self.password_hash:
            raise ValueError("User password hash is required.")

        if self.role == UserRole.ADMIN:
            self.login = self._normalize_required_text(self.login, "Admin login")
            self.name = self._normalize_required_text(self.name, "Admin name")

    def rename(self, name: str | None) -> None:
        self.name = self._normalize_optional_text(name)

    def change_login(self, login: str | None) -> None:
        self.login = self._normalize_login(login)

    def change_password_hash(self, password_hash: str) -> None:
        password_hash = password_hash.strip()

        if not password_hash:
            raise ValueError("User password hash is required.")

        self.password_hash = password_hash

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_regular_user(self) -> bool:
        return self.role == UserRole.USER

    @staticmethod
    def _normalize_login(login: str | None) -> str | None:
        if login is None:
            return None

        login = login.strip().lower()
        return login or None

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None

    @classmethod
    def _normalize_required_text(cls, value: str | None, field_name: str) -> str:
        value = cls._normalize_optional_text(value)

        if value is None:
            raise ValueError(f"{field_name} is required.")

        return value