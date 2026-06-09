from __future__ import annotations

from enum import StrEnum


class KnowledgeNodeType(StrEnum):
    AREA = "area"
    TOPIC = "topic"
    CONCEPT = "concept"
    SKILL = "skill"
    RESOURCE = "resource"
