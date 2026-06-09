from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Mapping


LlmRole = Literal["system", "user", "assistant", "tool"]


class LlmWorkload(StrEnum):
    """Logical capacity class used by the runtime scheduler."""

    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    GRAPH_UPDATE = "graph_update"
    MAINTENANCE = "maintenance"


class LlmExecutionScope(StrEnum):
    """What owns a reserved LLM session."""

    ONE_SHOT = "one_shot"
    AGENT_RUN = "agent_run"
    WORKFLOW_RUN = "workflow_run"
    BATCH_DRAIN = "batch_drain"


@dataclass(frozen=True, slots=True)
class LlmMessage:
    role: LlmRole
    content: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class LlmToolSpec:
    """Provider-neutral tool description placeholder.

    LangGraph/LangChain agents usually bind native LangChain tools directly to
    the chat model, so this object is primarily for simple one-shot calls and
    future structured tool support.
    """

    name: str
    description: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmRequest:
    messages: list[LlmMessage]
    model: str | None = None
    temperature: float | None = None
    tools: list[LlmToolSpec] = field(default_factory=list)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class LlmUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmResponse:
    content: str
    usage: LlmUsage | None = None
    raw: Any | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmSessionRequest:
    workload: LlmWorkload
    scope: LlmExecutionScope
    purpose: str
    prompt_template: str | None = None
    max_duration_seconds: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
