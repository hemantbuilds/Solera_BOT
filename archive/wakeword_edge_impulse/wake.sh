#!/bin/bash

# Set your Edge Impulse API key (Replace with your actual API key)
EI_API_KEY="<your_api_key>"  # Replace with your new API key

# Check if Edge Impulse is installed
if ! command -v edge-impulse-linux-runner &> /dev/null; then
    echo "❌ Edge Impulse runner not found! Please install it first."
    exit 1
fi

# List available microphone devices
echo "🔍 Listing available microphone devices..."
arecord -l

# Extract the fourth microphone device
MIC_DEVICE=$(arecord -l | grep -oP 'card \K\d+' | sed -n '4p')

if [ -z "$MIC_DEVICE" ]; then
    echo "❌ No fourth microphone device found! Exiting..."
    exit 1
fi

echo "🎤 Selected microphone device: card $MIC_DEVICE"

# Run Edge Impulse with the selected microphone and API key
echo "🚀 Running Edge Impulse with API key..."
edge-impulse-linux-runner --api-key "$EI_API_KEY" --device "$MIC_DEVICE"

# Check if it ran successfully
if [ $? -eq 0 ]; then
    echo "✅ Edge Impulse is running successfully!"
else
    echo "❌ Failed to start Edge Impulse. Check your API key and mic device."
    exit 1
fi
