
import pyaudio
import websockets
import asyncio
import base64
import json

# Replace with your actual AssemblyAI API key
auth_key = "YOUR_ASSEMBLYAI_API_KEY"

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Updated to match the microphone's specification
RATE = 48000  # Using standard sample rate for speech recognition
MICROPHONE_INDEX = 3  # Update to the correct index of your microphone
p = pyaudio.PyAudio()

# Start recording
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=MICROPHONE_INDEX,
    frames_per_buffer=FRAMES_PER_BUFFER
)

# The AssemblyAI endpoint
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

async def send_receive():
    print(f"Connecting to websocket at {URL}")
    async with websockets.connect(
        URL,
        extra_headers={"Authorization": auth_key},
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(f"SessionBegins Response: {session_begins}")
        print("Sending audio data ...")

        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    print(f"Sending audio data: {len(data)} bytes")  # Debugging log
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket connection closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while sending audio data: {e}")
                    break
                await asyncio.sleep(0.01)
            return True

        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    print(f"Received data: {result_str}")  # Debugging log
                    print(json.loads(result_str).get('text', ''))
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket connection closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while receiving data: {e}")
                    break

        await asyncio.gather(send(), receive())


# Run the async function
asyncio.run(send_receive())
