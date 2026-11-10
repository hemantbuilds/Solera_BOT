#!/usr/bin/env python3
"""Start the Solera WiFi hotspot for first-time configuration."""

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

INTERFACE = "wlan0"
SSID = os.getenv("HOTSPOT_SSID", "Solera_config")
PASSWORD = os.getenv("HOTSPOT_PASSWORD", "solera123")

try:
    print("Disconnecting existing connection on wlan0...")
    subprocess.run(["nmcli", "device", "disconnect", INTERFACE], check=True)

    print("Starting hotspot...")
    subprocess.run(
        [
            "nmcli",
            "device",
            "wifi",
            "hotspot",
            "ifname",
            INTERFACE,
            "ssid",
            SSID,
            "password",
            PASSWORD,
        ],
        check=True,
    )
    print(f"Hotspot '{SSID}' started on '{INTERFACE}'")
except subprocess.CalledProcessError as e:
    print("Failed to start hotspot:", e)
