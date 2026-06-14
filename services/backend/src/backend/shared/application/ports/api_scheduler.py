from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class ApiScheduledOperation:
    operation_key: str
    run_at: datetime
    handler_key: str
    payload: dict[str, Any]
    owner_user_id: UUID | None = None

@dataclass(frozen=True, kw_only=True)
class ApiScheduledCronOperation:
    operation_key: str
    cron_expression: str
    handler_key: str
    payload: dict[str, Any]
    owner_user_id: UUID | None = None


class ApiSchedulerPort(Protocol):
    async def schedule_operation(
        self,
        operation: ApiScheduledOperation,
    ) -> None:
        """
        Create or replace a scheduled operation by operation_key.
        """
        raise NotImplementedError

    async def cancel_operation(
        self,
        operation_key: str,
    ) -> None:
        raise NotImplementedError
    
    async def schedule_cron_operation(
        self,
        operation: ApiScheduledCronOperation,
    ) -> None:
        raise NotImplementedError