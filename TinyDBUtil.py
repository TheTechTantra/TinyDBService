import os
import secrets
import threading
from datetime import datetime, timezone

from tinydb import TinyDB, Query

from crypto import EncryptedJSONStorage, load_fernet

_lock = threading.Lock()
_db: TinyDB | None = None


def _get_db() -> TinyDB:
    global _db
    if _db is None:
        path = os.environ.get("TINYDB_PATH", "/data/db.json.enc")
        fernet = load_fernet()
        _db = TinyDB(path, storage=EncryptedJSONStorage, fernet=fernet)
    return _db


class TinyDbReader:
    def read(self, key: str) -> str | None:
        with _lock:
            results = _get_db().search(Query().key == key)
        return results[0]["value"] if results else None

    def all_map(self) -> dict[str, str]:
        with _lock:
            rows = _get_db().all()
        return {r["key"]: r["value"] for r in rows}

    def write(self, key: str, value: str) -> None:
        with _lock:
            _get_db().upsert({"key": key, "value": value}, Query().key == key)

    def delete(self, key: str) -> int:
        with _lock:
            removed = _get_db().remove(Query().key == key)
        return len(removed)


class TokenVault:
    """Random vaulted tokenization (SERVICE_MODE=tokenization).

    Tokens are opaque CSPRNG surrogates with no relationship to the value.
    Records live in a separate `tokens` table so they never collide with
    credential records sharing the same encrypted vault file.
    """

    _TABLE = "tokens"

    def _table(self):
        return _get_db().table(self._TABLE)

    def tokenize(self, value: str) -> str:
        """Store value under a fresh random token and return the token."""
        with _lock:
            table = self._table()
            q = Query()
            while True:
                token = f"tok_{secrets.token_urlsafe(32)}"
                # Astronomically unlikely, but verify uniqueness before insert.
                if not table.contains(q.token == token):
                    break
            table.insert(
                {
                    "token": token,
                    "value": value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        return token

    def detokenize(self, token: str) -> str | None:
        with _lock:
            results = self._table().search(Query().token == token)
        return results[0]["value"] if results else None

    def revoke(self, token: str) -> int:
        with _lock:
            removed = self._table().remove(Query().token == token)
        return len(removed)
