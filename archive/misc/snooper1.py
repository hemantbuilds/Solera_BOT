import zmq
import time

def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    # Connect to two publisher endpoints
    socket.connect("tcp://127.0.0.1:5559")
    socket.connect("tcp://127.0.0.1:5556")

    # Subscribe to all topics
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    # Create a Poller to handle socket events
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    print("Subscriber connected to 5555 and 5556. (Using ZMQ Poller)")
    print("Printing every message as it arrives:\n")

    while True:
        # Poll for up to 1 second (1000 ms)
        events = dict(poller.poll(timeout=1000))

        if socket in events and events[socket] == zmq.POLLIN:
            # Grab all messages currently in the queue
            while True:
                try:
                    msg = socket.recv_string(zmq.NOBLOCK)
                    print(f"Received: {msg}")
                except zmq.Again:
                    # No more messages in the queue
                    break

        # Optional small sleep to avoid busy-looping
        time.sleep(0.05)

if __name__ == "__main__":
    main()
