class TelegramGatewayApplicationError(Exception):
    """Base application error."""


class TelegramBindingNotFoundError(TelegramGatewayApplicationError):
    """Telegram binding was not found."""


class EmptyTelegramMessageError(TelegramGatewayApplicationError):
    """Incoming Telegram message has no usable text."""


class UnsupportedTelegramUpdateError(TelegramGatewayApplicationError):
    """Telegram update cannot be processed by current gateway."""


class InvalidAgentResponseError(TelegramGatewayApplicationError):
    """Agent returned invalid response contract."""


class NoActiveTelegramSessionError(TelegramGatewayApplicationError):
    """There is no active Telegram session to close."""