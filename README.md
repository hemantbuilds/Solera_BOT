# Solera_BOT

Voice-controlled Raspberry Pi assistant integrated with **SendAI Agent Kit** for crypto / chat actions.

Say the wake word **“Solera”**, speak a request, and the bot transcribes it, calls the agent API, then replies with speech and a live web UI.

## How it works

```
Wake word (Picovoice) ──START──► STT (AssemblyAI) ──text──► Agent API (SendAI)
                                      ▲                         │
                                      │                         ▼
                                   STOP ◄────────────── TTS (gTTS) + Web UI
```

| Stage | Module | Role |
|-------|--------|------|
| Wake word | `wakeword/wake.py` | Porcupine listens for “Solera”, plays a cue, publishes `START`/`STOP` on ZMQ `:5560` |
| Speech-to-text | `stt/transcribe.py` | AssemblyAI realtime STT; publishes final transcripts on `:5557` |
| Agent | `agent/processor.py` | POSTs text to SendAI Agent Kit; publishes `Thinking` + reply on `:5556` |
| TTS | `tts/speak.py` | Speaks replies via gTTS; publishes `Finished` on `:5569` |
| Web UI | `web_ui/app.py` | Flask + Socket.IO dashboard on `:5000` |
| Shutdown | `services/shutdown.py` | Voice command “shutdown now” / “sleep now” |
| WiFi portal | `wifi_portal/` | AP + captive config when the Pi has no internet |

## Project layout

```
Solera_BOT/
├── .env.example          # template for secrets
├── .env                  # your keys (gitignored)
├── requirements.txt
├── SETUP.md              # install & boot guide
├── start_bot.sh          # convenience → scripts/start_bot.sh
├── launch_ui.sh          # convenience → scripts/launch_ui.sh
├── scripts/              # launchers, WiFi boot, AP helpers
├── boot/                 # boot-time WiFi / AP helpers
├── wakeword/             # Picovoice Porcupine + .ppn model + cue sound
├── stt/                  # AssemblyAI realtime transcription
├── agent/                # SendAI / Agent Kit ZMQ processor
├── tts/                  # gTTS speech output
├── web_ui/               # Flask + Socket.IO UI
├── wifi_portal/          # first-time WiFi config portal
├── services/             # shutdown listener + ZMQ snooper
├── display/              # LCD ↔ HDMI switch helpers
└── archive/              # old experiments / draft script versions
```

## Quick start

```bash
cd Solera_BOT
cp .env.example .env          # then edit keys
python3 -m venv botenv
source botenv/bin/activate
pip install -r requirements.txt

./start_bot.sh                # voice pipeline only
# or
./launch_ui.sh                # pipeline + web UI
```

Full hardware, audio, and systemd setup: see **[SETUP.md](SETUP.md)**.

## Secrets

All API keys and hotspot credentials live in **`.env`** (never commit it). Required:

- `PICOVOICE_ACCESS_KEY` — [Picovoice Console](https://console.picovoice.ai/)
- `ASSEMBLYAI_API_KEY` — [AssemblyAI](https://www.assemblyai.com/)
- `AGENT_API_URL` — SendAI / Agent Kit chat endpoint
- `HOTSPOT_SSID` / `HOTSPOT_PASSWORD` — AP used for on-device WiFi setup

## Notes

- Designed for **Raspberry Pi** with a USB mic / speaker and NetworkManager (`nmcli`).
- `botenv/` is intentionally gitignored — recreate it from `requirements.txt`.
- Draft scripts and Edge Impulse wake-word experiments are kept under `archive/` for reference only.
