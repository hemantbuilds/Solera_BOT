#!/bin/bash
# Quick helper to bring up the Solera config hotspot.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

SSID="${HOTSPOT_SSID:-Solera_config}"
PASS="${HOTSPOT_PASSWORD:-solera123}"

nmcli radio wifi off
sleep 2
nmcli radio wifi on
nmcli device wifi hotspot ifname wlan0 ssid "$SSID" password "$PASS"
echo "Hotspot '$SSID' is up."
