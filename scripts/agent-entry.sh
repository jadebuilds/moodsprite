#!/bin/sh
set -e

# Template config from env vars
envsubst < /workspace/config.template.toml > /zeroclaw-data/.zeroclaw/config.toml
mkdir -p /zeroclaw-data/jiron

# Start Jiron HTTP server if present
if [ -f /workspace/jiron/server.py ]; then
  python3 /workspace/jiron/server.py &
fi

# Signal DM to human owner
if [ -f /workspace/startup-message.txt ] && [ -n "${SIGNAL_HTTP_URL}" ] && [ -n "${OWNER_PHONE}" ]; then
  MSG=$(cat /workspace/startup-message.txt)
  (
    for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -sf -X POST "${SIGNAL_HTTP_URL}/api/v1/rpc" \
        -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"send\",\"params\":{\"recipient\":[\"${OWNER_PHONE}\"],\"message\":\"${MSG}\"},\"id\":1}" \
        && break
      sleep 5
    done
  ) &
fi

# Discord ops channel announcement
if [ -f /workspace/discord-startup-message.txt ] && [ -n "${DISCORD_BOT_TOKEN}" ] && [ -n "${DISCORD_OPS_CHANNEL_ID}" ]; then
  DMSG=$(cat /workspace/discord-startup-message.txt)
  (
    for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -sf -X POST "https://discord.com/api/v10/channels/${DISCORD_OPS_CHANNEL_ID}/messages" \
        -H "Authorization: Bot ${DISCORD_BOT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"content\":\"${DMSG}\"}" \
        && break
      sleep 5
    done
  ) &
fi

# Run Zeroclaw daemon as PID 1
exec zeroclaw daemon
