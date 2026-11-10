#!/bin/bash
# Launch Solera_BOT services + web UI (optionally fullscreen Chromium)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="${ROOT}/botenv"
if [[ -f "${VENV}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${VENV}/bin/activate"
fi

# Optional debug snooper
python3 "$ROOT/services/snooper.py" &

# Start voice pipeline
bash "$ROOT/scripts/start_bot.sh" &

# Start Flask web UI
cd "$ROOT/web_ui"
python3 app.py &

echo "Waiting for Flask on :5000..."
until curl -s http://127.0.0.1:5000 >/dev/null; do
  sleep 1
done

if command -v chromium-browser >/dev/null 2>&1; then
  chromium-browser --start-fullscreen http://127.0.0.1:5000
elif command -v chromium >/dev/null 2>&1; then
  chromium --start-fullscreen http://127.0.0.1:5000
else
  echo "Chromium not found — open http://127.0.0.1:5000 in a browser"
  wait
fi
