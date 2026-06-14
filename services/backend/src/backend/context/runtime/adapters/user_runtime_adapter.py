from __future__ import annotations

from uuid import UUID

from direttore import ModularMonolithExecutionRuntime

from backend.context.runtime.application.ports.user_runtime_port import (
    UserRuntimePort,
)
from backend.context.user.adapters.inbound.in_process_facade import (
    UserInProcessFacade,
)


class InProcessUserRuntimeAdapter(UserRuntimePort):
    def __init__(
        self,
        runtime: ModularMonolithExecutionRuntime,
    ) -> None:
        self._user_facade = UserInProcessFacade(runtime)

    async def get_ready_user_ids(self) -> tuple[UUID, ...]:
        result = await self._user_facade.get_ready_user_ids()
        return result.user_ids