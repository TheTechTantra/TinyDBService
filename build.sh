#!/usr/bin/env bash
# build.sh — Build and push TinyDBService to Docker Hub.
#
# Tags produced:
#   thetechtantra/tinydbservice:<sha>    — immutable, pinnable
#   thetechtantra/tinydbservice:latest  — mutable, what compose pulls
#
# Usage:
#   bash build.sh              # build + push both tags
#   bash build.sh --no-push    # build only (local smoke-test)
#
# Prerequisites:
#   - Docker daemon running
#   - `docker login` already completed for thetechtantra

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[build]${NC} $*"; }
warn()  { echo -e "${YELLOW}[build]${NC} $*"; }
error() { echo -e "${RED}[build]${NC} $*" >&2; exit 1; }

# ── Parse flags ───────────────────────────────────────────────────────────────
DO_PUSH=true
for arg in "$@"; do
  case "$arg" in
    --no-push) DO_PUSH=false ;;
    --help|-h)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *) error "Unknown flag: $arg  (use --no-push | --help)" ;;
  esac
done

# ── Resolve git SHA ───────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
GIT_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

if [[ "$GIT_COMMIT" == "unknown" ]]; then
  warn "Could not resolve git SHA — image will be tagged 'unknown'"
fi

IMAGE_BASE="thetechtantra/tinydbservice"
SHA_TAG="${IMAGE_BASE}:${GIT_COMMIT}"
LATEST_TAG="${IMAGE_BASE}:latest"

# ── Build ─────────────────────────────────────────────────────────────────────
info "Building ${SHA_TAG}  (commit ${GIT_COMMIT})"
docker build \
  --build-arg GIT_COMMIT="${GIT_COMMIT}" \
  --tag "${SHA_TAG}" \
  --tag "${LATEST_TAG}" \
  "${REPO_ROOT}"

info "Built:"
info "  ${SHA_TAG}"
info "  ${LATEST_TAG}"

# ── Push ──────────────────────────────────────────────────────────────────────
if [[ "$DO_PUSH" == true ]]; then
  info "Pushing ${SHA_TAG} …"
  docker push "${SHA_TAG}"
  info "Pushing ${LATEST_TAG} …"
  docker push "${LATEST_TAG}"
  info "Done. To deploy: docker compose pull tinydbservice && docker compose up -d tinydbservice"
else
  warn "--no-push: skipped push. Run 'bash build.sh' to push."
fi
