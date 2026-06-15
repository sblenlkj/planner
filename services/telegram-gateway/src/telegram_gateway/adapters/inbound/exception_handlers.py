from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from telegram_gateway.application.errors import (
    AgentInputBlockedError,
    BusinessUserNotFoundError,
    TelegramBindingNotFoundError,
    TelegramGatewayApplicationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        AgentInputBlockedError,
        agent_input_blocked_error_handler,
    )
    app.add_exception_handler(
        TelegramBindingNotFoundError,
        telegram_binding_not_found_error_handler,
    )
    app.add_exception_handler(
        BusinessUserNotFoundError,
        business_user_not_found_error_handler,
    )
    app.add_exception_handler(
        TelegramGatewayApplicationError,
        application_error_handler,
    )
    app.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )


async def agent_input_blocked_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, AgentInputBlockedError):
        return await application_error_handler(request, exc)

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "code": "agent_input_blocked",
                "message": str(exc),
                "violations": exc.violations,
            },
        },
    )


async def telegram_binding_not_found_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "code": "telegram_binding_not_found",
                "message": str(exc),
            },
        },
    )


async def business_user_not_found_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "code": "business_user_not_found",
                "message": str(exc),
            },
        },
    )


async def application_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "code": "application_error",
                "message": str(exc),
            },
        },
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "code": "internal_error",
                "message": "Internal server error.",
            },
        },
    )