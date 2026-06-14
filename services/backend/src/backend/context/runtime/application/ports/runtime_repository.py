from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.runtime.domain.models import (
    RuntimeJob,
    RuntimeJobExecution,
    RuntimeJobExecutionStatus,
    RuntimeJobStatus,
    RuntimeJobType,
)


class RuntimeRepository(Protocol):
    async def add_job(self, job: RuntimeJob) -> None:
        raise NotImplementedError

    async def get_job_by_id(self, job_id: UUID) -> RuntimeJob | None:
        raise NotImplementedError

    async def get_job_by_key(self, job_key: str) -> RuntimeJob | None:
        raise NotImplementedError

    async def list_jobs(
        self,
        *,
        status: RuntimeJobStatus | None = None,
        job_type: RuntimeJobType | None = None,
    ) -> list[RuntimeJob]:
        raise NotImplementedError

    async def update_job(self, job: RuntimeJob) -> None:
        raise NotImplementedError

    async def add_execution(self, execution: RuntimeJobExecution) -> None:
        raise NotImplementedError

    async def get_execution_by_id(
        self,
        execution_id: UUID,
    ) -> RuntimeJobExecution | None:
        raise NotImplementedError

    async def list_executions(
        self,
        *,
        job_id: UUID | None = None,
        job_key: str | None = None,
        status: RuntimeJobExecutionStatus | None = None,
        limit: int = 100,
    ) -> list[RuntimeJobExecution]:
        raise NotImplementedError

    async def update_execution(
        self,
        execution: RuntimeJobExecution,
    ) -> None:
        raise NotImplementedError