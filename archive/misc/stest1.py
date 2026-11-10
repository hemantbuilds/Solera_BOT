import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5559")
print("Waiting for final messages...")
while True:
    message = socket.recv_string()
    print(f"Received final message: {message}")
