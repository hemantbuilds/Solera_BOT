import zmq
import time
import requests
import re

API_URL = "https://express-agent-kit.onrender.com/api/chat"

# Addresses
SUB_ADDRESS = "tcp://127.0.0.1:5559"   # Subscribe to messages
PUB_ADDRESS = "tcp://127.0.0.1:5560"   # Publish to this address

def filter_response_text(text):
    """Clean up text to remove unwanted characters."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"[^\w\s\.,!\?\-]", "", text)
    return text.strip()

def main():
    context = zmq.Context()

    # Create a SUB socket to receive input messages
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect(SUB_ADDRESS)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics

    # Create a PUB socket to publish output
    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect(PUB_ADDRESS)

    session = requests.Session()

    print(f"Subscribed to {SUB_ADDRESS}, publishing to {PUB_ADDRESS}.")

    try:
        while True:
            incoming_msg = sub_socket.recv_string().strip()
            if not incoming_msg:
                continue

            print(f"Received: {incoming_msg}")
            pub_socket.send_string("Thinking")  # Publish "Thinking" immediately

            # Send to API
            data = {"message": incoming_msg}
            try:
                start_time = time.time()
                response = session.post(API_URL, json=data, timeout=10)
                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    api_text = response.json().get('response', 'No response received.')
                    filtered_text = filter_response_text(api_text)
                    print(f"API Response: {filtered_text}, Time: {elapsed_time:.2f}s")

                    # Publish final response
                    pub_socket.send_string(filtered_text)
                else:
                    print(f"Error: Status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"API Error: {e}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        sub_socket.close()
        pub_socket.close()
        session.close()
        context.term()

if __name__ == "__main__":
    main()
