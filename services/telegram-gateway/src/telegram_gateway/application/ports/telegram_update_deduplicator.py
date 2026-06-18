class TelegramUpdateDeduplicator:
    async def mark_processing_started(
        self,
        update_id: int,
    ) -> bool:
        """Atomically marks Telegram update as processing started.

        Returns:
            True  - update was not seen before and can be processed.
            False - update is duplicate and must be skipped.
        """
        raise NotImplementedError