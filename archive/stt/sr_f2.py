import pyaudio
import websockets
import asyncio
import base64
import json
import zmq
import time

# ---------------------- CONFIGURATION ---------------------- #
AUTH_KEY = 'YOUR_ASSEMBLYAI_API_KEY'  # AssemblyAI API key
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Audio recording parameters
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

# ZMQ Configuration
SUB_IP = "tcp://127.0.0.1:5560"  # Subscribes to START/STOP signals
PUB_IP = "tcp://127.0.0.1:5557"  # Publishes final transcriptions

# Initialize ZMQ Subscriber for START/STOP
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect(SUB_IP)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(f"Listening for START signals on {SUB_IP}")

# Initialize ZMQ Publisher for transcriptions
pub_socket = context.socket(zmq.PUB)
pub_socket.bind(PUB_IP)
print(f"Publishing final transcriptions on {PUB_IP}")

# ---------------------- FUNCTIONS ---------------------- #
async def handle_transcription():
    """
    Keeps the WebSocket session active by sending silent audio and transcribes only when START is received.
    """
    while True:  # Infinite loop to retry connection
        try:
            async with websockets.connect(
                URL,
                extra_headers=(("Authorization", AUTH_KEY),),
                ping_interval=5,
                ping_timeout=20
            ) as _ws:
                await asyncio.sleep(0.1)
                print("✅ WebSocket session established. Waiting for START signal...")

                session_begins = await _ws.recv()
                print(session_begins)  # Log session start

                # Create the PyAudio stream but keep it inactive initially
                stream = p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=FRAMES_PER_BUFFER
                )

                transcription_active = False  # Track if transcription is running

                while True:
                    message = sub_socket.recv_string()
                    
                    if message.strip() == "START":
                        if not transcription_active:
                            print("▶️ Received START signal. Beginning transcription...")
                            transcription_active = True
                        await transcribe_audio(_ws, stream, transcription_active)  # Start transcribing
                    
                    elif message.strip() == "STOP":
                        if transcription_active:
                            print("⏸ Received STOP signal. Pausing transcription...")
                            transcription_active = False

        except (OSError, websockets.exceptions.ConnectionClosedError) as e:
            print(f"⚠️ WebSocket Connection Failed: {e}")
            print("🔄 Retrying connection in 5 seconds...")
            await asyncio.sleep(5)  # Wait before reconnecting

async def transcribe_audio(_ws, stream, transcription_active):
    """
    Streams audio to AssemblyAI while transcription is active and keeps session alive when idle.
    """
    try:
        async def send():
            """Continuously sends audio (real audio if START, silence otherwise)."""
            while True:
                try:
                    if transcription_active:
                        # Capture real microphone data
                        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    else:
                        # Send silent audio to keep session alive
                        data = b'\x00' * FRAMES_PER_BUFFER  # Silent audio (zero bytes)

                    encoded_data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(encoded_data)})
                    await _ws.send(json_data)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while sending audio: {e}")
                    break

                await asyncio.sleep(0.01)

        async def receive():
            """Receives and publishes transcription results."""
            while True:
                try:
                    result_str = await _ws.recv()
                    data = json.loads(result_str)

                    if 'message_type' in data and data['message_type'] == 'FinalTranscript':
                        final_text = data['text']
                        print(f"📝 Final transcription: {final_text}")
                        pub_socket.send_string(final_text)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while receiving transcription: {e}")
                    break

        # Run send and receive concurrently
        await asyncio.gather(send(), receive())

    except Exception as e:
        print(f"Error in transcription loop: {e}")

# ---------------------- MAIN EXECUTION ---------------------- #
if __name__ == "__main__":
    try:
        asyncio.run(handle_transcription())  # Runs indefinitely
    except KeyboardInterrupt:
        print("\n🛑 Stopping transcription service...")
    finally:
        p.terminate()
        print("✅ Clean-up completed.")
