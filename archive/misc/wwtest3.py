import zmq
import subprocess
import re

# Initialize ZeroMQ
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)

# Connect to the PUB socket on tcp://127.0.0.1:5560
sub_socket.connect("tcp://127.0.0.1:5560")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
print("Listening for START and STOP signals on tcp://127.0.0.1:5560")

# Function to find an available mic other than card 4
def get_available_mic():
    try:
        output = subprocess.check_output(["arecord", "-l"], text=True)
        devices = re.findall(r"card (\d+):.*?device (\d+):.*?USB Audio", output)
        for card, device in devices:
            if card != "4":  # Exclude card 4
                print(f"Using microphone on card {card}, device {device}")
                return card
    except Exception as e:
        print(f"Error finding available microphone: {e}")
    return None

# Get the available microphone
MIC_CARD = get_available_mic()
MIC_CONTROL = "Capture"  # Control name for the microphone

if not MIC_CARD:
    print("No suitable microphone found. Exiting...")
    exit(1)

def mute_mic():
    """Mute the microphone on the specified card."""
    try:
        subprocess.run(
            ["amixer", "-c", MIC_CARD, "set", MIC_CONTROL, "nocap"], check=True
        )
        print("Microphone muted.")
    except subprocess.CalledProcessError as e:
        print(f"Error muting microphone: {e}")
    except Exception as e:
        print(f"Unexpected error muting microphone: {e}")

def unmute_mic():
    """Unmute the microphone on the specified card."""
    try:
        subprocess.run(
            ["amixer", "-c", MIC_CARD, "set", MIC_CONTROL, "cap"], check=True
        )
        subprocess.run(
            ["amixer", "-c", MIC_CARD, "set", MIC_CONTROL", "99%"], check=True
        )
        print("Microphone unmuted.")
    except subprocess.CalledProcessError as e:
        print(f"Error unmuting microphone: {e}")
    except Exception as e:
        print(f"Unexpected error unmuting microphone: {e}")

# Start with the microphone muted
mute_mic()

try:
    while True:
        # Wait for a message
        message = sub_socket.recv_string()
        if message.strip() == "START":
            print("Received START signal. Unmuting microphone...")
            unmute_mic()
        elif message.strip() == "STOP":
            print("Received STOP signal. Muting microphone...")
            mute_mic()
        else:
            print(f"Received unknown signal: {message}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    # Ensure the microphone is muted on exit
    mute_mic()
    sub_socket.close()
    context.term()
