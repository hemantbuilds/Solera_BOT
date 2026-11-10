import pyaudio
import websockets
import asyncio
import base64
import json
import zmq

# AssemblyAI API key
auth_key = 'YOUR_ASSEMBLYAI_API_KEY'

# Audio recording parameters
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

# Starts recording
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)

# The AssemblyAI endpoint
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Initialize ZeroMQ
context = zmq.Context()

# Socket for sending transcripts from AssemblyAI
send_socket = context.socket(zmq.PUSH)
#send_socket.bind("tcp://127.0.0.1:5555")
send_socket.connect("tcp://127.0.0.1:5555")
print("Publishing transcription to tcp://127.0.0.1:5555")

# Socket for receiving messages and publishing final messages
receive_socket = context.socket(zmq.PULL)
receive_socket.connect("tcp://127.0.0.1:5555")
final_publish_socket = context.socket(zmq.PUB)
#final_publish_socket.bind("tcp://127.0.0.1:5559")
final_publish_socket.connect("tcp://127.0.0.1:5559")
print("Publishing final messages to tcp://127.0.0.1:5559")


async def send_receive():
    print(f'Connecting websocket to URL {URL}')
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)

        # Function to send audio data
        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except Exception as e:
                    print(f"Error while sending: {e}")
                    break
                await asyncio.sleep(0.01)

        # Function to receive and process transcripts
        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    data = json.loads(result_str)
                    if 'text' in data:
                        text = data['text']
                        print(f"Transcription: {text}")
                        send_socket.send_string(text)
                except Exception as e:
                    print(f"Error while receiving: {e}")
                    break

        await asyncio.gather(send(), receive())


def process_final_messages():
    """Receive messages from tcp://127.0.0.1:5555 and publish the final message to tcp://127.0.0.1:5559."""
    print("Processing messages for final output...")
    last_message = None

    while True:
        try:
            message = receive_socket.recv_string()
            if message.strip():
                last_message = message
            else:
                if last_message:
                    print(f"Final message: {last_message}")
                    final_publish_socket.send_string(last_message)
                    last_message = None
        except Exception as e:
            print(f"Error processing messages: {e}")


# Run both functions concurrently
async def main():
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, process_final_messages),
        send_receive()
    ]
    await asyncio.gather(*tasks)


asyncio.run(main())
