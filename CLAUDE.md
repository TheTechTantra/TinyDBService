# TinyDBService — working notes for Claude

Encrypted key/value + tokenization credential store (FastAPI). Two run modes via
`SERVICE_MODE`: `credentials` (default, encryption-at-rest) and `tokenization`
(random vaulted surrogates). Vault is Fernet-encrypted at rest in both modes.

## ⚠️ Publication boundary — read before ANY change

- The **Docker image `thetechtantra/tinydbservice` is PUBLIC.**
- The **GitHub repo is PRIVATE** (Docker Hub free tier allows only one private
  repo, and it is used elsewhere).
- **The image — not GitHub — is the publication boundary.** Every file in the
  Dockerfile `COPY` list ships as readable source inside the public image:
  `docker run --rm --entrypoint sh thetechtantra/tinydbservice:latest -c 'cat /app/*.py'`.
  Treat those files as fully public regardless of the repo being private.
- Files NOT copied into the image stay private with the repo: `docker-compose.yml`,
  `build.sh`, `README.md`, `.env`, `.git`, `CLAUDE.md`.

## Guardrails — confirm these hold before building/pushing the image or committing

1. **No secrets or PII in COPY'd source** (`app.py`, `auth.py`, `crypto.py`,
   `TinyDBUtil.py`, `CredentialModel.py`, `__init__.py`): no hardcoded keys or
   tokens, no personal filesystem paths (`/Users/...`), no real hostnames. Keys
   and tokens are runtime env only.
2. **`.dockerignore` keeps secrets out of the image**: `.env`, `db.json*`,
   `.git` stay excluded. Never switch to `COPY . .` — keep the explicit COPY list.
3. **No real values committed.** Personal paths and the real network name live in
   `.env` (gitignored). `docker-compose.yml` references them via `${VAULT_DIR}` /
   `${DOCKER_NETWORK}` — never literal `/Users/...` paths. Keep `.env.example` as
   the sanitized template.
4. **Adding a new Python module?** Add it to the Dockerfile `COPY` line (or it
   won't be in the image) AND re-check it against guardrail #1 — it becomes public.

## Quick self-check

```bash
# 1. No PII / secrets in tracked files (should print nothing):
git grep -nEi 'amarjha|OneDrive|/Users/|secretstore|-----BEGIN' -- . ':!CLAUDE.md'

# 2. .env is ignored, .env.example is tracked:
git check-ignore .env && git ls-files --error-unmatch .env.example

# 3. Image contains only intended files:
docker run --rm --entrypoint sh thetechtantra/tinydbservice:latest -c 'ls /app'
```
