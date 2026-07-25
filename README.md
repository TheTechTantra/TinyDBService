# TinyDBService

A minimal FastAPI service that stores key/value credentials in a [TinyDB](https://tinydb.readthedocs.io/)
JSON file, **encrypted at rest** with [Fernet](https://cryptography.io/en/latest/fernet/) (AES-128-CBC + HMAC-SHA256)
and protected by an API key on every data endpoint.

Designed to be a low-footprint Docker sidecar (~128 MB RAM, 0.25 CPU) — the single source of
truth for runtime secrets across services that would otherwise need a `.env` file.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TINYDB_ENC_KEY` | **Yes** | Base64 Fernet key that encrypts the vault at rest |
| `SECRET_STORE_TOKEN` | No | `X-API-Key` value required on data endpoints. Unset = open (dev only) |
| `TINYDB_PATH` | No | Path to the encrypted vault file (default `/data/db.json.enc`) |
| `TINYDB_ENC_KEYS_OLD` | No | Comma-separated old Fernet keys used for decryption only (rotation) |

## Generate a new encryption key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Generate an API token

```bash
openssl rand -hex 24
```

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | Liveness probe — returns `{"status":"ok"}` |
| `GET` | `/credentials` | X-API-Key | All secrets as a flat `{key: value}` map |
| `POST` | `/key/` | X-API-Key | Upsert a credential: body `{"key": "...", "value": "..."}` |
| `GET` | `/credential/{key}` | X-API-Key | Read a single credential (404 if absent) |
| `DELETE` | `/key/{key}` | X-API-Key | Delete a credential (404 if absent) |

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export TINYDB_ENC_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export SECRET_STORE_TOKEN=$(openssl rand -hex 24)
export TINYDB_PATH=./data/db.json.enc
mkdir -p data

uvicorn app:app --host 0.0.0.0 --port 28080
```

## Run with Docker

Build:
```bash
docker build -t thetechtantra/tinydbservice:latest .
```

Run, mounting the vault file:
```bash
docker run \
  -e TINYDB_ENC_KEY="<your-key>" \
  -e SECRET_STORE_TOKEN="<your-token>" \
  -e TINYDB_PATH=/data/db.json.enc \
  -v /path/to/vault-dir:/data \
  -p 127.0.0.1:28080:28080 \
  thetechtantra/tinydbservice:latest
```

The vault directory must be writable by the container user (UID 999 by default). Either pre-create
the vault file and `chown` it, or `chmod o+rw` the directory.

## Key rotation (zero downtime)

1. Set `TINYDB_ENC_KEYS_OLD=<current-key>` alongside the new `TINYDB_ENC_KEY=<new-key>`.
2. Restart the container — existing ciphertext still decrypts via the old key fallback.
3. Make any write; the vault is re-encrypted under the new primary key.
4. Remove `TINYDB_ENC_KEYS_OLD` on the next deployment.

## Security notes

- The vault file is a single Fernet blob — no plaintext structure visible on disk.
- Atomic writes (temp + `os.replace`) minimise the partial-write window on mounted paths.
- `X-API-Key` is compared with constant-time `secrets.compare_digest` to prevent timing attacks.
- **Never store `TINYDB_ENC_KEY` beside the vault file.** Losing the key = permanently unrecoverable vault.
- Bind the host port to `127.0.0.1` only; grant in-cluster access via a private Docker network.
