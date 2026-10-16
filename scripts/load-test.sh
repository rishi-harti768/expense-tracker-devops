#!/usr/bin/env bash
set -euo pipefail
URL="${URL:-http://expense-tracker.local/api/expenses}"
for i in $(seq 1 500); do curl -s "$URL" >/dev/null || true; done
echo "Load test completed"
