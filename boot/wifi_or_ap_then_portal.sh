#!/bin/bash
# Boot helper: if not on WiFi, start AP then open the config portal.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

WIFI_DEVICE="wlan0"
AP_MODE_SCRIPT="$ROOT/scripts/ap_mode.sh"
WIFI_PORTAL_SCRIPT="$ROOT/wifi_portal/portal.py"
PYTHON_ENV="$ROOT/botenv/bin/activate"

check_wifi() {
  nmcli -t -f DEVICE,STATE dev | grep -q "${WIFI_DEVICE}:connected"
}

if check_wifi; then
  echo "WiFi already connected. Nothing to do."
else
  echo "Starting AP Mode..."
  sudo bash "$AP_MODE_SCRIPT"

  echo "Waiting before launching WiFi portal..."
  sleep 60

  echo "Launching WiFi portal..."
  if [[ -f "$PYTHON_ENV" ]]; then
    # shellcheck disable=SC1090
    source "$PYTHON_ENV"
  fi
  sudo python3 "$WIFI_PORTAL_SCRIPT" &

  while true; do
    sleep 10
    if check_wifi; then
      echo "Connected to WiFi. Cleaning up and rebooting..."
      pkill -f "$WIFI_PORTAL_SCRIPT" || true
      nmcli connection down Hotspot || true
      sudo reboot
    fi
  done
fi
