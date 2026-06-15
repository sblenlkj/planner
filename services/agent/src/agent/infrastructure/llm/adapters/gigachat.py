from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_gigachat.chat_models import GigaChat


@dataclass(frozen=True, slots=True)
class GigaChatConnectionConfig:
    credentials: str
    model: str
    scope: str
    verify_ssl_certs: bool


class GigaChatConnectionFactory:
    def create(self, config: GigaChatConnectionConfig) -> Any:
        return GigaChat(
            credentials=config.credentials,
            model=config.model,
            scope=config.scope,
            verify_ssl_certs=config.verify_ssl_certs,
        )