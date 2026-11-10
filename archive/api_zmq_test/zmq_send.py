import zmq

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.connect("tcp://127.0.0.1:5556")

while True:
    msg = input("Enter a message to publish: ")
    pub_socket.send_string(msg)

