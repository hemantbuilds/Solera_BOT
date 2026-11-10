import subprocess
import re
import zmq
import time

def run_inference():
    # Initialize ZMQ context and socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    zmq_ip = "tcp://127.0.0.1:5560"  # Replace with your desired ZMQ IP and port
    socket.bind(zmq_ip)
    print(f"Publishing to ZMQ at {zmq_ip}")

    # Start edge-impulse-linux-runner as a subprocess
    process = subprocess.Popen(
        ["edge-impulse-linux-runner"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        print("Listening for wake word... Press CTRL+C to stop.")
        # Variable to track whether the message has been sent
        message_sent = False
        last_detection_time = 0
        cooldown_period = 2  # Cooldown period in seconds to avoid duplicate messages

        # Read output line-by-line
        for line in process.stdout:
            # Extract classification results using regex
            match = re.search(r"classifyRes \d+ms\. \{ (.*?) \}", line)
            if match:
                # Parse the classification results
                results = match.group(1)
                classifications = {k: float(v) for k, v in re.findall(r"(\w+): '([\d\.]+)'", results)}
                print("Classification Results:", classifications)

                # Check if `solera` exceeds the threshold
                if classifications.get("solera", 0) > 0.65:
                    current_time = time.time()
                    if not message_sent or (current_time - last_detection_time) > cooldown_period:
                        print("Wake word detected! Publishing to ZMQ...")
                        socket.send_string("1")  # Publish "1" to ZMQ
                        message_sent = True
                        last_detection_time = current_time
                else:
                    # Reset the message_sent flag if `solera` falls below the threshold
                    message_sent = False

    except KeyboardInterrupt:
        print("\nStopping inference...")
    finally:
        # Ensure the subprocess is terminated and ZMQ socket is closed
        process.terminate()
        socket.close()
        context.term()

if __name__ == "__main__":
    run_inference()
