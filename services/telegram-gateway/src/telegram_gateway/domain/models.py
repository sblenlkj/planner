from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


@dataclass(slots=True)
class TelegramBinding:
    business_user_id: UUID
    telegram_user_id: int
    telegram_chat_id: int


@dataclass(slots=True)
class TelegramIncomingMessage:
    update_id: int
    telegram_user_id: int
    telegram_chat_id: int
    telegram_message_id: int
    text: str


class ConversationMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True)
class ConversationMessage:
    role: ConversationMessageRole
    content: str
