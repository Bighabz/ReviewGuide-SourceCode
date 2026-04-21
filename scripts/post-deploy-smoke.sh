#!/usr/bin/env bash
# Post-deploy smoke check
# Usage: BACKEND_URL=https://your-backend.com scripts/post-deploy-smoke.sh
# Exits non-zero on any failure so CI/Railway can page on regressions.

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-https://backend-production-0ae7.up.railway.app}"
TIMEOUT="${TIMEOUT:-30}"
FAIL=0

say() { printf '\n▸ %s\n' "$*"; }
fail() { printf '✗ %s\n' "$*" >&2; FAIL=1; }
ok() { printf '✓ %s\n' "$*"; }

# ---------------------------------------------------------------------------
# 1. Health endpoint must return 200
# ---------------------------------------------------------------------------
say "checking /health …"
HEALTH_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$BACKEND_URL/health" || echo "000")
if [[ "$HEALTH_CODE" == "200" ]]; then
  ok "/health returned 200"
else
  fail "/health returned $HEALTH_CODE (expected 200)"
fi

# ---------------------------------------------------------------------------
# 2. Product chat query must return non-empty ui_blocks with an Amazon tag
# ---------------------------------------------------------------------------
say "running canonical product query …"
PRODUCT_BODY=$(cat <<'EOF'
{"message":"best wireless earbuds under $100","session_id":null}
EOF
)
# Stream the SSE response to a temp file so we can grep it.
PRODUCT_OUT=$(mktemp)
trap 'rm -f "$PRODUCT_OUT"' EXIT

curl -sSN --max-time "$TIMEOUT" \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  -d "$PRODUCT_BODY" \
  "$BACKEND_URL/v1/chat/stream" > "$PRODUCT_OUT" || true

if ! [[ -s "$PRODUCT_OUT" ]]; then
  fail "product chat stream returned no body"
elif grep -qi 'error while formatting the response' "$PRODUCT_OUT"; then
  fail "product compose returned the error-fallback string"
elif ! grep -q '"ui_blocks"' "$PRODUCT_OUT"; then
  fail "product chat stream had no ui_blocks payload"
elif ! grep -q 'tag=revguide-20' "$PRODUCT_OUT"; then
  fail "product chat produced an Amazon link without tag=revguide-20 (revenue leak)"
else
  ok "product query produced ui_blocks AND Amazon tag present"
fi

# ---------------------------------------------------------------------------
# 3. Travel chat query must NOT hang (has a timeout/recovery path)
# ---------------------------------------------------------------------------
say "running canonical travel query …"
TRAVEL_BODY=$(cat <<'EOF'
{"message":"plan a 5-day trip to Tokyo","session_id":null}
EOF
)
TRAVEL_OUT=$(mktemp)
trap 'rm -f "$PRODUCT_OUT" "$TRAVEL_OUT"' EXIT

# 45s upper bound — if it's still streaming, kill and record failure.
if ! timeout 45 curl -sSN \
     -H 'Content-Type: application/json' \
     -H 'Accept: text/event-stream' \
     -d "$TRAVEL_BODY" \
     "$BACKEND_URL/v1/chat/stream" > "$TRAVEL_OUT"; then
  fail "travel chat hung or errored (>45s or non-zero curl exit)"
elif ! [[ -s "$TRAVEL_OUT" ]]; then
  fail "travel chat returned no body"
elif ! grep -qE '("event": ?"done"|"done"|artifact|clarifier)' "$TRAVEL_OUT"; then
  fail "travel chat completed but no 'done'/'artifact'/'clarifier' event seen"
else
  ok "travel query completed within 45s with a terminal event"
fi

# ---------------------------------------------------------------------------
# Exit summary
# ---------------------------------------------------------------------------
if [[ "$FAIL" -ne 0 ]]; then
  printf '\n✗ POST-DEPLOY SMOKE CHECK FAILED (BACKEND_URL=%s)\n' "$BACKEND_URL" >&2
  exit 1
fi

printf '\n✓ Post-deploy smoke check OK (BACKEND_URL=%s)\n' "$BACKEND_URL"
