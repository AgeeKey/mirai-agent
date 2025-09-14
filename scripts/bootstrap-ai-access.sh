#!/usr/bin/env bash
# scripts/bootstrap-ai-access.sh
set -Eeuo pipefail
IFS=$'\n\t'

log() { printf "\033[1;36m[bootstrap]\033[0m %s\n" "$*"; }
fail() { printf "\033[1;31m[error]""\033[0m %s\n" "$*" >&2; exit 1; }

# --- Required envs ---------------------------------------------------------
# Accept CODEX as a fallback for GH_TOKEN if provided
if [[ -z "${GH_TOKEN:-}" && -n "${CODEX:-}" ]]; then
  export GH_TOKEN="$CODEX"
fi
if [[ -z "${GH_TOKEN:-}" ]]; then
  printf "\033[1;31m[error]\033[0m %s\n" "GH_TOKEN is required (scopes: repo, workflow, write:packages). You can also set CODEX as an alias." >&2
  exit 1
fi
: "${SSH_HOST:?SSH_HOST is required}"
: "${SSH_USER:?SSH_USER is required}"
if [[ -z "${SSH_KEY:-}" && -z "${SSH_KEY_B64:-}" ]]; then
  fail "Provide SSH_KEY (multiline private key) OR SSH_KEY_B64 (base64)."
fi

# --- Optional envs ---------------------------------------------------------
GHCR_USERNAME="${GHCR_USERNAME:-}"
GHCR_TOKEN="${GHCR_TOKEN:-$GH_TOKEN}"

BINANCE_API_KEY="${BINANCE_API_KEY:-}"
BINANCE_API_SECRET="${BINANCE_API_SECRET:-}"
DOMAIN_PANEL="${DOMAIN_PANEL:-}"
DOMAIN_STUDIO="${DOMAIN_STUDIO:-}"
ENVIRONMENT="${ENVIRONMENT:-}"
JWT_SECRET="${JWT_SECRET:-}"
WEB_USER="${WEB_USER:-}"
WEB_PASS="${WEB_PASS:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID_ADMIN="${TELEGRAM_CHAT_ID_ADMIN:-}"

# --- GitHub CLI auth -------------------------------------------------------
log "Authenticating GitHub CLI…"
if ! gh auth status >/dev/null 2>&1; then
  export GH_TOKEN
  gh auth login --with-token <<<"$GH_TOKEN"
fi
gh auth status || fail "GitHub auth failed"

if [[ -z "$GHCR_USERNAME" ]]; then
  GHCR_USERNAME="$(gh api user --jq .login 2>/dev/null || true)"
fi

# --- GHCR login ------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
  log "Logging into ghcr.io as ${GHCR_USERNAME}…"
  echo -n "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin || fail "Docker login to ghcr.io failed"
else
  log "Docker not found — skipping GHCR login"
fi

# --- SSH setup -------------------------------------------------------------
log "Preparing SSH key…"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
KEY_PATH="$HOME/.ssh/id_ed25519"

if [[ -n "${SSH_KEY:-}" ]]; then
  printf "%s\n" "$SSH_KEY" > "$KEY_PATH"
elif [[ -n "${SSH_KEY_B64:-}" ]]; then
  echo -n "$SSH_KEY_B64" | base64 -d > "$KEY_PATH"
fi
chmod 600 "$KEY_PATH"

ssh-keygen -y -f "$KEY_PATH" > "$KEY_PATH.pub" 2>/dev/null || true

if ! grep -q "^Host mirai-deploy$" "$HOME/.ssh/config" 2>/dev/null; then
  {
    echo "Host mirai-deploy"
    echo "  HostName $SSH_HOST"
    echo "  User $SSH_USER"
    echo "  IdentityFile $KEY_PATH"
    echo "  StrictHostKeyChecking accept-new"
    echo "  ServerAliveInterval 30"
    echo "  ServerAliveCountMax 5"
  } >> "$HOME/.ssh/config"
  chmod 600 "$HOME/.ssh/config"
fi

# --- Sanity checks ---------------------------------------------------------
log "Testing SSH connectivity…"
if ! ssh -o BatchMode=yes -o ConnectTimeout=8 mirai-deploy "echo ok"; then
  fail "SSH connection failed — check key, user, host, or server firewall"
fi

# --- Summary ---------------------------------------------------------------
log "Secrets summary:"
[[ -n "$BINANCE_API_KEY" ]] && log "  ✔ Binance API loaded"
[[ -n "$DOMAIN_PANEL" ]] && log "  ✔ Domain panel: $DOMAIN_PANEL"
[[ -n "$DOMAIN_STUDIO" ]] && log "  ✔ Domain studio: $DOMAIN_STUDIO"
[[ -n "$JWT_SECRET" ]] && log "  ✔ JWT_SECRET available"
[[ -n "$OPENAI_API_KEY" ]] && log "  ✔ OpenAI API key loaded"
[[ -n "$TELEGRAM_BOT_TOKEN" ]] && log "  ✔ Telegram bot enabled"
[[ -n "$WEB_USER" && -n "$WEB_PASS" ]] && log "  ✔ Web basic auth creds set"

log "GitHub, Docker, SSH, and integrations bootstrap complete ✅"
