#!/usr/bin/env bash
set -euo pipefail

# Create the "neshemet" Signal group with all agent + human phone numbers.
# Run once after Signal CLI instances are registered and running.
#
# Usage: ./scripts/setup-signal-group.sh
#
# Requires: .env with phone numbers, signal-cli REST APIs running

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../.env"

SIGNAL_API="${SIGNAL_API_URL_GHOSTWHEEL:-http://localhost:8081}"
GROUP_NAME="neshemet"

echo "Creating Signal group '${GROUP_NAME}'..."
echo "Admin phone: ${GHOSTWHEEL_PHONE}"
echo "Members: ${AYA_PHONE}, ${ALASTAIR_PHONE}"

RESPONSE=$(curl -s -X POST "${SIGNAL_API}/v1/groups/${GHOSTWHEEL_PHONE}" \
  -H 'Content-Type: application/json' \
  -d "{
    \"name\": \"${GROUP_NAME}\",
    \"members\": [\"${AYA_PHONE}\", \"${ALASTAIR_PHONE}\"]
  }")

GROUP_ID=$(echo "${RESPONSE}" | jq -r '.id // empty')

if [ -z "${GROUP_ID}" ]; then
  echo "Failed to create group. Response:"
  echo "${RESPONSE}" | jq .
  exit 1
fi

echo ""
echo "Group created successfully!"
echo "Group ID: ${GROUP_ID}"
echo ""
echo "Add this to your .env file:"
echo "SIGNAL_GROUP_ID=${GROUP_ID}"
echo ""
echo "To add human members (Jade, Bex), have them join via invite link,"
echo "or add them manually through the Signal app on each phone."
