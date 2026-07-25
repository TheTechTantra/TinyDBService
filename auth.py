import os
import secrets

from fastapi import Header, HTTPException, status


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    token = os.environ.get("SECRET_STORE_TOKEN", "").strip()
    if not token:
        # Open mode: SECRET_STORE_TOKEN unset → allow all
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )
