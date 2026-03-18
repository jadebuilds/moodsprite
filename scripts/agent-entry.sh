#!/bin/sh
set -e

# Template config from env vars
envsubst < /workspace/config.template.toml > /zeroclaw-data/.zeroclaw/config.toml

# Start Jiron HTTP server if present
if [ -f /workspace/jiron/server.py ]; then
  python3 /workspace/jiron/server.py &
fi

# Wait for signal-cli daemon to be reachable, then send startup message
# Uses signal-cli JSON-RPC directly since zeroclaw CLI doesn't support signal channel send
if [ -f /workspace/startup-message.txt ] && [ -n "${SIGNAL_HTTP_URL}" ] && [ -n "${SIGNAL_GROUP_ID}" ]; then
  MSG=$(cat /workspace/startup-message.txt)
  (
    for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -sf -X POST "${SIGNAL_HTTP_URL}/api/v1/rpc" \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"send\",\"params\":{\"groupId\":\"${SIGNAL_GROUP_ID}\",\"message\":\"${MSG}\"},\"id\":1}" \
        && break
      sleep 5
    done
  ) &
fi

# Run Zeroclaw daemon as PID 1
exec zeroclaw daemon
