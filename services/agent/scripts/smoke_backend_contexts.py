import asyncio
import json
from uuid import UUID

from agent.core.backend_settings import BackendApiSettings
from agent.infrastructure.backend.factory import build_backend_context_adapters


USER_ID = UUID("6fd80af1-b9d1-46a5-b8cb-f8cd752b8ef2")

from datetime import date

def dump(value):
    if hasattr(value, "__dict__"):
        return value.__dict__
    if isinstance(value, list):
        return [dump(item) for item in value]
    return str(value)


async def main() -> None:
    settings = BackendApiSettings.from_env()
    clients = build_backend_context_adapters(settings)

    print("== user profile ==")
    user = await clients.user.get_user_profile(USER_ID)
    print(json.dumps(dump(user), ensure_ascii=False, indent=2, default=str))

    print("\n== courses ==")
    courses = await clients.course.list_courses(USER_ID)
    print(json.dumps(dump(courses), ensure_ascii=False, indent=2, default=str))

    print("\n== analytics observations ==")
    observations = await clients.analytics.list_observations(USER_ID, limit=20)
    print(json.dumps(dump(observations), ensure_ascii=False, indent=2, default=str))

    print("\n== schedule date observations ==")
    date_observations = await clients.schedule.list_schedule_date_observations(USER_ID, date_=date.today())
    print(json.dumps(dump(date_observations), ensure_ascii=False, indent=2, default=str))

    today = date.today()

    date_observations = await clients.schedule.list_schedule_date_observations(
        USER_ID,
        date_=today,
    )

    day_observations = await clients.schedule.list_schedule_day_observations(
        USER_ID,
        date_=today,
    )

    commitments = await clients.schedule.list_commitments(USER_ID)

    await clients.aclose()


if __name__ == "__main__":
    asyncio.run(main())