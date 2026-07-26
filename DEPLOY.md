# TinyDBService — Build, Deploy & Seed

Operational runbook for building the Docker image, deploying the container, and
seeding values into it. Commands assume you are in the repo root
(`TinyDBService/`) with the Docker daemon running.

---

## 0. Prerequisites

- Docker + Docker Compose installed and the daemon running.
- `docker login` completed for the `thetechtantra` account (only needed to push).
- A `.env` file created from `.env.example`:

  ```bash
  cp .env.example .env
  ```

- Generate the two secrets and put them in `.env` (or export them in your shell):

  ```bash
  # Fernet encryption key (encrypts the vault at rest)
  TINYDB_ENC_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

  # API token required on every data endpoint (X-API-Key)
  SECRET_STORE_TOKEN=$(openssl rand -hex 24)
  ```

  > ⚠️ **Never store `TINYDB_ENC_KEY` beside the vault file.** Losing the key
  > makes the vault permanently unrecoverable. Never commit real values.

`.env` variables consumed by `docker-compose.yml`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `TINYDB_ENC_KEY` | **Yes** | Base64 Fernet key encrypting the vault at rest |
| `SECRET_STORE_TOKEN` | No (recommended) | `X-API-Key` value; unset = open, dev only |
| `VAULT_DIR` | No | Host path mounted at `/data` (default `./data`) |
| `DOCKER_NETWORK` | No | External network name (default `tinydb-net`) |
| `SERVICE_MODE` | No | `credentials` (default) or `tokenization` |

---

## 1. Build the Docker image

### Option A — helper script (builds + pushes both tags)

```bash
bash build.sh              # build + push  :<git-sha>  and  :latest
bash build.sh --no-push    # build only (local smoke-test, no push)
```

Tags produced:

- `thetechtantra/tinydbservice:<sha>` — immutable, pinnable
- `thetechtantra/tinydbservice:latest` — mutable, what compose pulls

### Option B — manual build

```bash
docker build \
  --build-arg GIT_COMMIT="$(git rev-parse --short HEAD)" \
  --tag thetechtantra/tinydbservice:latest \
  .
```

`GIT_COMMIT` is baked into the image as `APP_VERSION` and reported by `/health`.

> ⚠️ **Publication boundary:** the image is PUBLIC. Every file in the Dockerfile
> `COPY` list ships as readable source inside the image. Never switch to
> `COPY . .`; keep `.env`, `db.json*`, and `.git` excluded via `.dockerignore`.

### Push manually (if not using build.sh)

```bash
docker push thetechtantra/tinydbservice:latest
```

---

## 2. Deploy the container

### Option A — Docker Compose (recommended)

```bash
docker compose pull tinydbservice          # pull latest image
docker compose up -d tinydbservice         # start detached
```

The service binds **loopback only** (`127.0.0.1:28080:28080`): host-side
seeding/inspection works, LAN cannot reach it. In-cluster services reach it by
name over the `app-net` network at `http://tinydbservice:28080`.

Manage:

```bash
docker compose logs -f tinydbservice       # follow logs
docker compose restart tinydbservice       # restart
docker compose down                        # stop & remove
```

### Option B — plain `docker run`

```bash
docker run -d \
  --name tinydbservice \
  -e TINYDB_ENC_KEY="<your-key>" \
  -e SECRET_STORE_TOKEN="<your-token>" \
  -e TINYDB_PATH=/data/db.json.enc \
  -v /path/to/vault-dir:/data \
  -p 127.0.0.1:28080:28080 \
  thetechtantra/tinydbservice:latest
```

> The vault directory must be writable by the container user (UID 999). Either
> pre-create + `chown` the vault file, or `chmod o+rw` the directory.

### Verify it is healthy

```bash
curl -s http://127.0.0.1:28080/health
# {"status":"ok","mode":"credentials"}

docker compose ps                          # STATUS should show (healthy)
```

---

## 3. Seed values into the container

Seeding is done over the loopback-bound HTTP API. Export the token first so it
is sent as `X-API-Key` on every request:

```bash
export SECRET_STORE_TOKEN=<your-token>     # same value set at deploy time
export BASE=http://127.0.0.1:28080
```

### `credentials` mode (default)

**Upsert a single key/value:**

```bash
curl -s -X POST "$BASE/key/" \
  -H "X-API-Key: $SECRET_STORE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "DB_PASSWORD", "value": "s3cr3t"}'
```

**Seed many values from a JSON file** (`seed.json` = `{"KEY": "value", ...}`):

```bash
# seed.json example:
# { "DB_PASSWORD": "s3cr3t", "API_KEY": "abc123", "SMTP_PASS": "hunter2" }

jq -r 'to_entries[] | @json' seed.json | while read -r entry; do
  key=$(echo "$entry"   | jq -r '.key')
  value=$(echo "$entry" | jq -r '.value')
  curl -s -X POST "$BASE/key/" \
    -H "X-API-Key: $SECRET_STORE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg k "$key" --arg v "$value" '{key:$k, value:$v}')"
  echo "seeded $key"
done
```

**Read back / verify:**

```bash
curl -s "$BASE/credentials"          -H "X-API-Key: $SECRET_STORE_TOKEN"   # all as {key: value}
curl -s "$BASE/credential/DB_PASSWORD" -H "X-API-Key: $SECRET_STORE_TOKEN" # single key
```

**Delete:**

```bash
curl -s -X DELETE "$BASE/key/DB_PASSWORD" -H "X-API-Key: $SECRET_STORE_TOKEN"
```

### `tokenization` mode (`SERVICE_MODE=tokenization`)

Store a value and receive an opaque surrogate token:

```bash
# Tokenize — returns {"token": "tok_..."}
curl -s -X POST "$BASE/tokenize" \
  -H "X-API-Key: $SECRET_STORE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "s3cr3t"}'

# Detokenize — token goes in the BODY (keeps it out of proxy/access logs)
curl -s -X POST "$BASE/detokenize" \
  -H "X-API-Key: $SECRET_STORE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "tok_..."}'

# Revoke a token
curl -s -X DELETE "$BASE/token/tok_..." -H "X-API-Key: $SECRET_STORE_TOKEN"
```

---

## 4. Key rotation (zero downtime)

1. Set `TINYDB_ENC_KEYS_OLD=<current-key>` alongside a new `TINYDB_ENC_KEY=<new-key>`.
2. Restart the container — existing ciphertext still decrypts via the old key.
3. Make any write; the vault is re-encrypted under the new primary key.
4. Remove `TINYDB_ENC_KEYS_OLD` on the next deployment.
