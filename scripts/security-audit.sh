#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT_DIR/reports/security_audit_$(date +%Y%m%d_%H%M%S).md"
mkdir -p "$ROOT_DIR/reports"

echo "# Security Audit" > "$OUT"
echo "Generated: $(date -Iseconds)" >> "$OUT"
echo >> "$OUT"

echo "## Open Ports" >> "$OUT"
ss -ltnp | sed 's/^/    /' >> "$OUT" || true

echo >> "$OUT"
echo "## World-writable files under project" >> "$OUT"
find "$ROOT_DIR" -xdev -type f -perm -0002 2>/dev/null | sed 's/^/    /' >> "$OUT" || true

echo >> "$OUT"
echo "## .env and secrets exposure" >> "$OUT"
grep -RIn "API_KEY\|SECRET\|TOKEN" "$ROOT_DIR/.env" "$ROOT_DIR" 2>/dev/null | sed 's/^/    /' >> "$OUT" || true

echo >> "$OUT"
echo "## Nginx TLS Configs" >> "$OUT"
grep -RIn "ssl_\|listen 443" "$ROOT_DIR/nginx" "$ROOT_DIR/deployment/nginx" 2>/dev/null | sed 's/^/    /' >> "$OUT" || true

echo >> "$OUT"
echo "## Dependency vulnerabilities (pip)" >> "$OUT"
python3 -m pip list --outdated --format=columns 2>/dev/null | sed 's/^/    /' >> "$OUT" || echo "    (pip not available)" >> "$OUT"

echo >> "$OUT"
echo "Audit saved to $OUT"

