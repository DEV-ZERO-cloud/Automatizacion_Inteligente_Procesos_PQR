from typing import Any

from fastapi.responses import JSONResponse


def ok_response(data: Any = None, message: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
        },
    )


def error_response(message: str, status_code: int = 500, code: str | None = None) -> JSONResponse:
    payload: dict[str, Any] = {
        "success": False,
        "message": message,
        "data": None,
    }
    if code:
        payload["error_code"] = code

    return JSONResponse(status_code=status_code, content=payload)
