import pyaudio
import websockets
import asyncio
import base64
import json
import zmq
import argparse

# AssemblyAI API key
auth_key = 'YOUR_ASSEMBLYAI_API_KEY'

# Audio recording parameters
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Ensure this matches your microphone's capabilities
RATE = 16000

# Argument parser for dynamic microphone selection
parser = argparse.ArgumentParser(description="Transcription Script with Persistent WebSocket")
parser.add_argument("--device", type=int, default=None, help="Audio input device index (default: system default)")
args = parser.parse_args()

p = pyaudio.PyAudio()

# List available audio devices
if args.device is None:
    print("Available audio devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"Index {i}: {dev['name']}")

# Use the default device or the specified device
device_index = args.device

# Starts recording
try:
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAMES_PER_BUFFER
    )
except IOError as e:
    print(f"Error opening microphone device. Details: {e}")
    exit(1)

# The AssemblyAI endpoint
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Initialize ZeroMQ
context = zmq.Context()

# ZMQ PUB socket to publish results
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5559")
print("Publishing transcription results to tcp://127.0.0.1:5559")

# ZMQ SUB socket to receive control signals
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://127.0.0.1:5560")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print("Listening for transcription control signals on tcp://127.0.0.1:5560")

# Control flag for transcription
transcription_active = False

async def send_receive():
    """
    Maintains a persistent WebSocket connection and handles audio streaming dynamically.
    """
    global transcription_active
    print(f"Connecting to WebSocket at {URL}")
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        print("WebSocket connection established.")

        # Receive Session Begins message
        await _ws.recv()

        async def send_audio():
            """Sends audio data to the WebSocket when transcription is active."""
            while True:
                if transcription_active:
                    try:
                        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data": str(data)})
                        await _ws.send(json_data)
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                        transcription_active = False
                        break
                await asyncio.sleep(0.01)

        async def receive_transcription():
            """Receives transcription results from the WebSocket."""
            while True:
                try:
                    result_str = await _ws.recv()
                    data = json.loads(result_str)

                    # Publish final transcription
                    if 'message_type' in data and data['message_type'] == 'FinalTranscript':
                        final_text = data['text']
                        print(f"Final transcription: {final_text}")
                        pub_socket.send_string(final_text)
                except Exception as e:
                    print(f"Error receiving transcription: {e}")
                    break

        # Run send and receive tasks concurrently
        await asyncio.gather(send_audio(), receive_transcription())

async def control_listener():
    """
    Listens for START/STOP signals to toggle transcription.
    """
    global transcription_active
    while True:
        try:
            message = sub_socket.recv_string()
            if message == "START":
                if not transcription_active:
                    print("Received START signal. Enabling transcription...")
                    transcription_active = True
            elif message == "STOP":
                if transcription_active:
                    print("Received STOP signal. Disabling transcription...")
                    transcription_active = False
        except Exception as e:
            print(f"Error in control listener: {e}")

async def main():
    """
    Main function to run the control listener and persistent WebSocket connection concurrently.
    """
    await asyncio.gather(
        control_listener(),
        send_receive()
    )

# Run the event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nStopping transcription...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Clean-up completed.")
