from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.adapters.persistence import Base


class AnalyticsObservationRow(Base):
    __tablename__ = "analytics_observations"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    scope: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    stability: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


class AnalyticsInsightRow(Base):
    __tablename__ = "analytics_insights"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    scope: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    stability: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source_observation_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    derived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    replaced_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
