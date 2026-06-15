from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


@dataclass(slots=True)
class TelegramBinding:
    business_user_id: UUID
    telegram_user_id: int
    telegram_chat_id: int


class ConversationMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(slots=True)
class ConversationMessage:
    role: ConversationMessageRole
    content: str
