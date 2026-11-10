import zmq
import threading

# ZMQ Addresses
START_STOP_IP = "tcp://127.0.0.1:5560"
TRANSCRIBED_IP = "tcp://127.0.0.1:5557"
FINAL_RESPONSE_IP = "tcp://127.0.0.1:5556"
FINISHED_IP = "tcp://127.0.0.1:5569"

def zmq_listener(ip, label):
    """
    Listens for messages on a ZMQ socket and prints them.
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(ip)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    while True:
        message = socket.recv_string()  # Blocking call
        print(f"Message from IP {ip}: {message}")


if __name__ == "__main__":
    # Start a separate thread for each IP listener
    threading.Thread(target=zmq_listener, args=(START_STOP_IP, "START/STOP"), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(TRANSCRIBED_IP, "TRANSCRIBED"), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(FINAL_RESPONSE_IP, "FINAL RESPONSE"), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(FINISHED_IP, "FINISHED"), daemon=True).start()

    # Keep the main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nExiting...")
