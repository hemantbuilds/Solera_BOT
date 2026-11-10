import zmq

# Initialize ZeroMQ context and socket
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5559")  # Connect to the same IP and port as the publisher

# Set the subscription filter to receive all messages
# Use an empty string to subscribe to all topics
socket.setsockopt_string(zmq.SUBSCRIBE, "")

print("ZMQ Server is running. Waiting for messages...")
last_message = None  # Variable to store the last non-empty message

try:
    while True:
        # Receive message from the publisher
        message = socket.recv_string()
        if message.strip():  # If the message is not empty
            last_message = message
            print(f"Received: {message}")
        else:
            print(f"Final message before empty string: {last_message}")
except KeyboardInterrupt:
    print("\nServer interrupted. Exiting...")
finally:
    context.term()
