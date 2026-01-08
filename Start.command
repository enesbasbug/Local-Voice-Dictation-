#!/bin/bash
cd "$(dirname "$0")"
echo "🎙️ Starting VoiceToClipboard..."

# Prefer project virtualenv if present
VENV_PY="$(pwd)/.venv/bin/python"
if [ -x "$VENV_PY" ]; then
  exec "$VENV_PY" VoiceToClipboard.py
else
  # Fallback to system python
  exec python3 VoiceToClipboard.py
fi
