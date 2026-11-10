#!/bin/bash

# ZMQ IP to subscribe to
ZMQ_IP="tcp://127.0.0.1:5556"

# Location of the ttsDemo executable
TTS_EXECUTABLE="/home/solana/piper/piper/ttsDemo"

# Check if ttsDemo exists
if [[ ! -f "$TTS_EXECUTABLE" ]]; then
    echo "Error: ttsDemo not found at $TTS_EXECUTABLE. Exiting."
    exit 1
fi

# Install dependencies for ZeroMQ Python if not already installed
if ! python3 -c "import zmq" 2>/dev/null; then
    echo "Installing zmq for Python..."
    pip install pyzmq
fi

# Launch ttsDemo and capture its PID
"$TTS_EXECUTABLE" &
TTS_PID=$!

# Check if ttsDemo started successfully
if ! ps -p $TTS_PID > /dev/null; then
    echo "Error: Failed to start ttsDemo. Exiting."
    exit 1
fi

# Python script to listen to ZMQ and send messages to ttsDemo
python3 - <<EOF
import zmq
import os
import signal
import subprocess

# ZeroMQ setup
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("$ZMQ_IP")
socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics

# Open a pipe to the ttsDemo process
pipe = os.popen("$TTS_EXECUTABLE", "w")

print("Listening for messages on $ZMQ_IP and feeding to ttsDemo...")
try:
    while True:
        message = socket.recv_string().strip()
        if message.startswith("response "):  # Check for "response" prefix
            # Remove "response" and clean up whitespace
            tts_message = message[len("response "):].strip()
            print(f"Processing message: {tts_message}")

            # Write the message to ttsDemo via the pipe
            pipe.write(tts_message + "\n")
            pipe.flush()
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    pipe.close()
    socket.close()
    context.term()
EOF

# Cleanup
kill $TTS_PID 2>/dev/null
