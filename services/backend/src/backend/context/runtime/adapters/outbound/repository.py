from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.runtime.adapters.outbound.models import (
    RuntimeJobExecutionRow,
    RuntimeJobRow,
)
from backend.context.runtime.application.ports.runtime_repository import (
    RuntimeRepository,
)
from backend.context.runtime.domain.models import (
    RuntimeJob,
    RuntimeJobExecution,
    RuntimeJobExecutionSource,
    RuntimeJobExecutionStatus,
    RuntimeJobStatus,
    RuntimeJobType,
)


class SqlAlchemyRuntimeRepository(RuntimeRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def add_job(
        self,
        job: RuntimeJob,
    ) -> None:
        self._session.add(self._job_to_row(job))

    async def get_job_by_id(
        self,
        job_id: UUID,
    ) -> RuntimeJob | None:
        row = await self._session.get(RuntimeJobRow, job_id)
        if row is None:
            return None

        return self._job_from_row(row)

    async def get_job_by_key(
        self,
        job_key: str,
    ) -> RuntimeJob | None:
        stmt = select(RuntimeJobRow).where(RuntimeJobRow.job_key == job_key)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._job_from_row(row)

    async def list_jobs(
        self,
        *,
        status: RuntimeJobStatus | None = None,
        job_type: RuntimeJobType | None = None,
    ) -> list[RuntimeJob]:
        stmt = select(RuntimeJobRow)

        if status is not None:
            stmt = stmt.where(RuntimeJobRow.status == status.value)

        if job_type is not None:
            stmt = stmt.where(RuntimeJobRow.job_type == job_type.value)

        stmt = stmt.order_by(RuntimeJobRow.job_key.asc())

        result = await self._session.execute(stmt)
        return [self._job_from_row(row) for row in result.scalars().all()]

    async def update_job(
        self,
        job: RuntimeJob,
    ) -> None:
        row = await self._session.get(RuntimeJobRow, job.id)
        if row is None:
            raise RuntimeError(f"Runtime job not found: {job.id}")

        row.job_type = job.job_type.value
        row.job_key = job.job_key
        row.cron_expression = job.cron_expression
        row.status = job.status.value
        row.last_run_at = job.last_run_at
        row.last_success_at = job.last_success_at
        row.metadata_json = dict(job.metadata)

    async def add_execution(
        self,
        execution: RuntimeJobExecution,
    ) -> None:
        self._session.add(self._execution_to_row(execution))

    async def get_execution_by_id(
        self,
        execution_id: UUID,
    ) -> RuntimeJobExecution | None:
        row = await self._session.get(RuntimeJobExecutionRow, execution_id)
        if row is None:
            return None

        return self._execution_from_row(row)

    async def list_executions(
        self,
        *,
        job_id: UUID | None = None,
        job_key: str | None = None,
        status: RuntimeJobExecutionStatus | None = None,
        limit: int = 100,
    ) -> list[RuntimeJobExecution]:
        stmt = select(RuntimeJobExecutionRow)

        if job_key is not None:
            stmt = stmt.join(
                RuntimeJobRow,
                RuntimeJobExecutionRow.job_id == RuntimeJobRow.id,
            ).where(RuntimeJobRow.job_key == job_key)

        if job_id is not None:
            stmt = stmt.where(RuntimeJobExecutionRow.job_id == job_id)

        if status is not None:
            stmt = stmt.where(RuntimeJobExecutionRow.status == status.value)

        stmt = stmt.order_by(RuntimeJobExecutionRow.started_at.desc()).limit(limit)

        result = await self._session.execute(stmt)
        return [self._execution_from_row(row) for row in result.scalars().all()]

    async def update_execution(
        self,
        execution: RuntimeJobExecution,
    ) -> None:
        row = await self._session.get(RuntimeJobExecutionRow, execution.id)
        if row is None:
            raise RuntimeError(f"Runtime job execution not found: {execution.id}")

        row.job_id = execution.job_id
        row.source = execution.source.value
        row.status = execution.status.value
        row.started_at = execution.started_at
        row.finished_at = execution.finished_at
        row.metadata_json = dict(execution.metadata)

    @staticmethod
    def _job_to_row(
        job: RuntimeJob,
    ) -> RuntimeJobRow:
        return RuntimeJobRow(
            id=job.id,
            job_type=job.job_type.value,
            job_key=job.job_key,
            cron_expression=job.cron_expression,
            status=job.status.value,
            last_run_at=job.last_run_at,
            last_success_at=job.last_success_at,
            metadata_json=dict(job.metadata),
        )

    @staticmethod
    def _job_from_row(
        row: RuntimeJobRow,
    ) -> RuntimeJob:
        return RuntimeJob(
            id=row.id,
            job_type=RuntimeJobType(row.job_type),
            job_key=row.job_key,
            cron_expression=row.cron_expression,
            status=RuntimeJobStatus(row.status),
            last_run_at=row.last_run_at,
            last_success_at=row.last_success_at,
            metadata=dict(row.metadata_json or {}),
        )

    @staticmethod
    def _execution_to_row(
        execution: RuntimeJobExecution,
    ) -> RuntimeJobExecutionRow:
        return RuntimeJobExecutionRow(
            id=execution.id,
            job_id=execution.job_id,
            source=execution.source.value,
            status=execution.status.value,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            metadata_json=dict(execution.metadata),
        )

    @staticmethod
    def _execution_from_row(
        row: RuntimeJobExecutionRow,
    ) -> RuntimeJobExecution:
        return RuntimeJobExecution(
            id=row.id,
            job_id=row.job_id,
            source=RuntimeJobExecutionSource(row.source),
            status=RuntimeJobExecutionStatus(row.status),
            started_at=row.started_at,
            finished_at=row.finished_at,
            metadata=dict(row.metadata_json or {}),
        )