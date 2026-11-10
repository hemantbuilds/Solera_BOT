# Solera_BOT Setup Guide

Step-by-step setup for a Raspberry Pi (tested around Raspberry Pi OS Bookworm / Python 3.11).

## 1. System packages

```bash
sudo apt update
sudo apt install -y \
  python3-venv python3-dev python3-pip \
  portaudio19-dev libasound2-dev \
  mpg123 \
  network-manager \
  chromium-browser \
  git
```

Confirm your mic shows up:

```bash
arecord -l
```

## 2. Clone / place the project

Put the repo where you want it permanently, e.g.:

```bash
cd ~
# or: /home/solera/Solera_BOT
```

All launch scripts resolve paths from the repo root — no hardcoded `/home/solera/...` required.

## 3. Python virtualenv

```bash
cd /path/to/Solera_BOT
python3 -m venv botenv
source botenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** An old `botenv/` copied from another machine will not work (broken interpreter paths). Always recreate the venv on the target Pi.

## 4. Configure secrets

```bash
cp .env.example .env
nano .env   # or your preferred editor
```

Fill in:

| Variable | Where to get it |
|----------|-----------------|
| `PICOVOICE_ACCESS_KEY` | https://console.picovoice.ai/ |
| `ASSEMBLYAI_API_KEY` | https://www.assemblyai.com/ |
| `AGENT_API_URL` | Your SendAI / Agent Kit `/api/chat` URL |
| `HOTSPOT_SSID` / `HOTSPOT_PASSWORD` | Credentials for the Pi’s setup AP |

The custom wake-word model is already in:

```
wakeword/solera_en_raspberry-pi_v3_0_0.ppn
```

If you retrain in Picovoice Console, replace that `.ppn` and keep the same filename (or update `wakeword/wake.py`).

## 5. Audio check

```bash
source botenv/bin/activate
python3 - <<'PY'
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info.get("maxInputChannels", 0) > 0:
        print(i, info.get("name"))
p.terminate()
PY

# Speaker cue used by wake word
mpg123 wakeword/sounds/bubble-pop-2-293341.mp3
```

## 6. Run manually

**Voice pipeline only:**

```bash
./start_bot.sh
```

**Pipeline + web UI (opens Chromium fullscreen when available):**

```bash
./launch_ui.sh
```

Then open http://127.0.0.1:5000 if the browser does not launch.

**Debug ZMQ traffic:**

```bash
source botenv/bin/activate
python3 services/snooper.py
```

**Reset stuck Python / ZMQ processes:**

```bash
./scripts/zmq-refresh.sh
```

## 7. First-time WiFi (AP portal)

If the Pi has no internet on boot:

```bash
./scripts/wifi_boot_manager.sh
```

Flow:

1. Creates hotspot `HOTSPOT_SSID` (default `Solera_config`)
2. Serves the portal at **http://10.42.0.1:8080** (typical NM hotspot IP)
3. After you join a network and internet works, launches the UI

Manual AP only:

```bash
./scripts/ap_mode.sh
python3 wifi_portal/portal.py
```

## 8. Optional: start on boot (systemd)

Example unit — adjust `User=` and paths:

```ini
# /etc/systemd/system/solera-bot.service
[Unit]
Description=Solera_BOT WiFi check + launch
After=network-online.target NetworkManager.service
Wants=network-online.target

[Service]
Type=simple
User=solera
WorkingDirectory=/home/solera/Solera_BOT
ExecStart=/home/solera/Solera_BOT/scripts/wifi_boot_manager.sh
Restart=on-failure
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/solera/.Xauthority

[Install]
WantedBy=graphical.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now solera-bot.service
sudo systemctl status solera-bot.service
```

For LCD ↔ HDMI helpers see `display/lcd_hdmi/`.

## 9. ZMQ ports (reference)

| Port | Direction | Purpose |
|------|-----------|---------|
| `5560` | wake → STT | `START` / `STOP` |
| `5557` | STT → agent / UI | final transcript |
| `5556` | agent → TTS / UI | `Thinking` + reply |
| `5569` | TTS → UI | `Finished` |
| `5000` | HTTP | Web UI |
| `8080` | HTTP | WiFi portal |

## 10. Troubleshooting

| Symptom | Check |
|---------|--------|
| `PICOVOICE_ACCESS_KEY is missing` | `.env` present and loaded from repo root |
| Porcupine activation error | Key valid for this device; `.ppn` matches platform (`raspberry-pi`) |
| No transcription | Mic index, AssemblyAI key, internet |
| Agent always fails | `AGENT_API_URL` reachable; `curl -X POST` with `{"message":"hi"}` |
| No speech | `mpg123` / pygame audio device; HDMI vs analog output |
| Hotspot fails | `nmcli` / NetworkManager running; not blocked by `dhcpcd`-only setups |
| Old `botenv` broken | Delete and recreate: `rm -rf botenv && python3 -m venv botenv` |

## Security reminder

- Never commit `.env`
- Rotate any keys that were previously hardcoded in older copies of this project
- Change `HOTSPOT_PASSWORD` from the default before deploying
