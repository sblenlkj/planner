from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


MessageRole = Literal["user", "assistant", "system"]


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1)


class ConversationRequest(BaseModel):
    messages: list[ConversationMessage]


class ConversationRespondResponse(BaseModel):
    assistant_text: str | None = None


class WorkflowOkResponse(BaseModel):
    ok: bool = True


class MorningBriefingRequest(BaseModel):
    date: date


class MorningBriefingResponse(BaseModel):
    ok: bool = True
    assistant_text: str | None = None