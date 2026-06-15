from __future__ import annotations


from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyticsHttpEndpoints:
    """
    POST /analytics/observations
    GET  /analytics/observations
    """

    host: str = "localhost"
    port: int = 8001
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def create_analytics_observation(self) -> str:
        return f"{self.base_url}/analytics/observations"

    @property
    def list_analytics_observations(self) -> str:
        return f"{self.base_url}/analytics/observations"
