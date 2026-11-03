"""Unified API envelope {code, data, message}."""
from typing import Any, Optional
from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok", code: int = 0) -> dict:
    return {"code": code, "data": data, "message": message}


def fail(code: int, message: str, data: Any = None, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "data": data, "message": message})
