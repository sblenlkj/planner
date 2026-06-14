import asyncio
from contextlib import suppress
from collections.abc import Awaitable

from typing import Any

from .ports.telegram_message_sender import TelegramMessageSender


async def run_with_typing_indicator(
    *,
    telegram_chat_id: int,
    telegram_message_sender: TelegramMessageSender,
    operation: Awaitable[Any | None],
    interval_seconds: float = 4.0,
) -> Any | None:
    async def typing_loop() -> None:
        while True:
            await telegram_message_sender.send_chat_action(
                telegram_chat_id=telegram_chat_id,
                action="typing...",
            )
            await asyncio.sleep(interval_seconds)

    typing_task = asyncio.create_task(typing_loop())

    try:
        return await operation
    finally:
        typing_task.cancel()

        with suppress(asyncio.CancelledError):
            await typing_task