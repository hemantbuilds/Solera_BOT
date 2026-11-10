import pyaudio
import websockets
import asyncio
import base64
import json
import zmq
import time

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
pub_socket = context.socket(zmq.PUB)  # PUB socket to publish the final message
zmq_ip = "tcp://127.0.0.1:5557"  # ZMQ server IP and port
pub_socket.bind(zmq_ip)
#pub_socket.connect(zmq_ip)
print(f"Publishing final transcriptions to ZMQ server at {zmq_ip}")

time.sleep(1)   # add a small delay  zmq ko saans lene k liye 
async def send_receive():
    print(f"Connecting to WebSocket at {URL}")
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

        async def send():
            """Send audio data to the WebSocket."""
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while sending audio: {e}")
                    break
                await asyncio.sleep(0.01)

        async def receive():
            """Receive transcription results from the WebSocket."""
            while True:
                try:
                    result_str = await _ws.recv()
                    data = json.loads(result_str)

                    # Publish only the final transcription
                    if 'message_type' in data and data['message_type'] == 'FinalTranscript':
                        final_text = data['text']
                        print(f"Final transcription: {final_text}")
                        pub_socket.send_string(final_text)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while receiving transcription: {e}")
                    break

        # Run send and receive tasks concurrently
        await asyncio.gather(send(), receive())

# Run the event loop
try:
    asyncio.run(send_receive())
except KeyboardInterrupt:
    print("\nStopping transcription...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Clean-up completed.")
