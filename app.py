import logging

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from auth import require_api_key
from CredentialModel import Credential
from TinyDBUtil import TinyDbReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="TinyDBService")

# Unauthenticated — used by Docker healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}


# All credential endpoints require X-API-Key
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


app.include_router(router)
