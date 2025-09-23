#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"
OUT="$REPORTS_DIR/weekly_report_$(date +%Y%m%d_%H%M%S).md"

echo "# Weekly Performance Review" > "$OUT"
echo "Generated: $(date -Iseconds)" >> "$OUT"
echo >> "$OUT"

echo "## Trading (last 48h quick view)" >> "$OUT"
python3 "$ROOT_DIR/app/trader/analytics_48h.py" | sed 's/^/    /' >> "$OUT" || echo "    (no data)" >> "$OUT"

echo >> "$OUT"
echo "## System Metrics Snapshots" >> "$OUT"
curl -s http://localhost:8000/metrics | head -n 50 | sed 's/^/    /' >> "$OUT" || echo "    (metrics unavailable)" >> "$OUT"

echo >> "$OUT"
echo "## Risk Settings Summary" >> "$OUT"
sed 's/^/    /' "$ROOT_DIR/configs/risk.yaml" >> "$OUT"

echo >> "$OUT"
echo "## Active Alerts (tail)" >> "$OUT"
tail -n 50 "$ROOT_DIR/logs/telegram-alerts.log" 2>/dev/null | sed 's/^/    /' >> "$OUT" || echo "    (no alerts)" >> "$OUT"

echo >> "$OUT"
echo "Report saved to $OUT"

