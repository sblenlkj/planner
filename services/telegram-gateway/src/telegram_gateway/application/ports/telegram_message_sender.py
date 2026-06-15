class TelegramMessageSender:
    async def send_text(
        self,
        telegram_chat_id: int,
        text: str,
    ) -> None:
        raise NotImplementedError
