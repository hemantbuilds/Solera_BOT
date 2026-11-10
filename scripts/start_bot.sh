#!/bin/bash
# Start the Solera_BOT pipeline (wake word → STT → agent → TTS → shutdown)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load secrets if present
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

VENV="${ROOT}/botenv"
if [[ -f "${VENV}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${VENV}/bin/activate"
  echo "venv activated"
else
  echo "WARNING: ${VENV} not found — using system Python"
fi

trap 'echo "Exiting..."; pkill -f "wakeword/wake.py|stt/transcribe.py|agent/processor.py|tts/speak.py|services/shutdown.py" 2>/dev/null || true; exit' SIGINT

echo "Starting wake word detection..."
(cd "$ROOT/wakeword" && python3 wake.py) &
sleep 3

echo "Starting realtime transcription..."
python3 "$ROOT/stt/transcribe.py" &
sleep 2

echo "Starting agent API processor..."
python3 "$ROOT/agent/processor.py" &
sleep 2

echo "Starting speech generator..."
python3 "$ROOT/tts/speak.py" &
sleep 2

echo "Starting shutdown service..."
python3 "$ROOT/services/shutdown.py" &
sleep 2

echo "Solera_BOT pipeline is running. Enjoy!"
wait
