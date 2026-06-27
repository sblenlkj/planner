from typing import Protocol


class TelegramUpdateDeduplicator(Protocol):
    async def mark_processing_started(
        self,
        update_id: int,
    ) -> bool:
        ...
