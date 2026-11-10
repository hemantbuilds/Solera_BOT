import zmq
import requests

def subscribe_and_process():
    # Create a ZeroMQ context and subscriber socket
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    # Connect to the publisher's IP
    subscriber.connect("tcp://127.0.0.1:5555")  # Publisher IP
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    # Create a ZeroMQ publisher socket for the response
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5556")  # Response Publisher IP

    print("Waiting for messages...")
    while True:
        # Receive the published message
        received_message = subscriber.recv_string()
        print(f"Received message: {received_message}")

        # Make an API call with the received message
        api_url = "https://express-agent-kit.onrender.com/api/chat"  # Solana API
        payload = {"message": received_message}

        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                api_response = response.json()
                print(f"API Response: {api_response}")

                # Publish the API response
                publisher.send_string(str(api_response))
            else:
                print(f"Error: Received status code {response.status_code}")
        except Exception as e:
            print(f"Error while calling API: {e}")

if __name__ == "__main__":
    subscribe_and_process()
