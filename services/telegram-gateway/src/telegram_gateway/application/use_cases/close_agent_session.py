from datetime import datetime, timezone
from uuid import UUID

from telegram_gateway.application.ports.agent_client import AgentClient
from telegram_gateway.application.ports.conversation_store import ConversationStore
from telegram_gateway.logging import get_logger


class CloseAgentSession:
    def __init__(
        self,
        *,
        agent_client: AgentClient,
        conversation_store: ConversationStore,
    ) -> None:
        self._agent_client = agent_client
        self._conversation_store = conversation_store
        self._log = get_logger(self.__class__.__name__)

    async def close(
        self,
        *,
        business_user_id: UUID,
    ) -> bool:
        self._log.info(
            "use_case.started",
            use_case="close_agent_session",
            business_user_id=str(business_user_id),
        )

        messages = await self._conversation_store.get_messages(
            business_user_id=business_user_id,
        )

        if not messages:
            self._log.info(
                "use_case.finished",
                use_case="close_agent_session",
                business_user_id=str(business_user_id),
                closed=False,
                reason="no_active_session",
            )
            return False

        closed_at = datetime.now(timezone.utc)

        await self._agent_client.close_session(
            business_user_id=business_user_id,
            closed_at=closed_at,
            messages=messages,
        )

        await self._conversation_store.clear_messages(
            business_user_id=business_user_id,
        )

        self._log.info(
            "use_case.finished",
            use_case="close_agent_session",
            business_user_id=str(business_user_id),
            closed=True,
            messages_count=len(messages),
            closed_at=closed_at.isoformat(),
        )

        return True
