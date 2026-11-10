#!/bin/bash
# If WiFi is up, launch the bot UI; otherwise fall through to AP portal flow.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if nmcli -t -f DEVICE,STATE dev | grep -q "wlan0:connected"; then
  echo "WiFi connected — launching UI"
  bash "$ROOT/scripts/launch_ui.sh"
else
  echo "WiFi not connected — starting AP + portal"
  bash "$ROOT/boot/wifi_or_ap_then_portal.sh"
fi
