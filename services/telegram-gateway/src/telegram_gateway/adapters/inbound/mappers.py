from telegram_gateway.adapters.inbound.schemas import TelegramUpdateSchema
from telegram_gateway.domain.models import TelegramIncomingMessage
from telegram_gateway.application.errors import UnsupportedTelegramUpdateError


def map_telegram_update_to_message(update: TelegramUpdateSchema) -> TelegramIncomingMessage:
    if update.message is None:
        raise UnsupportedTelegramUpdateError("Telegram update has no message.")

    if update.message.text is None:
        raise UnsupportedTelegramUpdateError("Telegram message has no text.")

    return TelegramIncomingMessage(
        update_id=update.update_id,
        telegram_user_id=update.message.from_.id,
        telegram_chat_id=update.message.chat.id,
        telegram_message_id=update.message.message_id,
        text=update.message.text,
    )
