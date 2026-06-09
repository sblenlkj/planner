from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass(slots=True)
class User:
    id: UUID
    email: str
    name: str
    status: UserStatus = UserStatus.ACTIVE

    @classmethod
    def create(
        cls,
        *,
        email: str,
        name: str,
        id: UUID | None = None,
    ) -> "User":
        return cls(
            id=id or uuid4(),
            email=email,
            name=name,
            status=UserStatus.ACTIVE,
        )

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.name = self.name.strip()

        if not self.email:
            raise ValueError("User email is required.")

        if "@" not in self.email:
            raise ValueError("User email must contain '@'.")

        if not self.name:
            raise ValueError("User name is required.")

    def rename(self, name: str) -> None:
        name = name.strip()

        if not name:
            raise ValueError("User name is required.")

        self.name = name

    def change_email(self, email: str) -> None:
        email = email.strip().lower()

        if not email:
            raise ValueError("User email is required.")

        if "@" not in email:
            raise ValueError("User email must contain '@'.")

        self.email = email

    def disable(self) -> None:
        self.status = UserStatus.DISABLED

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE