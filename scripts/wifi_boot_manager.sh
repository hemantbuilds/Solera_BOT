#!/bin/bash
# On boot: if online, launch the UI; otherwise start AP + WiFi config portal.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

WIFI_DEVICE="wlan0"
SSID_HOTSPOT="${HOTSPOT_SSID:-Solera_config}"
PASSWORD_HOTSPOT="${HOTSPOT_PASSWORD:-solera123}"
WIFI_PORTAL_SCRIPT="$ROOT/wifi_portal/portal.py"
WEB_UI_LAUNCH_SCRIPT="$ROOT/scripts/launch_ui.sh"
PYTHON_ENV="$ROOT/botenv/bin/activate"

check_wifi_connected() {
  nmcli -t -f DEVICE,STATE dev | grep -q "${WIFI_DEVICE}:connected" \
    && ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1
}

start_web_ui() {
  echo "Starting Solera Web UI..."
  bash "$WEB_UI_LAUNCH_SCRIPT"
}

start_wifi_portal() {
  echo "Starting WiFi configuration portal on port 8080..."
  if [[ -f "$PYTHON_ENV" ]]; then
    # shellcheck disable=SC1090
    source "$PYTHON_ENV"
  fi
  python3 "$WIFI_PORTAL_SCRIPT" &
  echo "WiFi portal PID: $!"
}

start_ap_mode() {
  echo "Starting Access Point..."
  nmcli device wifi hotspot ifname "$WIFI_DEVICE" ssid "$SSID_HOTSPOT" password "$PASSWORD_HOTSPOT"
}

kill_portal_and_ap() {
  echo "Stopping WiFi Portal and Hotspot (if running)..."
  pkill -f "$WIFI_PORTAL_SCRIPT" 2>/dev/null || true
  HOTSPOT_NAME=$(nmcli -t -f NAME,TYPE con show --active | grep ":wifi" | cut -d ':' -f1 || true)
  if [[ "$HOTSPOT_NAME" == *Hotspot* ]]; then
    nmcli con down "$HOTSPOT_NAME" || true
  fi
}

echo "Checking WiFi connectivity..."
if check_wifi_connected; then
  echo "WiFi connected. Launching Web UI..."
  start_web_ui
else
  echo "No internet. Starting AP + WiFi config portal..."
  start_ap_mode
  start_wifi_portal

  echo "Waiting for WiFi connection via portal..."
  while true; do
    sleep 5
    if nmcli -t -f DEVICE,STATE dev | grep -q "${WIFI_DEVICE}:connected"; then
      echo "Wi-Fi associated. Waiting for internet..."
      sleep 10
      if ping -c 2 -W 2 8.8.8.8 >/dev/null 2>&1; then
        echo "Internet verified."
        kill_portal_and_ap
        start_web_ui
        break
      fi
      echo "Connected but no internet yet. Retrying..."
    fi
  done
fi
