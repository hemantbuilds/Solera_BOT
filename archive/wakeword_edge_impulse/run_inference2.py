import subprocess
import re
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

# ZMQ Configuration
ZMQ_IP = "tcp://127.0.0.1:5559"

# PyAudio setup
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)

def monitor_solera(wake_signal, cooldown_period=2):
    """
    Monitor the solera value using Edge Impulse runner and send signal when wake word is detected.
    """
    process = subprocess.Popen(
        ["edge-impulse-linux-runner"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        print("Monitoring solera value... Press CTRL+C to stop.")
        last_trigger_time = 0  # Track the time of the last trigger
        for line in process.stdout:
            # Extract classification results using regex
            match = re.search(r"classifyRes \d+ms\. \{ (.*?) \}", line)
            if match:
                # Parse the classification results
                results = match.group(1)
                classifications = {k: float(v) for k, v in re.findall(r"(\w+): '([\d\.]+)'", results)}
                print("Classification Results:", classifications)

                # Check if `solera` exceeds the threshold
                if classifications.get("solera", 0) > 0.65:
                    current_time = time.time()
                    # Ensure at least `cooldown_period` seconds have passed since the last trigger
                    if current_time - last_trigger_time > cooldown_period:
                        print("Wake word detected! Signaling to start transcription...")
                        wake_signal.append(True)  # Add a signal to the list
                        last_trigger_time = current_time
    except KeyboardInterrupt:
        print("\nStopping solera monitoring...")
    finally:
        process.terminate()

async def transcribe_and_publish(wake_signal):
    """
    Transcribe audio and publish final transcription to ZMQ IP when wake word is detected.
    """
    # Initialize ZMQ socket
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(ZMQ_IP)
    print(f"Connected to ZMQ server at {ZMQ_IP}")

    while True:
        # Wait for a wake word signal
        if not wake_signal:
            await asyncio.sleep(0.1)  # Check periodically for a signal
            continue

        # Consume the wake signal
        wake_signal.pop(0)

        print("Wake word signal received. Starting transcription in 200ms...")
        await asyncio.sleep(0.2)  # Delay of 200ms

        # Start transcription
        while True:
            try:
                async with websockets.connect(
                    "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000",
                    extra_headers=(("Authorization", auth_key),),
                    ping_interval=5,
                    ping_timeout=20
                ) as _ws:
                    print("WebSocket connection established with AssemblyAI.")
                    await asyncio.sleep(0.1)
                    await _ws.recv()  # Receive session begins

                    async def send_audio():
                        """Send audio data to the WebSocket."""
                        while True:
                            try:
                                data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                                data = base64.b64encode(data).decode("utf-8")
                                json_data = json.dumps({"audio_data": str(data)})
                                await _ws.send(json_data)
                            except Exception as e:
                                print(f"Error while sending audio: {e}")
                                break
                            await asyncio.sleep(0.01)

                    async def receive_transcription():
                        """Receive transcription results from the WebSocket."""
                        while True:
                            try:
                                result_str = await _ws.recv()
                                data = json.loads(result_str)
                                # Check if the message is a final transcription
                                if 'message_type' in data and data['message_type'] == 'FinalTranscript':
                                    final_text = data['text']
                                    print(f"Final transcription: {final_text}")
                                    socket.send_string(final_text)  # Publish final message to ZMQ
                                    return  # Stop transcription after final message
                            except Exception as e:
                                print(f"Error while receiving transcription: {e}")
                                break

                    # Run send and receive tasks concurrently
                    await asyncio.gather(send_audio(), receive_transcription())
                break  # Exit while loop if transcription completes successfully
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"WebSocket closed: {e}. Retrying...")
                await asyncio.sleep(1)  # Retry after a delay
            except Exception as e:
                print(f"Unexpected error: {e}. Retrying...")
                await asyncio.sleep(1)  # Retry after a delay

if __name__ == "__main__":
    # Shared wake signal list for communication between threads
    wake_signal = []

    # Start solera monitoring in a separate thread
    from threading import Thread
    solera_thread = Thread(target=monitor_solera, args=(wake_signal,))
    solera_thread.daemon = True
    solera_thread.start()

    # Run the transcription and publishing loop
    try:
        asyncio.run(transcribe_and_publish(wake_signal))
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Clean-up completed.")
