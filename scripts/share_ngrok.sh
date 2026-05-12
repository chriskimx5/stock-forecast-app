#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Bringing up services with docker compose..."
docker compose up -d --build

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok CLI not found. Install ngrok and run: ngrok config add-authtoken YOUR_TOKEN"
  exit 1
fi

echo "Stopping any existing ngrok processes..."
pkill -f "ngrok" >/dev/null 2>&1 || true

echo "Starting backend tunnel on port 8000..."
ngrok http 8000 --log=stdout > /tmp/ngrok_backend.log 2>&1 &
backend_pid=$!

sleep 2

echo "Starting frontend tunnel on port 3000..."
ngrok http 3000 --log=stdout > /tmp/ngrok_frontend.log 2>&1 &
frontend_pid=$!

cleanup() {
  echo
  echo "Stopping ngrok tunnels..."
  kill "$backend_pid" "$frontend_pid" >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Waiting for ngrok APIs..."

for i in {1..30}; do
  BACKEND_JSON="$(curl -sS http://127.0.0.1:4040/api/tunnels 2>/dev/null || true)"
  FRONTEND_JSON="$(curl -sS http://127.0.0.1:4041/api/tunnels 2>/dev/null || true)"

  if [[ -n "$BACKEND_JSON" && -n "$FRONTEND_JSON" ]]; then
    break
  fi

  sleep 1
done

BACKEND_JSON="$(curl -sS http://127.0.0.1:4040/api/tunnels 2>/dev/null || true)"
FRONTEND_JSON="$(curl -sS http://127.0.0.1:4041/api/tunnels 2>/dev/null || true)"

if [[ -z "$BACKEND_JSON" ]]; then
  echo "Backend ngrok API not found on 4040. Backend log:"
  cat /tmp/ngrok_backend.log
  exit 1
fi

if [[ -z "$FRONTEND_JSON" ]]; then
  echo "Frontend ngrok API not found on 4041. Frontend log:"
  cat /tmp/ngrok_frontend.log
  exit 1
fi

BACKEND_URL="$(
  echo "$BACKEND_JSON" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for t in data.get("tunnels", []):
    url = t.get("public_url", "")
    if url.startswith("https://"):
        print(url)
        break
'
)"

FRONTEND_URL="$(
  echo "$FRONTEND_JSON" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for t in data.get("tunnels", []):
    url = t.get("public_url", "")
    if url.startswith("https://"):
        print(url)
        break
'
)"

if [[ -z "${BACKEND_URL:-}" ]]; then
  echo "Could not extract backend URL. Backend JSON:"
  echo "$BACKEND_JSON"
  exit 1
fi

if [[ -z "${FRONTEND_URL:-}" ]]; then
  echo "Could not extract frontend URL. Frontend JSON:"
  echo "$FRONTEND_JSON"
  exit 1
fi

SHARE_URL="${FRONTEND_URL}/?backend=${BACKEND_URL}"

echo
echo "Public URLs:"
echo
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo
echo "Single shareable app link:"
echo
echo "$SHARE_URL"
echo
echo "Send only the single shareable app link above."
echo "Keep this terminal open while sharing the app."
echo "Press Ctrl+C to stop."
echo

while true; do
  sleep 3600
done