from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from telegram_gateway.domain.models import ConversationMessage


class RedisStreamName(StrEnum):
    TELEGRAM_SESSION_CLOSED = "planner.telegram.session.closed"
    AGENT_OBSERVATIONS_EXTRACTED = "planner.agent.observations.extracted"
    AGENT_OBSERVATIONS_BATCH_READY = "planner.agent.observations.batch_ready"
    AGENT_DAY_GENERATION_REQUESTED = "planner.agent.day_generation.requested"


@dataclass(slots=True)
class ClosedSessionEvent:
    event_id: UUID
    business_user_id: UUID
    telegram_chat_id: int
    closed_at: datetime
    messages: list[ConversationMessage]
