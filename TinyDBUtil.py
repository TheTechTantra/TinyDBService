import os
import threading

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
