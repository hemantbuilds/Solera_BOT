import zmq
import time

def main():
    context = zmq.Context()

    # 1) Socket for messages from port 5555 (treated as "input")
    socket_input = context.socket(zmq.SUB)
    socket_input.connect("tcp://127.0.0.1:5555")
    socket_input.setsockopt_string(zmq.SUBSCRIBE, "")

    # 2) Socket for messages from port 5556 (treated as "response")
    socket_response = context.socket(zmq.SUB)
    socket_response.connect("tcp://127.0.0.1:5556")
    socket_response.setsockopt_string(zmq.SUBSCRIBE, "")

    # 3) Poller to check both sockets
    poller = zmq.Poller()
    poller.register(socket_input, zmq.POLLIN)
    poller.register(socket_response, zmq.POLLIN)

    print("Subscriber connected to 5555 (input) and 5556 (response). Using ZMQ Poller.")
    print("Will store messages in /record.txt. Press Ctrl+C to stop.\n")

    while True:
        # Poll for up to 1 second
        events = dict(poller.poll(timeout=1000))

        # Check if there's a message on the 5555 socket
        if socket_input in events and events[socket_input] == zmq.POLLIN:
            msg_in = socket_input.recv_string()
            print(f"Received from 5555: {msg_in}")

            # Append to /record.txt
            with open("/record.txt", "a") as f:
                f.write(f"input = {msg_in}\n")

        # Check if there's a message on the 5556 socket
        if socket_response in events and events[socket_response] == zmq.POLLIN:
            msg_out = socket_response.recv_string()
            print(f"Received from 5556: {msg_out}")

            # Append to /record.txt
            with open("/record.txt", "a") as f:
                f.write(f"response = {msg_out}\n")

        # Avoid tight-loop spinning
        time.sleep(0.05)

if __name__ == "__main__":
    main()
