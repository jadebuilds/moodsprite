#!/bin/sh
set -e

# Template config from env vars
envsubst < /workspace/config.template.toml > /zeroclaw-data/.zeroclaw/config.toml

# Start Jiron HTTP server if present
if [ -f /workspace/jiron/server.py ]; then
  python3 /workspace/jiron/server.py &
fi

# Wait for signal-cli daemon to be reachable, then send startup message
if [ -f /workspace/startup-message.txt ]; then
  MSG=$(cat /workspace/startup-message.txt)
  for i in 1 2 3 4 5 6 7 8 9 10; do
    zeroclaw channel send "$MSG" --channel-id signal && break
    sleep 3
  done &
fi

# Run Zeroclaw daemon as PID 1
exec zeroclaw daemon
