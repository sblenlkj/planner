from __future__ import annotations

import os

from agent.llm import LlmOrchestrator, LlmProviderPool, LlmSlot, LlmWorkload
from agent.llm.adapters import GigaChatProvider, GigaChatProviderConfig


def _read_csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def build_llm_orchestrator() -> LlmOrchestrator:
    """Build a simple 3+2 LLM capacity split.

    Env:
      GIGACHAT_INTERACTIVE_CREDENTIALS=key1,key2,key3
      GIGACHAT_BACKGROUND_CREDENTIALS=key4,key5
    """

    interactive_credentials = _read_csv_env("GIGACHAT_INTERACTIVE_CREDENTIALS")
    background_credentials = _read_csv_env("GIGACHAT_BACKGROUND_CREDENTIALS")

    if not interactive_credentials and not background_credentials:
        raise RuntimeError(
            "Set GIGACHAT_INTERACTIVE_CREDENTIALS and/or GIGACHAT_BACKGROUND_CREDENTIALS"
        )

    slots: list[LlmSlot] = []

    for index, credentials in enumerate(interactive_credentials, start=1):
        slots.append(
            LlmSlot(
                slot_id=f"interactive-{index}",
                provider=GigaChatProvider(
                    GigaChatProviderConfig(credentials=credentials)
                ),
                workloads={LlmWorkload.INTERACTIVE},
            )
        )

    for index, credentials in enumerate(background_credentials, start=1):
        slots.append(
            LlmSlot(
                slot_id=f"background-{index}",
                provider=GigaChatProvider(
                    GigaChatProviderConfig(credentials=credentials)
                ),
                workloads={LlmWorkload.BACKGROUND, LlmWorkload.GRAPH_UPDATE},
            )
        )

    return LlmOrchestrator(LlmProviderPool(slots))
