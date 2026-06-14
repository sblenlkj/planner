from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from backend.shared.adapters.persistence import Base


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    login: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )


class UserPreferencesRow(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    utc_offset_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    region: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )

class UserRuntimeProfileRow(Base):
    __tablename__ = "user_runtime_profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    last_session_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )