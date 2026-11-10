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

# Socket for sending transcripts to tcp://127.0.0.1:5555
send_socket = context.socket(zmq.PUSH)
send_socket.connect("tcp://127.0.0.1:5555")  # Change from `bind` to `connect`
print("Connected to tcp://127.0.0.1:5555 for transcription publishing.")

# Socket for receiving control messages
control_socket = context.socket(zmq.SUB)
control_socket.connect("tcp://127.0.0.1:5560")
control_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

# Socket for publishing final messages to tcp://127.0.0.1:5559
publish_socket = context.socket(zmq.PUB)
publish_socket.connect("tcp://127.0.0.1:5559")  # Change from `bind` to `connect`
print("Connected to tcp://127.0.0.1:5559 for final message publishing.")

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

        active_control_message = None

        async def control_listener():
            """Listen for control messages and store the latest."""
            nonlocal active_control_message
            while True:
                try:
                    message = control_socket.recv_string(flags=zmq.NOBLOCK)
                    print(f"Received control message: {message}")
                    active_control_message = message
                except zmq.Again:
                    await asyncio.sleep(0.1)

        async def send():
            """Send audio data to the AssemblyAI WebSocket."""
            while True:
                if not active_control_message:
                    await asyncio.sleep(0.1)
                    continue  # Skip if there's no active control message

                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except Exception as e:
                    print(f"Error while sending: {e}")
                    break
                await asyncio.sleep(0.01)

        async def receive():
            """Receive and process transcripts."""
            last_message = None
            while True:
                try:
                    result_str = await _ws.recv()
                    data = json.loads(result_str)
                    if 'text' in data:
                        text = data['text']
                        print(f"Transcription: {text}")
                        last_message = text
                except Exception as e:
                    print(f"Error while receiving: {e}")
                    break

                # Publish only the final message when transcription ends
                if last_message and active_control_message:
                    final_message = f"{active_control_message} {last_message}"
                    print(f"Publishing final message: {final_message}")
                    publish_socket.send_string(final_message)
                    last_message = None

        await asyncio.gather(control_listener(), send(), receive())


async def main():
    await send_receive()


asyncio.run(main())
