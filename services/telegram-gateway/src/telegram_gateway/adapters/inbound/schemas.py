from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class TelegramUserSchema(BaseModel):
    id: int
    is_bot: bool | None = None
    first_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class TelegramChatSchema(BaseModel):
    id: int
    type: str | None = None


class TelegramMessageSchema(BaseModel):
    message_id: int
    from_: TelegramUserSchema = Field(alias="from")
    chat: TelegramChatSchema
    text: str | None = None


class TelegramUpdateSchema(BaseModel):
    update_id: int
    message: TelegramMessageSchema | None = None


class SendTelegramMessageRequest(BaseModel):
    business_user_id: UUID
    text: str


class CloseTelegramConversationRequest(BaseModel):
    business_user_id: UUID


class CloseTelegramConversationResponse(BaseModel):
    ok: bool = True
    closed: bool
    reason: str | None = None


class OkResponse(BaseModel):
    ok: bool = True
