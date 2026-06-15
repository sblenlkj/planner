class TelegramGatewayApplicationError(Exception):
    """Base Telegram Gateway application error."""


class TelegramBindingNotFoundError(TelegramGatewayApplicationError):
    pass


class BusinessUserNotFoundError(TelegramGatewayApplicationError):
    pass


class AgentResponseError(TelegramGatewayApplicationError):
    pass


class TelegramMessageDeliveryError(TelegramGatewayApplicationError):
    pass
