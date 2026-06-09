from enum import StrEnum


class TimeBlockKind(StrEnum):
    FREE = "free"
    BUSY = "busy"
    SLEEP = "sleep"
    LIMITED = "limited"
    BLOCKED = "blocked"
