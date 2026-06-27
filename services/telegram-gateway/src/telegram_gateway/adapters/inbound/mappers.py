from telegram_gateway.adapters.inbound.schemas import TelegramUpdateSchema
from telegram_gateway.application.use_cases.handle_telegram_webhook_message import (
    IncomingTelegramWebhookMessage,
)


def map_telegram_update_to_incoming_webhook_message(
    update: TelegramUpdateSchema,
) -> IncomingTelegramWebhookMessage | None:
    if update.message is None:
        return None

    if update.message.text is None:
        return None

    return IncomingTelegramWebhookMessage(
        update_id=update.update_id,
        telegram_user_id=update.message.from_user.id,
        telegram_chat_id=update.message.chat.id,
        text=update.message.text,
        telegram_username=update.message.from_user.username,
        telegram_first_name=update.message.from_user.first_name,
        telegram_last_name=update.message.from_user.last_name,
    )
