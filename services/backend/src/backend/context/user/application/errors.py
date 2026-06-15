from __future__ import annotations

from uuid import UUID


class UserApplicationError(RuntimeError):
    pass


class UserNotFoundError(UserApplicationError):
    def __init__(self, *, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User with id={user_id} does not exist.")


class UserLoginAlreadyTakenError(UserApplicationError):
    def __init__(self, *, login: str) -> None:
        self.login = login
        super().__init__(f"User login '{login}' is already taken.")