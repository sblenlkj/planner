from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RuntimeHttpEndpoints:
    """
    POST /runtime/day-generation/request
    """

    host: str = "localhost"
    port: int = 8001
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def request_day_generation(self) -> str:
        return f"{self.base_url}/runtime/day-generation/request"