import zmq
from gtts import gTTS
from io import BytesIO
from pygame import mixer
import threading
import queue

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

def process_messages():
    """Processes messages from the queue and plays them using Google TTS."""
    while True:
        message = message_queue.get()  # Blocking call, waits for a message in the queue
        print(f"Processing message: {message}")

        # Generate TTS audio from the message
        mp3audio = BytesIO()
        tts = gTTS(message, lang='en', tld='us')
        tts.write_to_fp(mp3audio)
        mp3audio.seek(0)

        # Play the audio
        mixer.music.load(mp3audio, "mp3")
        mixer.music.play()

        # Wait for the current audio to finish playing
        while mixer.music.get_busy():
            pass

# Start the ZMQ listener in a separate thread
listener_thread = threading.Thread(target=zmq_listener, daemon=True)
listener_thread.start()

# Process messages in the main thread
process_messages()
