from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackendApiSettings:
    """Static Backend internal API settings for local MVP development.

    Keep this file intentionally simple while we are testing Agent Server
    adapters against Backend endpoints.
    """

    base_url: str = "http://localhost:8001"
    access_token: str | None = None
    timeout_seconds: float = 10.0

    # User
    get_user_profile_path: str = "/users/{user_id}"
    update_user_profile_path: str = "/users/{user_id}"

    # Course read
    list_courses_path: str = "/courses"
    get_course_path: str = "/courses/{course_id}"
    list_course_tasks_path: str = "/courses/{course_id}/tasks"
    get_course_task_path: str = "/course-tasks/{task_id}"
    list_course_observations_path: str = "/courses/{course_id}/observations"
    list_course_task_observations_path: str = "/course-tasks/{task_id}/observations"

    # Course write
    create_course_path: str = "/courses"
    create_course_task_path: str = "/courses/{course_id}/tasks"
    update_course_task_progress_path: str = "/course-tasks/{task_id}/progress"
    create_course_observation_path: str = "/courses/{course_id}/observations"
    create_course_task_observation_path: str = "/course-tasks/{task_id}/observations"

    # Schedule read
    list_schedule_date_observations_path: str = "/schedule/date-observations"
    list_schedule_day_observations_path: str = "/schedule/day-observations"
    list_reminders_path: str = "/schedule/commitments"
    list_deadlines_path: str = "/schedule/commitments"
    list_commitments_path: str = "/schedule/commitments"

    # Schedule write
    create_schedule_date_observation_path: str = "/schedule/date-observations"
    create_schedule_day_observation_path: str = "/schedule/day-observations"
    create_reminder_path: str = "/schedule/reminders"
    create_deadline_path: str = "/schedule/deadlines"

    # Analytics
    list_analytics_observations_path: str = "/analytics/observations"
    create_analytics_observation_path: str = "/analytics/observations"

    @classmethod
    def local(cls) -> "BackendApiSettings":
        return cls()

    @classmethod
    def from_env(cls) -> "BackendApiSettings":
        """Compatibility alias.

        We intentionally do not read env vars in the MVP smoke-test stage.
        """
        return cls.local()