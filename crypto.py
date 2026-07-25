import json
import os
import tempfile
from typing import Any

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from tinydb.storages import Storage


def load_fernet() -> MultiFernet:
    primary_key = os.environ.get("TINYDB_ENC_KEY", "").strip()
    if not primary_key:
        raise RuntimeError(
            "TINYDB_ENC_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    keys = [Fernet(primary_key.encode())]
    old_keys_raw = os.environ.get("TINYDB_ENC_KEYS_OLD", "").strip()
    if old_keys_raw:
        for k in old_keys_raw.split(","):
            k = k.strip()
            if k:
                keys.append(Fernet(k.encode()))
    return MultiFernet(keys)


def generate_key() -> str:
    return Fernet.generate_key().decode()


class EncryptedJSONStorage(Storage):
    """TinyDB storage that encrypts the entire JSON file as a single Fernet token."""

    def __init__(self, path: str, fernet: MultiFernet) -> None:
        self._path = path
        self._fernet = fernet

    def read(self) -> dict[str, Any] | None:
        if not os.path.exists(self._path):
            return None
        with open(self._path, "rb") as f:
            data = f.read()
        if not data:
            return None
        try:
            return json.loads(self._fernet.decrypt(data))
        except InvalidToken as exc:
            raise RuntimeError(
                f"Failed to decrypt vault at {self._path}. "
                "Wrong TINYDB_ENC_KEY or corrupted file."
            ) from exc

    def write(self, data: dict[str, Any]) -> None:
        # Encrypt first, then atomic replace to minimise partial-write window
        # (important for OneDrive-synced paths)
        encrypted = self._fernet.encrypt(json.dumps(data).encode())
        dir_ = os.path.dirname(self._path) or "."
        fd, tmp = tempfile.mkstemp(dir=dir_)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(encrypted)
            os.replace(tmp, self._path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def close(self) -> None:
        pass
