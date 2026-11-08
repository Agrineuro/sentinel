#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    echo "Docker Engine and the Docker Compose plugin are required. Install them, then run this script again." >&2
    exit 1
fi

if [[ ! -f .env ]]; then
    if ! command -v openssl >/dev/null 2>&1; then
        echo "OpenSSL is required to generate private Sentinel keys." >&2
        exit 1
    fi
    vault_key="$(openssl rand -hex 32)"
    umask 077
    cat > .env <<EOF
ENVIRONMENT=production
VAULT_KEY=$vault_key
SENTINEL_BIND=127.0.0.1
SENTINEL_PORT=8080
HEALTH_POLL_INTERVAL_SECONDS=30
EOF
    chmod 600 .env
else
    vault_key="$(sed -n 's/^VAULT_KEY=//p' .env | head -n 1)"
    if [[ -z "$vault_key" || "$vault_key" == replace_* ]]; then
        echo "The existing .env must contain a real, non-empty VAULT_KEY value." >&2
        echo "Back up any existing .env, remove placeholder values, then rerun this script." >&2
        exit 1
    fi
    chmod 600 .env
fi

docker compose up --build -d
sentinel_port="$(sed -n 's/^SENTINEL_PORT=//p' .env | head -n 1)"
sentinel_port="${sentinel_port:-8080}"
echo "Sentinel is starting. Open http://localhost:$sentinel_port on this machine."
echo "On first visit, create the Sentinel administrator account."
