import time
import requests

# Define the API endpoint
url = "https://express-agent-kit.onrender.com/api/chat"  # Replace with your actual API URL

# Get message input from the user
message = input("Enter your message: ")

# Define the payload (data to be sent to the API)
data = {
    "message": message  # Adjust the key as per your API's expected format
}

# Use a session to optimize connection handling
with requests.Session() as session:
    try:
        # Measure the time taken to send the request and get the response
        start_time = time.time()
        response = session.post(url, json=data, timeout=10)  # Set a timeout to avoid indefinite waiting
        elapsed_time = time.time() - start_time
        
        # Check if the request was successful
        if response.status_code == 200:
            # Print the API response and time taken
            print(f"API Response: {response.json()}, Time Taken: {elapsed_time:.2f} seconds")
        else:
            print(f"Failed to get a response. Status code: {response.status_code}, Time Taken: {elapsed_time:.2f} seconds")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
