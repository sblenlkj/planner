from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScheduleHttpEndpoints:
    """
    POST /schedule/reminders
    POST /schedule/deadlines
    GET  /schedule/commitments

    POST /schedule/date-observations
    GET  /schedule/date-observations

    POST /schedule/day-observations
    GET  /schedule/day-observations
    """

    host: str = "localhost"
    port: int = 8001
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def create_reminder(self) -> str:
        return f"{self.base_url}/schedule/reminders"

    @property
    def create_deadline(self) -> str:
        return f"{self.base_url}/schedule/deadlines"

    @property
    def list_commitments(self) -> str:
        return f"{self.base_url}/schedule/commitments"

    @property
    def create_date_observation(self) -> str:
        return f"{self.base_url}/schedule/date-observations"

    @property
    def list_date_observations(self) -> str:
        return f"{self.base_url}/schedule/date-observations"

    @property
    def create_day_observation(self) -> str:
        return f"{self.base_url}/schedule/day-observations"

    @property
    def list_day_observations(self) -> str:
        return f"{self.base_url}/schedule/day-observations"