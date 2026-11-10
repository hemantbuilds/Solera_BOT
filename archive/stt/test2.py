import pyaudio
import websockets
import asyncio
import base64
import json

# Replace with your AssemblyAI API key
auth_key = "YOUR_ASSEMBLYAI_API_KEY"

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MICROPHONE_INDEX = 3  # Adjust based on `arecord -l` output
p = pyaudio.PyAudio()

# Open audio stream
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=MICROPHONE_INDEX,
    frames_per_buffer=FRAMES_PER_BUFFER
)

# AssemblyAI WebSocket URL
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"


async def send_receive():
    async with websockets.connect(
        URL,
        headers={"Authorization": auth_key},
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)

        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(f"SessionBegins: {session_begins}")

        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    audio_data = base64.b64encode(data).decode("utf-8")
                    await _ws.send(json.dumps({"audio_data": audio_data}))
                except Exception as e:
                    print(f"Error while sending audio: {e}")
                    break

        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    response = json.loads(result_str)
                    transcription = response.get("text", "")
                    if transcription:
                        print(f"Transcription: {transcription}")
                except Exception as e:
                    print(f"Error while receiving response: {e}")
                    break

        await asyncio.gather(send(), receive())


# Run the WebSocket client
asyncio.run(send_receive())
