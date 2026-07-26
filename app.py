import logging
import os

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from auth import require_api_key
from CredentialModel import (
    Credential,
    DetokenizeRequest,
    DetokenizeResponse,
    TokenizeRequest,
    TokenizeResponse,
)
from TinyDBUtil import TinyDbReader, TokenVault

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("tinydbservice")

_VERSION = os.environ.get("APP_VERSION", "unknown")
_MODE = os.environ.get("SERVICE_MODE", "credentials").strip().lower()

# Warn loudly if running unauthenticated — every data endpoint is open,
# and in tokenization mode that means anyone can detokenize secrets.
if not os.environ.get("SECRET_STORE_TOKEN", "").strip():
    logger.warning(
        "SECRET_STORE_TOKEN is not set — running in OPEN mode: all data "
        "endpoints are UNAUTHENTICATED. Do not use in production."
    )

app = FastAPI(title="TinyDBService", version=_VERSION)

# Unauthenticated — used by Docker healthcheck
@app.get("/health")
def health():
    return {"status": "ok", "version": _VERSION, "mode": _MODE}


def _build_credentials_router() -> APIRouter:
    """Encryption-at-rest credential store (default mode)."""
    router = APIRouter(dependencies=[Depends(require_api_key)])

    @router.get("/credentials")
    def get_all_credentials():
        """Return all credentials as a flat {key: value} map."""
        return TinyDbReader().all_map()

    @router.get("/credential/{key}")
    def get_credential(key: str):
        value = TinyDbReader().read(key)
        if value is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
        return {"key": key, "value": value}

    @router.post("/key/", status_code=status.HTTP_201_CREATED)
    def set_credential(credential: Credential):
        TinyDbReader().write(credential.key, credential.value)
        return {"result": "ok"}

    @router.delete("/key/{key}")
    def delete_credential(key: str):
        removed = TinyDbReader().delete(key)
        if removed == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
        return {"result": "ok"}

    return router


def _build_tokenization_router() -> APIRouter:
    """Random vaulted tokenization store (SERVICE_MODE=tokenization)."""
    router = APIRouter(dependencies=[Depends(require_api_key)])

    @router.post("/tokenize", response_model=TokenizeResponse, status_code=status.HTTP_201_CREATED)
    def tokenize(req: TokenizeRequest):
        token = TokenVault().tokenize(req.value)
        # Audit: token id + event only — never the value.
        logger.info("tokenize token=%s", token)
        return TokenizeResponse(token=token)

    @router.post("/detokenize", response_model=DetokenizeResponse)
    def detokenize(req: DetokenizeRequest):
        value = TokenVault().detokenize(req.token)
        logger.info("detokenize token=%s hit=%s", req.token, value is not None)
        if value is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        return DetokenizeResponse(value=value)

    @router.delete("/token/{token}")
    def revoke_token(token: str):
        removed = TokenVault().revoke(token)
        logger.info("revoke token=%s removed=%d", token, removed)
        if removed == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        return {"result": "ok"}

    return router


if _MODE == "tokenization":
    app.include_router(_build_tokenization_router())
elif _MODE == "credentials":
    app.include_router(_build_credentials_router())
else:
    raise RuntimeError(
        f"Invalid SERVICE_MODE={_MODE!r}. Expected 'credentials' or 'tokenization'."
    )
