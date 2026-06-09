from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class CourseTaskLink:
    description: str
    url: str | None = None

    def __post_init__(self) -> None:
        description = self.description.strip()
        url = self.url.strip() if self.url else None

        if not description:
            raise ValueError("Course task link description is required.")

        object.__setattr__(self, "description", description)
        object.__setattr__(self, "url", url or None)