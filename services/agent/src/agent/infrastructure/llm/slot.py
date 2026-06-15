from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapters import GigaChatConnectionConfig, GigaChatConnectionFactory
from agent.core.settings import LlmModelKind


@dataclass(frozen=True, slots=True)
class LlmSlot:
    slot_id: str
    credentials: str
    strong_model: str
    weak_model: str
    scope: str
    verify_ssl_certs: bool

    def connect(
        self,
        *,
        model_kind: LlmModelKind,
        factory: GigaChatConnectionFactory,
    ) -> "AcquiredLlmSlot":
        model = self._resolve_model(model_kind)

        llm = factory.create(
            GigaChatConnectionConfig(
                credentials=self.credentials,
                model=model,
                scope=self.scope,
                verify_ssl_certs=self.verify_ssl_certs,
            )
        )

        return AcquiredLlmSlot(
            slot_id=self.slot_id,
            model_kind=model_kind,
            model=model,
            llm=llm,
        )

    def _resolve_model(self, model_kind: LlmModelKind) -> str:
        match model_kind:
            case LlmModelKind.STRONG:
                return self.strong_model
            case LlmModelKind.WEAK:
                return self.weak_model


@dataclass(slots=True)
class AcquiredLlmSlot:
    slot_id: str
    model_kind: LlmModelKind
    model: str
    llm: Any | None

    def close(self) -> None:
        self.llm = None