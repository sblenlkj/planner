from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from direttore import ModularMonolithExecutionRuntime

from backend.context.user.application.use_cases import (
    GetReadyUserIdsCommand,
    GetReadyUserIdsCommandResult,
    GetUserUtcOffsetCommand,
    GetUserUtcOffsetCommandResult,
)


@dataclass(frozen=True, slots=True)
class UserUtcOffsetResult:
    user_id: UUID
    utc_offset_minutes: int


@dataclass(frozen=True, slots=True)
class ReadyUserIdsResult:
    user_ids: tuple[UUID, ...]


class UserInProcessFacade:
    def __init__(
        self,
        runtime: ModularMonolithExecutionRuntime,
    ) -> None:
        self._runtime = runtime

    async def get_user_utc_offset_minutes(
        self,
        *,
        user_id: UUID,
    ) -> UserUtcOffsetResult:
        result = await self._runtime.invoke(
            GetUserUtcOffsetCommand(user_id=user_id)
        )

        if not isinstance(result, GetUserUtcOffsetCommandResult):
            raise TypeError(
                "GetUserUtcOffsetCommand returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )

        return UserUtcOffsetResult(
            user_id=result.user_id,
            utc_offset_minutes=result.utc_offset_minutes,
        )

    async def get_ready_user_ids(self) -> ReadyUserIdsResult:
        result = await self._runtime.invoke(GetReadyUserIdsCommand())

        if not isinstance(result, GetReadyUserIdsCommandResult):
            raise TypeError(
                "GetReadyUserIdsCommand returned unexpected result type. "
                f"Got {type(result).__module__}.{type(result).__qualname__}."
            )

        return ReadyUserIdsResult(user_ids=result.user_ids)