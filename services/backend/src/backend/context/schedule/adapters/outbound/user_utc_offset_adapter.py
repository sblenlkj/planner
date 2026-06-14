from __future__ import annotations

from uuid import UUID

from direttore import ModularMonolithExecutionRuntime

from backend.context.schedule.application.ports.user_utc_offset_port import (
    UserUtcOffsetPort,
)
from backend.context.user.adapters.inbound.in_process_facade import (
    UserInProcessFacade,
)


class InProcessUserUtcOffsetAdapter(UserUtcOffsetPort):
    def __init__(
        self,
        runtime: ModularMonolithExecutionRuntime,
    ) -> None:
        self._user_facade = UserInProcessFacade(runtime)

    async def get_user_utc_offset_minutes(
        self,
        user_id: UUID,
    ) -> int:
        result = await self._user_facade.get_user_utc_offset_minutes(
            user_id=user_id,
        )

        return result.utc_offset_minutes