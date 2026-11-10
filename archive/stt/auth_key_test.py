import requests

# Replace with your actual AssemblyAI API key
auth_key = "YOUR_ASSEMBLYAI_API_KEY"

# URL to test authentication
url = "https://api.assemblyai.com/v2/account"

# Make a GET request to the account endpoint
headers = {"Authorization": auth_key}
response = requests.get(url, headers=headers)

# Check the response
if response.status_code == 200:
    print("Auth key is valid!")
    print("Response:", response.json())
else:
    print("Auth key is invalid or expired.")
    print("Status code:", response.status_code)
    print("Response:", response.text)
