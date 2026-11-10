import zmq

def subscribe_to_api_response():
    # Create a ZeroMQ context and subscriber socket
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    # Connect to the response publisher's IP
    subscriber.connect("tcp://127.0.0.1:5556")  # Response Publisher IP
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    print("Waiting for API responses...")
    while True:
        # Receive the API response
        api_response = subscriber.recv_string()
        print(f"API Response Received: {api_response}")

if __name__ == "__main__":
    subscribe_to_api_response()

