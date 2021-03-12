import os
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader


DEFAULT_TOKEN = "hunter2"
_security_header = APIKeyHeader(name="Token")


async def security(
    *,
    token: str = Security(_security_header),
) -> None:
    real_token = os.getenv("ERT_STORAGE_TOKEN", DEFAULT_TOKEN)
    if token == real_token:
        # Success
        return
    # HTTP 403 is when the user has authorized themselves, but aren't allowed to
    # access this resource
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
