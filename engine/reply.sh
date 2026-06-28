#!/usr/bin/env bash
# reply.sh — post a reply that the dashboard renders inline.
#   Usage: reply.sh <elementId|-> <info|success|warn|error|question> "<text>"
#   Env:   DASH_SERVER (default http://localhost:8765)
set -euo pipefail
SERVER="${DASH_SERVER:-http://localhost:8765}"
if [[ $# -lt 3 ]]; then
  echo "usage: $0 <elementId|-> <level> <text>" >&2
  exit 2
fi
target="$1"; level="$2"; text="$3"
if [[ "$target" == "-" ]]; then
  payload="$(jq -n --arg level "$level" --arg text "$text" '{level:$level, text:$text}')"
else
  payload="$(jq -n --arg id "$target" --arg level "$level" --arg text "$text" \
    '{testId:$id, level:$level, text:$text}')"
fi
printf '%s' "$payload" | curl -sf -X POST "$SERVER/reply" \
  -H 'Content-Type: application/json' --data-binary @- \
  || { echo "reply failed — is the dashboard server running on $SERVER?" >&2; exit 1; }
echo
echo "posted reply target=$target level=$level"
