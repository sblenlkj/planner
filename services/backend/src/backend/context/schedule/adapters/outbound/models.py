from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, ForeignKeyConstraint, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.adapters.persistence import Base


class ReminderRow(Base):
    __tablename__ = "schedule_reminders"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )


class DeadlineRow(Base):
    __tablename__ = "schedule_deadlines"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    course_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    course_task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )


class WeeklyScheduleTemplateRow(Base):
    __tablename__ = "weekly_schedule_templates"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )


class ScheduleDayTemplateRow(Base):
    __tablename__ = "schedule_day_templates"

    weekly_schedule_template_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("weekly_schedule_templates.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weekday: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
    )


class TemplateTimeBlockRow(Base):
    __tablename__ = "schedule_template_time_blocks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["weekly_schedule_template_id", "weekday"],
            ["schedule_day_templates.weekly_schedule_template_id", "schedule_day_templates.weekday"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    weekly_schedule_template_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    weekday: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
    )
    start_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    end_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class WeeklyScheduleObservationRow(Base):
    __tablename__ = "weekly_schedule_observations"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    weekly_schedule_template_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("weekly_schedule_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


class ScheduleDayRow(Base):
    __tablename__ = "schedule_days"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


class ScheduledBlockRow(Base):
    __tablename__ = "scheduled_blocks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "date"],
            ["schedule_days.user_id", "schedule_days.date"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    start_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    end_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class ScheduledActivityRow(Base):
    __tablename__ = "scheduled_activities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "date"],
            ["schedule_days.user_id", "schedule_days.date"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    start_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    end_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    course_task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )


class ScheduleDayObservationRow(Base):
    __tablename__ = "schedule_day_observations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "date"],
            ["schedule_days.user_id", "schedule_days.date"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


class ScheduleDateObservationRow(Base):
    __tablename__ = "schedule_date_observations"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    starts_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    ends_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
