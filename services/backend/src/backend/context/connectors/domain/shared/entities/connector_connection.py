from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import ConnectorConnectionStatus, ConnectorProvider


@dataclass(kw_only=True, slots=True)
class ConnectorConnection:
    """
    Represents a user's connection to an external provider.

    `ConnectorConnection` is the shared domain entity that stores the business
    state of an integration account, for example Gmail or YouTube. It does not
    store OAuth tokens, refresh tokens, encrypted credentials, API clients, or any
    other infrastructure-specific details. Those concerns belong to the adapters,
    persistence layer, or credential storage.

    The entity answers the domain question: can this external provider connection
    currently be used by the system?

    A connection belongs to one user and one provider. The `external_account_ref`
    field identifies the account on the provider side. Depending on the provider,
    this may be an email address, account id, subject id, channel owner id, or
    another stable external reference.

    The connection tracks its lifecycle through `status`:

    - `ACTIVE` means jobs and sync operations may be executed.
    - `EXPIRED` means authentication is no longer valid and must be refreshed or
    reconnected.
    - `REVOKED` means the user or provider revoked access and jobs must not run.
    - `ERROR` means the connection failed due to a provider, auth, sync, or
    application-level problem.

    The entity also records coarse operational timestamps such as when it was
    connected, when it was updated, when the last successful operation happened,
    and when the last error happened. These timestamps are domain-level state, not
    scheduler implementation details.

    Main responsibilities:

    - keep provider connection state consistent;
    - validate required external account identity;
    - normalize scopes and error messages;
    - decide whether connector jobs may run;
    - expose explicit state transitions: activate, expire, revoke, error, success;
    - avoid leaking credential or API-client concerns into the domain model.

    This entity is intentionally provider-neutral. Gmail-specific filters,
    YouTube-specific subscriptions, cursors, messages, videos, and other provider
    models should live in their own provider modules and reference this connection
    by `connection_id`.
    """
    user_id: UUID
    provider: ConnectorProvider
    external_account_ref: str
    status: ConnectorConnectionStatus = ConnectorConnectionStatus.ACTIVE
    scopes: tuple[str, ...] = ()
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_success_at: datetime | None = None
    last_error_at: datetime | None = None
    error_message: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ConnectorProvider):
            raise ValueError("provider must be ConnectorProvider")

        if not isinstance(self.status, ConnectorConnectionStatus):
            raise ValueError("status must be ConnectorConnectionStatus")

        self._validate_required_string(self.external_account_ref, field_name="external_account_ref")
        self.external_account_ref = self.external_account_ref.strip()

        self.scopes = tuple(scope.strip() for scope in self.scopes if scope and scope.strip())

        self._validate_utc_datetime(self.connected_at, field_name="connected_at")
        self._validate_utc_datetime(self.updated_at, field_name="updated_at")

        if self.last_success_at is not None:
            self._validate_utc_datetime(self.last_success_at, field_name="last_success_at")

        if self.last_error_at is not None:
            self._validate_utc_datetime(self.last_error_at, field_name="last_error_at")

        if self.error_message is not None:
            self.error_message = self.error_message.strip() or None

    def activate(self) -> None:
        self.status = ConnectorConnectionStatus.ACTIVE
        self.error_message = None
        self._touch()

    def mark_expired(self, error_message: str | None = None) -> None:
        self.status = ConnectorConnectionStatus.EXPIRED
        self._set_error(error_message)
        self._touch()

    def revoke(self) -> None:
        self.status = ConnectorConnectionStatus.REVOKED
        self.error_message = None
        self._touch()

    def mark_error(self, error_message: str) -> None:
        self._validate_required_string(error_message, field_name="error_message")
        self.status = ConnectorConnectionStatus.ERROR
        self._set_error(error_message)
        self._touch()

    def mark_success(self, occurred_at: datetime | None = None) -> None:
        occurred_at = occurred_at or datetime.now(UTC)
        self._validate_utc_datetime(occurred_at, field_name="occurred_at")

        self.last_success_at = occurred_at
        self.error_message = None

        if self.status == ConnectorConnectionStatus.ERROR:
            self.status = ConnectorConnectionStatus.ACTIVE

        self._touch()

    def replace_scopes(self, scopes: tuple[str, ...]) -> None:
        self.scopes = tuple(scope.strip() for scope in scopes if scope and scope.strip())
        self._touch()

    def can_run_jobs(self) -> bool:
        return self.status == ConnectorConnectionStatus.ACTIVE

    def _set_error(self, error_message: str | None) -> None:
        self.last_error_at = datetime.now(UTC)
        self.error_message = error_message.strip() if error_message is not None else None

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

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
