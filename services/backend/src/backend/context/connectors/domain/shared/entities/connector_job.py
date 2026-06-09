from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import ConnectorJobStatus, ConnectorJobType, ConnectorProvider


@dataclass(kw_only=True, slots=True)
class ConnectorJob:
    """
    Represents a domain-level unit of connector work.

    `ConnectorJob` describes that the connectors context needs to perform, is
    performing, or has performed some integration-related operation for a provider
    connection. It is not a Celery task, cron entry, queue message, thread, worker,
    or infrastructure job implementation. The actual execution mechanism belongs
    to the application and infrastructure layers.

    The entity answers the domain question: what connector operation was scheduled
    or executed, and what is its current result?

    A job belongs to one connector connection and one provider. The `job_type`
    explains the kind of work, for example polling, syncing, refreshing auth, or
    processing an event. The `scheduled_at`, `started_at`, and `finished_at`
    timestamps describe the lifecycle of this work from the domain perspective.

    The job lifecycle is intentionally small and explicit:

    - `PENDING` means the job is scheduled and may be started.
    - `RUNNING` means the job is currently being executed.
    - `SUCCEEDED` means the operation completed successfully.
    - `FAILED` means the operation ended with an error.
    - `CANCELLED` means the job was stopped before successful completion.

    The entity owns retry counters and retry limits because those fields describe
    the domain state of an integration operation. It does not decide when a worker
    will actually pick the job up; it only validates whether the job may transition
    back to `PENDING` after failure.

    Main responsibilities:

    - keep connector work lifecycle consistent;
    - prevent invalid state transitions, such as starting a non-pending job;
    - record start, finish, failure, cancellation, and retry state;
    - validate retry counters and retry limits;
    - preserve error information for failed connector operations;
    - keep execution state independent from any concrete queue or scheduler.

    Provider-specific application services may create jobs such as Gmail sync jobs
    or YouTube polling jobs. The shared entity remains generic and should not know
    how a concrete provider API is called.
    """
    connection_id: UUID
    provider: ConnectorProvider
    job_type: ConnectorJobType
    scheduled_at: datetime
    status: ConnectorJobStatus = ConnectorJobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ConnectorProvider):
            raise ValueError("provider must be ConnectorProvider")

        if not isinstance(self.job_type, ConnectorJobType):
            raise ValueError("job_type must be ConnectorJobType")

        if not isinstance(self.status, ConnectorJobStatus):
            raise ValueError("status must be ConnectorJobStatus")

        if self.retry_count < 0:
            raise ValueError("retry_count must be greater than or equal to 0")

        if self.max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")

        if self.retry_count > self.max_retries:
            raise ValueError("retry_count cannot be greater than max_retries")

        self._validate_utc_datetime(self.scheduled_at, field_name="scheduled_at")

        if self.started_at is not None:
            self._validate_utc_datetime(self.started_at, field_name="started_at")

        if self.finished_at is not None:
            self._validate_utc_datetime(self.finished_at, field_name="finished_at")

        if self.error_message is not None:
            self.error_message = self.error_message.strip() or None

    def start(self, started_at: datetime | None = None) -> None:
        if self.status != ConnectorJobStatus.PENDING:
            raise ValueError("only pending job can be started")

        started_at = started_at or datetime.now(UTC)
        self._validate_utc_datetime(started_at, field_name="started_at")

        self.status = ConnectorJobStatus.RUNNING
        self.started_at = started_at
        self.error_message = None

    def succeed(self, finished_at: datetime | None = None) -> None:
        if self.status != ConnectorJobStatus.RUNNING:
            raise ValueError("only running job can succeed")

        finished_at = finished_at or datetime.now(UTC)
        self._validate_utc_datetime(finished_at, field_name="finished_at")

        self.status = ConnectorJobStatus.SUCCEEDED
        self.finished_at = finished_at
        self.error_message = None

    def fail(self, error_message: str, finished_at: datetime | None = None) -> None:
        if self.status != ConnectorJobStatus.RUNNING:
            raise ValueError("only running job can fail")

        if not error_message or not error_message.strip():
            raise ValueError("error_message is required")

        finished_at = finished_at or datetime.now(UTC)
        self._validate_utc_datetime(finished_at, field_name="finished_at")

        self.status = ConnectorJobStatus.FAILED
        self.finished_at = finished_at
        self.error_message = error_message.strip()

    def cancel(self) -> None:
        if self.is_finished():
            raise ValueError("finished job cannot be cancelled")

        self.status = ConnectorJobStatus.CANCELLED
        self.finished_at = datetime.now(UTC)

    def retry(self, scheduled_at: datetime) -> None:
        if self.status != ConnectorJobStatus.FAILED:
            raise ValueError("only failed job can be retried")

        if not self.can_retry():
            raise ValueError("job retry limit exceeded")

        self._validate_utc_datetime(scheduled_at, field_name="scheduled_at")

        self.retry_count += 1
        self.status = ConnectorJobStatus.PENDING
        self.scheduled_at = scheduled_at
        self.started_at = None
        self.finished_at = None
        self.error_message = None

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def is_finished(self) -> bool:
        return self.status in {
            ConnectorJobStatus.SUCCEEDED,
            ConnectorJobStatus.FAILED,
            ConnectorJobStatus.CANCELLED,
        }

    @staticmethod
    def _validate_utc_datetime(value: datetime, *, field_name: str) -> None:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be datetime")

        if value.tzinfo is None:
            return

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be UTC datetime or naive UTC datetime")
