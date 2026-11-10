import zmq

# Initialize ZeroMQ context and subscriber socket
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)

# Connect to the publisher's ZMQ socket
sub_socket.connect("tcp://127.0.0.1:5556")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

print("Listening for messages on tcp://127.0.0.1:5556...")

try:
    while True:
        # Wait for a message
        message = sub_socket.recv_string()  # Blocking call
        print(f"Received message: {message}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    # Clean up ZMQ resources
    sub_socket.close()
    context.term()
