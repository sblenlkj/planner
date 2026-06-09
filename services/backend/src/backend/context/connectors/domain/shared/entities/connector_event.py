from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import ConnectorEventStatus, ConnectorEventType, ConnectorProvider


@dataclass(kw_only=True, slots=True)
class ConnectorEvent:
    """
    Represents an external event ingested by a connector.

    `ConnectorEvent` is the shared domain entity used when an external provider
    produces something that may be relevant to the planner system. Examples include
    a Gmail message being received or a YouTube video being detected. The entity
    stores a normalized event envelope, while provider-specific details may stay in
    `payload` or in provider-specific models.

    The entity answers the domain question: what external thing happened, has the
    system handled it, and was it dispatched to a workflow?

    An event belongs to one user, one connector connection, and one provider. The
    `external_event_id` is the provider-side identifier used to recognize the
    external item. For Gmail this may be a message id or history-derived event id;
    for YouTube this may be a video id or another stable provider reference.

    The event lifecycle is intentionally simple:

    - `RECEIVED` means the system ingested the event but has not handled it yet.
    - `DISPATCHED` means the event was sent to an application or agent workflow.
    - `IGNORED` means the event was intentionally skipped.
    - `FAILED` means handling the event failed and the reason is stored in
    `error_message`.

    `ConnectorEvent` does not create schedule blocks, deadlines, reminders, tasks,
    observations, or courses directly. It only records that an external signal was
    received and optionally dispatched to a named workflow. The target workflow may
    then call other bounded contexts or agent logic.

    Main responsibilities:

    - keep an auditable record of external provider signals;
    - normalize common event metadata across providers;
    - validate provider, event type, external id, and timestamps;
    - record whether the event was dispatched, ignored, or failed;
    - keep workflow dispatch explicit through `dispatched_workflow_name`;
    - avoid making shared connector logic depend on schedule, course, reminder, or
    other planner-specific domain models.

    The `payload` field is intentionally pragmatic for the first connector version.
    It may contain provider-specific data needed by workflows. If the model becomes
    more complex later, payload handling can move to provider-specific event payload
    models or external payload storage without changing the main responsibility of
    this entity.
    """
    connection_id: UUID
    user_id: UUID
    provider: ConnectorProvider
    event_type: ConnectorEventType
    external_event_id: str
    occurred_at: datetime
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict | None = None
    status: ConnectorEventStatus = ConnectorEventStatus.RECEIVED
    dispatched_workflow_name: str | None = None
    error_message: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ConnectorProvider):
            raise ValueError("provider must be ConnectorProvider")

        if not isinstance(self.event_type, ConnectorEventType):
            raise ValueError("event_type must be ConnectorEventType")

        if not isinstance(self.status, ConnectorEventStatus):
            raise ValueError("status must be ConnectorEventStatus")

        self._validate_required_string(self.external_event_id, field_name="external_event_id")
        self.external_event_id = self.external_event_id.strip()

        self._validate_utc_datetime(self.occurred_at, field_name="occurred_at")
        self._validate_utc_datetime(self.received_at, field_name="received_at")

        if self.dispatched_workflow_name is not None:
            self.dispatched_workflow_name = self.dispatched_workflow_name.strip() or None

        if self.error_message is not None:
            self.error_message = self.error_message.strip() or None

    def dispatch(self, workflow_name: str) -> None:
        if self.status != ConnectorEventStatus.RECEIVED:
            raise ValueError("only received event can be dispatched")

        self._validate_required_string(workflow_name, field_name="workflow_name")

        self.dispatched_workflow_name = workflow_name.strip()
        self.status = ConnectorEventStatus.DISPATCHED
        self.error_message = None

    def ignore(self) -> None:
        if self.status == ConnectorEventStatus.DISPATCHED:
            raise ValueError("dispatched event cannot be ignored")

        self.status = ConnectorEventStatus.IGNORED
        self.error_message = None

    def fail(self, error_message: str) -> None:
        self._validate_required_string(error_message, field_name="error_message")

        self.status = ConnectorEventStatus.FAILED
        self.error_message = error_message.strip()

    def is_terminal(self) -> bool:
        return self.status in {
            ConnectorEventStatus.DISPATCHED,
            ConnectorEventStatus.IGNORED,
            ConnectorEventStatus.FAILED,
        }

    @staticmethod
    def _validate_required_string(value: str, *, field_name: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{field_name} is required")

    @staticmethod
    def _validate_utc_datetime(value: datetime, *, field_name: str) -> None:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be datetime")

        if value.tzinfo is None:
            return

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be UTC datetime or naive UTC datetime")
