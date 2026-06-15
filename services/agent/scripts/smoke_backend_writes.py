from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from agent.core.backend_settings import BackendApiSettings
from agent.infrastructure.backend.factory import build_backend_context_adapters


USER_ID = UUID("6fd80af1-b9d1-46a5-b8cb-f8cd752b8ef2")


def dump(value: Any) -> Any:
    if is_dataclass(value):
        return {
            key: dump(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, list):
        return [dump(item) for item in value]

    if isinstance(value, tuple):
        return [dump(item) for item in value]

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def print_json(title: str, value: Any) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(dump(value), ensure_ascii=False, indent=2))


async def main() -> None:
    settings = BackendApiSettings.local()
    clients = build_backend_context_adapters(settings)

    today = date.today()
    tomorrow = today + timedelta(days=1)
    remind_at = datetime.now(timezone.utc) + timedelta(hours=2)

    try:
        print_json("user profile", await clients.user.get_user_profile(USER_ID))

        course = await clients.course.create_course(
            USER_ID,
            title=f"Smoke Course {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            description="Тестовый курс, созданный smoke script из Agent Server.",
        )
        print_json("created course", course)

        task = await clients.course.create_course_task(
            course.id,
            title="Проверить backend adapters",
            description="Создать курс, задачу, observation и reminder через Agent Server infrastructure layer.",
        )
        print_json("created course task", task)

        analytics_observation = await clients.analytics.create_observation(
            USER_ID,
            description="Пользователь тестирует MVP agent infrastructure через smoke script.",
            scope="productivity",
        )
        print_json("created analytics observation", analytics_observation)

        date_observation = await clients.schedule.create_schedule_date_observation(
            USER_ID,
            starts_on=tomorrow,
            ends_on=tomorrow,
            description="Завтра есть тестовое ограничение/контекст, созданный smoke script.",
        )
        print_json("created schedule date observation", date_observation)

        day_observation = await clients.schedule.create_schedule_day_observation(
            USER_ID,
            date_=today,
            description="Сегодня был выполнен smoke test backend context adapters.",
        )
        print_json("created schedule day observation", day_observation)

        reminder = await clients.schedule.create_reminder(
            USER_ID,
            remind_at=remind_at,
            title="Smoke reminder",
            description="Тестовое напоминание, созданное Agent Server smoke script.",
        )
        print_json("created reminder", reminder)

        print_json("courses after write", await clients.course.list_courses(USER_ID))

        print_json(
            "date observations after write",
            await clients.schedule.list_schedule_date_observations(
                USER_ID,
                date_=tomorrow,
            ),
        )

        print_json(
            "day observations after write",
            await clients.schedule.list_schedule_day_observations(
                USER_ID,
                date_=today,
            ),
        )

        print_json(
            "commitments after write",
            await clients.schedule.list_commitments(USER_ID),
        )

        print_json(
            "analytics observations after write",
            await clients.analytics.list_observations(USER_ID, limit=20),
        )

    finally:
        await clients.aclose()


if __name__ == "__main__":
    asyncio.run(main())