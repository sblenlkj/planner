from uuid import UUID

from pydantic import BaseModel, Field

from telegram_gateway.domain.models import ConversationMessageRole

class OkResponse(BaseModel):
    ok: bool = True


class AuthRequest(BaseModel):
    business_user_id: UUID


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AttachTelegramRequest(BaseModel):
    business_user_id: UUID
    telegram_user_id: int
    telegram_chat_id: int


class AgentMessageRequest(BaseModel):
    business_user_id: UUID
    text: str


class AgentMessageResponse(BaseModel):
    ok: bool = True
    assistant_text: str | None = None


class SendTelegramNotificationRequest(BaseModel):
    business_user_id: UUID
    text: str


class CloseAgentSessionRequest(BaseModel):
    business_user_id: UUID


class CloseAgentSessionResponse(BaseModel):
    ok: bool = True
    closed: bool
    reason: str | None = None

class GetAgentSessionRequest(BaseModel):
    business_user_id: UUID


class ConversationMessageResponse(BaseModel):
    role: ConversationMessageRole
    content: str


class GetAgentSessionResponse(BaseModel):
    ok: bool = True
    messages: list[ConversationMessageResponse]


class TelegramUserSchema(BaseModel):
    id: int
    is_bot: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class TelegramChatSchema(BaseModel):
    id: int


class TelegramMessageSchema(BaseModel):
    message_id: int
    date: int
    text: str | None = None
    from_user: TelegramUserSchema = Field(alias="from")
    chat: TelegramChatSchema


class TelegramUpdateSchema(BaseModel):
    update_id: int
    message: TelegramMessageSchema | None = None
