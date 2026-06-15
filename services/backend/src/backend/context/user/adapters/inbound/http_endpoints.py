from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserHttpEndpoints:
    """
    POST  /users
    GET   /users/{user_id}/runtime-status
    PATCH /users/{user_id}/runtime-status
    PATCH /users/{business_user_id}/last-session-at
    """
    host: str = "localhost"
    port: int = 8001
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def create_user(self) -> str:
        return f"{self.base_url}/users"

    def get_user_runtime_status(self, *, user_id: UUID | str) -> str:
        return f"{self.base_url}/users/{user_id}/runtime-status"

    def update_user_runtime_status(self, *, user_id: UUID | str) -> str:
        return f"{self.base_url}/users/{user_id}/runtime-status"
    
    def update_user_last_session_at(self, *, user_id: UUID | str) -> str:
        return f"{self.base_url}/users/{user_id}/last-session-at"
    
    def get_user(self, *, user_id: UUID | str) -> str:
        return f"{self.base_url}/users/{user_id}"