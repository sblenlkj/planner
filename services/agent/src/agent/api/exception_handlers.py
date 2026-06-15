from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from agent.conversation_agent.input_guard import InputGuardBlockedError


async def input_guard_blocked_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, InputGuardBlockedError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Unexpected exception type for input guard handler.",
                }
            },
        )

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": "input_guard_blocked",
                "message": (
                    "User message was blocked by safety policy. "
                    "Do not add this message to the active session."
                ),
                "violations": [
                    {
                        "code": violation.code.value,
                        "message": violation.message,
                    }
                    for violation in exc.violations
                ],
            }
        },
    )