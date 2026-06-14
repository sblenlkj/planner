from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from telegram_gateway.application.errors import TelegramGatewayApplicationError


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        TelegramGatewayApplicationError,
        application_error_handler,
    )

    app.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )


async def application_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        },
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error.",
            },
        },
    )