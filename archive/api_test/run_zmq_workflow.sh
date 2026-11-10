#!/bin/bash

# Start Script 1: Publisher
echo "Starting Publisher Script..."
python3 script1_publisher.py &
PUBLISHER_PID=$!
sleep 2  # Wait for the publisher to initialize

# Start Script 2: Subscriber + API Call + Republisher
echo "Starting Subscriber + API Script..."
python3 script2_subscriber_api.py &
SUBSCRIBER_API_PID=$!
sleep 2  # Wait for the subscriber and API script to initialize

# Start Script 3: API Response Subscriber
echo "Starting API Response Subscriber Script..."
python3 script3_response_subscriber.py &
SUBSCRIBER_RESPONSE_PID=$!
sleep 2  # Wait for the response subscriber to initialize

echo "All scripts are running. Enter a message in the publisher to proceed."

# Wait for all processes to complete (optional)
wait $PUBLISHER_PID
wait $SUBSCRIBER_API_PID
wait $SUBSCRIBER_RESPONSE_PID

echo "All processes have finished."
