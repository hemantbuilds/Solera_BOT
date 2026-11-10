import zmq

# Initialize ZeroMQ
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)

# Connect to the PUB socket on tcp://127.0.0.1:5560
sub_socket.connect("tcp://127.0.0.1:5560")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
print("Listening for START and STOP signals on tcp://127.0.0.1:5560")

try:
    while True:
        # Wait for a message
        message = sub_socket.recv_string()
        if message in ["START", "STOP"]:
            print(f"Received signal: {message}")
        else:
            print(f"Received unknown signal: {message}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    sub_socket.close()
    context.term()
