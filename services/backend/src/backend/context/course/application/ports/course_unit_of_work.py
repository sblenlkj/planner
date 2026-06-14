from __future__ import annotations

from typing import Protocol

from backend.context.course.application.ports.course_write_repository import (
    CourseWriteRepository,
)
from backend.context.course.application.ports.course_read_repository import (
    CourseReadRepository,
)

class CourseUnitOfWork(Protocol):
    course_writer: CourseWriteRepository
    course_reader: CourseReadRepository