import zmq
from gtts import gTTS
from io import BytesIO
from pygame import mixer
import threading
import queue
import os

# Initialize pygame mixer
mixer.init()

# Initialize ZMQ subscriber
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5556")
socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

# Thread-safe queue to hold incoming messages
message_queue = queue.Queue()

def zmq_listener():
    """Listens for messages on the ZMQ socket and adds them to the queue."""
    while True:
        message = socket.recv_string()  # Blocking call, waits for a message
        message_queue.put(message)  # Add message to the queue

def toggle_mic(state):
    """Enable or disable the microphone."""
    if state == "disable":
        os.system("amixer set Capture nocap")  # Disable mic
    elif state == "enable":
        os.system("amixer set Capture cap")  # Enable mic

def process_messages():
    """Processes messages from the queue and plays them using Google TTS."""
    while True:
        message = message_queue.get()  # Blocking call, waits for a message in the queue
        print(f"Received message: {message}")

        # Remove "response" at the start of the message
        if message.lower().startswith("response"):
            message = message[len("response"):].strip()

        print(f"Processing message: {message}")

        # Generate TTS audio from the message
        mp3audio = BytesIO()
        tts = gTTS(message, lang='en', tld='us')
        tts.write_to_fp(mp3audio)
        mp3audio.seek(0)

        # Disable the microphone before playing the audio
        toggle_mic("disable")

        # Play the audio
        mixer.music.load(mp3audio, "mp3")
        mixer.music.play()

        # Wait for the current audio to finish playing
        while mixer.music.get_busy():
            pass

        # Re-enable the microphone after the audio finishes playing
        toggle_mic("enable")

# Start the ZMQ listener in a separate thread
listener_thread = threading.Thread(target=zmq_listener, daemon=True)
listener_thread.start()

# Process messages in the main thread
process_messages()
