import zmq
import time

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5557")

print("Publishing messages to tcp://127.0.0.1:5557...")
while True:
    message = input("Enter message to publish: ")
    pub_socket.send_string(message)
    print(f"Published: {message}")
    time.sleep(1)
