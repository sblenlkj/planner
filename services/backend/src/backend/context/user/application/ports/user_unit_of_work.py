from __future__ import annotations

from typing import Protocol

from backend.context.user.application.ports.user_repository import UserRepository


class UserUnitOfWork(Protocol):
    users: UserRepository