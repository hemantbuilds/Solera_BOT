import zmq
import subprocess

# Initialize ZeroMQ
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)

# Connect to the PUB socket on tcp://127.0.0.1:5560
sub_socket.connect("tcp://127.0.0.1:5560")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
print("Listening for START and STOP signals on tcp://127.0.0.1:5560")

# Microphone control commands
MIC_CARD = "4"  # Card number for the microphone
#MIC_CARD1 = "1"
MIC_CONTROL = "Mic"  # Control name

def mute_mic():
    """Mute the microphone."""
    try:
        subprocess.run(["amixer", "-c", MIC_CARD, "set", MIC_CONTROL, "uncap"], check=True)
        print("Microphone muted.")
        #subprocess.run(["amixer", "-c", MIC_CARD1, "set", MIC_CONTROL, "nocap"], ch>        print("Microphone muted.")
    except Exception as e:
        print(f"Error muting microphone: {e}")

def unmute_mic():
    """Unmute the microphone."""
    try:
        subprocess.run(["amixer", "-c", MIC_CARD, "set", MIC_CONTROL, "99%"], check=True)
        print("Microphone unmuted.")
        #subprocess.run(["amixer", "-c", MIC_CARD1, "set", MIC_CONTROL, "cap"], chec>        print("Microphone unmuted.")
    except Exception as e:
        print(f"Error unmuting microphone: {e}")

# Start with the microphone muted
mute_mic()

try:
    while True:
        # Wait for a message
        message = sub_socket.recv_string()
        if message == "START":
            print("Received START signal. Unmuting microphone...")
            unmute_mic()
        elif message == "STOP":
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
