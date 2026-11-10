import zmq
from gtts import gTTS
from io import BytesIO
from pygame import mixer
import threading
import queue
import asyncio

# Initialize pygame mixer
mixer.init()

# Initialize ZMQ subscriber
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://127.0.0.1:5556")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

# Initialize ZMQ publisher for "Finished" message
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5569")
print("Publishing 'Finished' messages to tcp://127.0.0.1:5569")

# Thread-safe queue to hold incoming messages
message_queue = queue.Queue()

def zmq_listener():
    """Listens for messages on the ZMQ socket and adds them to the queue."""
    while True:
        message = sub_socket.recv_string()  # Blocking call, waits for a message
        message_queue.put(message)  # Add message to the queue

def split_message_into_chunks(message, chunk_size=20):
    """Split a message into chunks of a specified word size."""
    words = message.split()
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

async def generate_audio(chunk, index):
    """Generate audio for a given text chunk."""
    try:
        tts = gTTS(chunk, lang='en', tld='us')
        mp3audio = BytesIO()
        tts.write_to_fp(mp3audio)
        mp3audio.seek(0)
        return mp3audio
    except Exception as e:
        print(f"Error generating TTS for chunk_{index}: {e}")
        return None

async def play_audio(audio, index):
    """Play the audio chunk."""
    try:
        print(f"Playing chunk_{index}...")
        mixer.music.load(audio, "mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)  # Allow other coroutines to run
        print(f"Finished playing chunk_{index}.")
    except Exception as e:
        print(f"Error playing chunk_{index}: {e}")

async def process_message(message):
    """Process a single message by generating and playing TTS for each chunk."""
    print(f"Processing message: {message}")

    # Remove "response" at the start of the message
    if message.lower().startswith("response"):
        message = message[len("response"):].strip()

    # Split message into chunks
    chunks = split_message_into_chunks(message)

    # Generate and play TTS for each chunk sequentially
    for index, chunk in enumerate(chunks):
        audio = await generate_audio(chunk, index)
        if audio:
            await play_audio(audio, index)

    # Publish "Finished" message once all chunks are played
    pub_socket.send_string("Finished")
    print("Published: Finished")

async def process_messages():
    """Processes messages from the queue."""
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, message_queue.get)  # Wait for a message
        await process_message(message)

# Start the ZMQ listener in a separate thread
listener_thread = threading.Thread(target=zmq_listener, daemon=True)
listener_thread.start()

# Run the asyncio event loop to process messages
asyncio.run(process_messages())
