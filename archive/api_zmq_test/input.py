import time
import threading
import zmq

def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    # Bind to all interfaces on port 5555
    socket.bind("tcp://*:5555")

    def publish_null():
        """
        Continuously publish 'NULL' messages every second
        until the program is stopped.
        """
        while True:
            time.sleep(1)
            socket.send_string("NULL")
    
    # Start a background thread that keeps publishing "NULL"
    null_thread = threading.Thread(target=publish_null, daemon=True)
    null_thread.start()

    # Main thread: waits for user input and publishes it whenever entered
    print("Publisher started. Publishing 'NULL' until you type something...\n")
    print("Press Ctrl+C to exit.\n")

    while True:
        try:
            user_input = input("Enter your input: ").strip()
            # Publish the user input once
            if user_input:
                socket.send_string(user_input)
        except KeyboardInterrupt:
            print("\nExiting...")
            break

    # Clean up ZeroMQ
    socket.close()
    context.term()

if __name__ == "__main__":
    main()
