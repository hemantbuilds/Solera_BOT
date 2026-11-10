import zmq
import requests
import time

# Define ZMQ IPs and Ports
PUBLISHER_IP = "tcp://127.0.0.1:5555"  # Publisher for input messages
SUBSCRIBER_IP = "tcp://127.0.0.1:5556"  # Subscriber for API output

# API Endpoint
API_URL = "https://express-agent-kit.onrender.com/api/chat"  # Replace with your hosted API endpoint

def publisher():
    """
    ZMQ Publisher: Publishes a message to the defined ZMQ topic.
    """
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(PUBLISHER_IP)
    time.sleep(1)  # Allow subscribers to connect
    
    # Input message to send
    message = input("Enter your message to send to the API: ")
    print(f"Publishing message: {message}")
    socket.send_string(message)
    time.sleep(1)  # Ensure the message is sent
    socket.close()

def subscriber_and_call_api():
    """
    ZMQ Subscriber: Subscribes to the published input, sends it to the API, 
    and republishes the API response.
    """
    # ZMQ Subscriber for input
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(PUBLISHER_IP)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    print("Waiting for input message...")
    message = socket.recv_string()  # Blocking call
    print(f"Received message from publisher: {message}")

    # Send message to the API
    api_payload = {"message": message}
    try:
        print("Sending message to the API...")
        response = requests.post(API_URL, json=api_payload)
        response_data = response.json()
        print(f"API Response: {response_data}")
    except Exception as e:
        print(f"Error while calling API: {e}")
        response_data = {"error": str(e)}

    # ZMQ Publisher for API response
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(SUBSCRIBER_IP)
    time.sleep(1)  # Allow subscribers to connect

    # Publish the API response
    response_message = str(response_data)
    print(f"Publishing API response: {response_message}")
    pub_socket.send_string(response_message)
    time.sleep(1)  # Ensure the message is sent

    socket.close()
    pub_socket.close()

def response_subscriber():
    """
    ZMQ Subscriber: Subscribes to the API output and prints it.
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(SUBSCRIBER_IP)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    print("Waiting for API response...")
    response = socket.recv_string()  # Blocking call
    print(f"Received API Response: {response}")
    socket.close()

if __name__ == "__main__":
    # Run the functions in sequence
    print("Starting Publisher...")
    publisher()

    print("\nStarting Subscriber and API Caller...")
    subscriber_and_call_api()

    print("\nStarting Response Subscriber...")
    response_subscriber()
