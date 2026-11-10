#!/bin/bash

# Replace with your AssemblyAI API key
API_KEY="YOUR_ASSEMBLYAI_API_KEY"
ASSEMBLYAI_URL="wss://api.assemblyai.com/v2/realtime/ws?sample_rate=48000"

# Dependency check
if ! command -v wscat &>/dev/null; then
  echo "wscat is not installed. Installing..."
  npm install -g wscat
fi

if ! command -v arecord &>/dev/null; then
  echo "arecord is not installed. Please install alsa-utils."
  exit 1
fi

# Start recording and streaming audio
echo "Starting audio streaming to AssemblyAI..."
arecord -f S16_LE -r 16000 | base64 | while read -r audio_chunk; do
  echo "{\"audio_data\": \"$audio_chunk\"}" | wscat -H "Authorization: $API_KEY" -c "$ASSEMBLYAI_URL"
done

