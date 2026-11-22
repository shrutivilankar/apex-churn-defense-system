"""TMF error response helper (code, reason, message, status)."""
from typing import Optional

from fastapi.responses import JSONResponse


def tmf_error(
    status_code: int,
    reason: str,
    message: Optional[str] = None,
    code: Optional[str] = None,
) -> JSONResponse:
    content = {
        "code": code or f"ERR{status_code}",
        "reason": reason,
        "status": str(status_code),
    }
    if message:
        content["message"] = message
    return JSONResponse(status_code=status_code, content=content)
