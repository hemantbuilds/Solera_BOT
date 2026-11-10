import zmq

def main():
    context = zmq.Context()

    # Create a SUB socket to subscribe to the publisher at tcp://127.0.0.1:5556
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5555")

    # Subscribe to all topics
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    print("Subscriber connected to tcp://127.0.0.1:5555.")
    print("Printing all messages received. Press Ctrl+C to stop.\n")

    try:
        while True:
            message = subscriber.recv_string()
            print("Received:", message)
    except KeyboardInterrupt:
        print("\nSubscriber shutting down...")

    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
