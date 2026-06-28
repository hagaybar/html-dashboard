#!/usr/bin/env bash
# watch.sh — block until the operator pings an element in the browser, then
# print the ping payload and exit (re-invoking Claude).
#   Env: DASH_SERVER (default http://localhost:8765), DASH_POLL_SECS (default 2)
set -u
SERVER="${DASH_SERVER:-http://localhost:8765}"
POLL="${DASH_POLL_SECS:-2}"

ping_ts() {
  local body
  body="$(curl -s "$SERVER/ping" 2>/dev/null || true)"
  [[ -z "$body" ]] && { echo 0; return; }
  printf '%s' "$body" | jq -r '.ts // 0' 2>/dev/null || echo 0
}

baseline="$(ping_ts)"
echo "[dash-watch] watching $SERVER/ping (baseline ts=$baseline) — waiting for a ping…" >&2
while true; do
  cur="$(ping_ts)"
  if [[ "$cur" != "$baseline" && "$cur" != "0" ]]; then
    echo "[dash-watch] NEW PING:"
    curl -s "$SERVER/ping"
    echo
    exit 0
  fi
  sleep "$POLL"
done
