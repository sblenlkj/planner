from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CourseHttpEndpoints:
    """
    GET   /courses
    GET   /courses/{course_id}
    GET   /courses/tasks/{task_id}

    POST  /courses
    POST  /courses/{course_id}/tasks
    POST  /courses/{course_id}/observations
    POST  /courses/tasks/{task_id}/observations

    PATCH /courses/{course_id}/status
    PATCH /courses/tasks/{task_id}/status
    """

    host: str = "localhost"
    port: int = 8001
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def read_courses(self) -> str:
        return f"{self.base_url}/courses"

    @property
    def create_course(self) -> str:
        return f"{self.base_url}/courses"

    def read_course(self, *, course_id: UUID | str) -> str:
        return f"{self.base_url}/courses/{course_id}"

    def create_course_task(self, *, course_id: UUID | str) -> str:
        return f"{self.base_url}/courses/{course_id}/tasks"

    def create_course_observation(self, *, course_id: UUID | str) -> str:
        return f"{self.base_url}/courses/{course_id}/observations"

    def update_course_status(self, *, course_id: UUID | str) -> str:
        return f"{self.base_url}/courses/{course_id}/status"

    def read_course_task(self, *, task_id: UUID | str) -> str:
        return f"{self.base_url}/courses/tasks/{task_id}"

    def create_course_task_observation(
        self,
        *,
        task_id: UUID | str,
    ) -> str:
        return f"{self.base_url}/courses/tasks/{task_id}/observations"

    def update_course_task_status(self, *, task_id: UUID | str) -> str:
        return f"{self.base_url}/courses/tasks/{task_id}/status"