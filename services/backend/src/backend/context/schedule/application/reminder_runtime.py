from __future__ import annotations

from backend.context.schedule.domain.commitment.entities.reminder import Reminder


RUNTIME_TRIGGER_REMINDER_HANDLER_KEY = "runtime.trigger_reminder"


def build_reminder_text(reminder: Reminder) -> str:
    if reminder.description is None or not reminder.description.strip():
        return f"Напоминаю: {reminder.title}"

    return f"Напоминаю: {reminder.title}\n\n{reminder.description}"