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
async def transcribe_audio():
    """
    Connects to AssemblyAI WebSocket and starts transcription upon receiving a START signal.
    Stops transcription when a final response is received.
    """
    global stream  # Ensure stream is accessible across functions

    print("Waiting for START signal...")
    while True:
        try:
            message = sub_socket.recv_string()
            if message.strip() == "START":
                print("Received START signal. Connecting to WebSocket and starting transcription...")
                await start_transcription()
        except Exception as e:
            print(f"ZMQ Error: {e}")

async def start_transcription():
    """
    Starts the WebSocket connection with AssemblyAI and streams audio until a final response is received.
    """
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", AUTH_KEY),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER
        )

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

                        print("Stopping transcription and waiting for next START signal...")
                        return  # Exit loop to wait for next START signal
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"WebSocket closed: {e}")
                    break
                except Exception as e:
                    print(f"Error while receiving transcription: {e}")
                    break

        # Run send and receive tasks concurrently
        await asyncio.gather(send(), receive())

        # Close stream and wait for next START signal
        stream.stop_stream()
        stream.close()
        print("Audio stream closed. Waiting for the next START signal...\n")

# ---------------------- MAIN EXECUTION ---------------------- #
if __name__ == "__main__":
    try:
        asyncio.run(transcribe_audio())  # Runs indefinitely, waiting for START
    except KeyboardInterrupt:
        print("\nStopping transcription service...")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("Clean-up completed.")
