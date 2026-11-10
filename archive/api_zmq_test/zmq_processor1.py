import zmq
import time
import requests
import threading
import re

API_URL = "https://express-agent-kit.onrender.com/api/chat"

# Addresses (adjust as needed)
SUB_ADDRESS = "tcp://127.0.0.1:5555"   # We subscribe to this; another script publishes here.
PUB_ADDRESS = "tcp://127.0.0.1:5556"   # We publish here; another script subscribes to this.

# Shared state for the publisher thread
current_pub_message = ""   # Initially empty
stop_thread = False

def filter_response_text(text):
    """
    Remove brackets, slashes, and other unwanted characters from the API response.
    Adjust this as needed for your specific filtering requirements.
    """
    # Example: remove brackets [] {} () and slashes
    filtered = re.sub(r"[\[\]\(\)\{\}\\\/]", "", text)
    return filtered.strip()

def publisher_thread(pub_socket):
    """
    Continuously publish the current_pub_message every 0.5 seconds.
    """
    global current_pub_message, stop_thread
    while not stop_thread:
        pub_socket.send_string(current_pub_message)
        time.sleep(0.5)  # Publish frequency

def main():
    global current_pub_message, stop_thread

    # Prepare ZeroMQ context
    context = zmq.Context()

    # 1) Create a SUB socket to receive input messages
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect(SUB_ADDRESS)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics

    # 2) Create a PUB socket to publish output
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(PUB_ADDRESS)

    # 3) Start a background thread that continually publishes whatever is in `current_pub_message`
    pub_thread = threading.Thread(target=publisher_thread, args=(pub_socket,), daemon=True)
    pub_thread.start()

    # 4) Use a Session to optimize HTTP connection usage
    session = requests.Session()

    print(f"Started processor. Subscribing to {SUB_ADDRESS}, publishing to {PUB_ADDRESS}.")
    print("Only calling the API if incoming message is not 'NULL'.")
    print("Publishing 'Thinking' during API call, then the final response. Press Ctrl+C to stop.\n")

    try:
        while True:
            # Receive message from the subscription socket
            incoming_msg = sub_socket.recv_string().strip()

            # If the message is "NULL" or empty, do nothing and keep publishing the last known message
            if not incoming_msg or incoming_msg == "NULL":
                continue

            # We got a non-NULL message => Feed it to the API
            print(f"Received message: '{incoming_msg}'. Calling API...")

            # Publish "Thinking" while waiting for the API
            current_pub_message = "Thinking"

            # Prepare payload
            data = {"message": incoming_msg}

            try:
                # Call the API
                start_time = time.time()
                response = session.post(API_URL, json=data, timeout=10)
                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    # Success
                    api_json = response.json()
                    # Convert the entire JSON to a string, or pick a specific field
                    api_text = str(api_json)
                    filtered_text = filter_response_text(api_text)

                    print(f"Raw API Response: {api_text}, Time Taken: {elapsed_time:.2f} seconds")
                    print(f"Filtered Response: {filtered_text}")

                    # Publish the filtered response
                    current_pub_message = filtered_text
                else:
                    # Error in response
                    error_msg = f"Failed to get 200. Status code: {response.status_code}"
                    print(error_msg)
                    # Keep publishing the last known message (whatever that was)
            except requests.exceptions.RequestException as e:
                print(f"API call error: {e}")
                # Keep publishing the last known message (whatever that was)

    except KeyboardInterrupt:
        print("\nShutting down...")

    # Cleanup
    stop_thread = True
    pub_thread.join()
    sub_socket.close()
    pub_socket.close()
    session.close()
    context.term()

if __name__ == "__main__":
    main()
