import zmq

def publish_message():
    # Input message to publish
    input_message = input("Enter the string to publish: ")

    # Create a ZeroMQ context and socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    # Bind the socket to an IP and port
    socket.bind("tcp://127.0.0.1:5555")  # Publisher IP

    print(f"Publishing message: {input_message}")
    # Publish the message
    socket.send_string(input_message)

if __name__ == "__main__":
    publish_message()
