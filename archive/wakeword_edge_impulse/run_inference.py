import subprocess
import re

def run_inference():
    # Start edge-impulse-linux-runner as a subprocess
    process = subprocess.Popen(
        ["edge-impulse-linux-runner"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        print("Listening for wake word... Press CTRL+C to stop.")
        # Read output line-by-line
        for line in process.stdout:
            # Extract classification results using regex
            match = re.search(r"classifyRes \d+ms\. \{ (.*?) \}", line)
            if match:
                # Parse the classification results
                results = match.group(1)
                classifications = {k: float(v) for k, v in re.findall(r"(\w+): '([\d\.]+)'", results)}
                print("Classification Results:", classifications)

                # Perform actions based on classification
                if classifications.get("solera", 0) > 0.5:  # Example: Threshold for `solera`
                    print("Wake word detected!")
                    # Add additional actions here, like triggering a response or sending a signal

    except KeyboardInterrupt:
        print("\nStopping inference...")
    finally:
        # Ensure the subprocess is terminated
        process.terminate()

if __name__ == "__main__":
    run_inference()
