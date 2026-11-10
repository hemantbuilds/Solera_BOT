import subprocess
import re
import zmq
import threading
import time

# Initialize ZMQ
context = zmq.Context()
pub_socket = context.socket(zmq.PUB)  # PUB socket for sending control signals
pub_socket.bind("tcp://127.0.0.1:5560")  # Bind PUB socket
print("Publishing START/STOP signals on tcp://127.0.0.1:5560")

sub_socket = context.socket(zmq.SUB)  # SUB socket for listening to final messages
sub_socket.connect("tcp://127.0.0.1:5557")  # Connect to the transcription PUB socket
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print("Listening for final messages on tcp://127.0.0.1:5559")

# Function to listen for final transcription messages
def listen_for_final_messages():
    while True:
        try:
            message = sub_socket.recv_string()
            print(f"Final message received: {message}")
            print("Sending STOP signal...")
            pub_socket.send_string("STOP")
        except Exception as e:
            print(f"Error in listening for final messages: {e}")

# Start the final message listener in a separate thread
listener_thread = threading.Thread(target=listen_for_final_messages, daemon=True)
listener_thread.start()

def run_inference():
    """
    Monitors solera values from edge-impulse-linux-runner and sends START signal when solera > 0.65.
    """
    process = subprocess.Popen(
        ["edge-impulse-linux-runner"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        print("Listening for wake word... Press CTRL+C to stop.")
        time.sleep(1)  # Allow subscribers to connect before publishing
        for line in process.stdout:
            # Extract classification results using regex
            match = re.search(r"classifyRes \d+ms\. \{ (.*?) \}", line)
            if match:
                # Parse the classification results
                results = match.group(1)
                classifications = {k: float(v) for k, v in re.findall(r"(\w+): '([\d\.]+)'", results)}
                print("Classification Results:", classifications)

                # Check if solera > 0.65 and send START signal
                if classifications.get("solera", 0) > 0.75:
                    print("Wake word detected! Sending START signal...")
                    pub_socket.send_string("START")
    except KeyboardInterrupt:
        print("\nStopping inference...")
    finally:
        # Ensure the subprocess is terminated
        process.terminate()

if __name__ == "__main__":
    run_inference()
