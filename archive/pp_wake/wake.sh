#!/bin/bash

# Picovoice Access Key
ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY"

# Path to custom wake word model (.ppn)
WAKEWORD_FILE="solera_en_raspberry-pi_v3_0_0.ppn"

# ZMQ Configuration
PUB_IP="tcp://127.0.0.1:5560"  # PUB socket for sending START/STOP
SUB_IP="tcp://127.0.0.1:5557"  # SUB socket for receiving responses

# Function to play a beep sound when wake word is detected
play_beep() {
    play -n synth 0.1 sin 440 > /dev/null 2>&1
}

# Ensure the required dependencies are installed
if ! command -v porcupine_demo_mic &> /dev/null; then
    echo "Error: porcupine_demo_mic is not installed. Installing now..."
    pip3 install pvporcupinedemo
fi

if ! command -v play &> /dev/null; then
    echo "Error: sox is not installed. Installing now..."
    sudo apt install sox -y
fi

# Start the ZMQ Publisher (Sending START/STOP Signals)
echo "Starting ZMQ Publisher..."
zmq_pub() {
    echo "Publishing START/STOP signals on $PUB_IP"
    while true; do
        message=$(nc -l -p 5560)  # Listen for messages from wake word detection
        if [[ "$message" == "START" ]]; then
            echo "Sending START signal..."
            echo "START" | nc -q 0 127.0.0.1 5560
        elif [[ "$message" == "STOP" ]]; then
            echo "Sending STOP signal..."
            echo "STOP" | nc -q 0 127.0.0.1 5560
        fi
    done
}

# Start the ZMQ Subscriber (Listening for Responses)
echo "Starting ZMQ Subscriber..."
zmq_sub() {
    echo "Listening for responses on $SUB_IP"
    while true; do
        response=$(nc -l -p 5557)  # Listen for responses
        if [[ "$response" == "response received" ]]; then
            echo "Response received, sending STOP signal..."
            echo "STOP" | nc -q 0 127.0.0.1 5560
        fi
    done
}

# Start wake word detection in the background
echo "Starting wake word detection..."
porcupine_demo_mic --access_key "$ACCESS_KEY" --keyword_paths "$WAKEWORD_FILE" | while read -r line; do
    if [[ "$line" == *"detected"* ]]; then
        echo "Wake word detected!"
        play_beep
        echo "START" | nc -q 0 127.0.0.1 5560  # Send START signal to ZMQ
    fi
done &

# Start ZMQ threads
zmq_pub &
zmq_sub &

# Wait for all background processes to finish
wait
