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

# 🔹 PUB socket to send transcriptions
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5557")  # Publishing transcriptions
print("✅ Publishing transcriptions to ZMQ server at tcp://127.0.0.1:5557")

# 🔹 SUB socket to receive START/STOP commands
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://127.0.0.1:5560")  # Subscribing to ZMQ control
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
print("📡 Listening for ZMQ commands on tcp://127.0.0.1:5560")

async def send_receive():
    """Handles audio transmission and receives ZMQ control messages dynamically."""
    while True:  # 🔥 Always reconnect on WebSocket timeout
        try:
            print(f"🌐 Connecting to WebSocket at {URL}")
            async with websockets.connect(
                URL,
                extra_headers=(("Authorization", auth_key),),
                ping_interval=5,
                ping_timeout=20
            ) as _wss:
                await asyncio.sleep(0.1)
                print("🎧 Receiving SessionBegins ...")
                session_begins = await _ws.recv()
                print(session_begins)

                async def send():
                    """Sends audio data only when transcription_active is True."""
                    print("⏳ Waiting for first ZMQ START/STOP message...")
                    transcription_active = False  # ✅ Start with transcription OFF

                    while True:
                        try:
                            # 🔹 Check for new ZMQ messages dynamically
                            try:
                                message = sub_socket.recv_string(flags=zmq.NOBLOCK).strip().upper()
                                print(f"📩 Received ZMQ Command: {message}")

                                if message == "START":
                                    transcription_active = True
                                    print("✅ Transcription STARTED: Clearing previous audio buffer!")
                                    stream.stop_stream()  # Stop and restart to clear any buffered audio
                                    stream.start_stream()

                                elif message == "STOP":
                                    transcription_active = False
                                    print("🛑 Transcription STOPPED: Audio transmission paused.")

                            except zmq.Again:
                                pass  # No new ZMQ messages, continue execution

                            if transcription_active:
                                # 🔹 Capture and send fresh audio only when START signal is active
                                data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                                data = base64.b64encode(data).decode("utf-8")
                                json_data = json.dumps({"audio_data": str(data)})
                                await _ws.send(json_data)

                                print(f"🎤 Audio Sent: {json_data[:50]}...")  # Debugging
                            else:
                                print("⏸️ Transcription Paused. No audio is being sent.")

                        except websockets.exceptions.ConnectionClosedError as e:
                            print(f"⚠️ WebSocket closed while sending audio: {e}")
                            break
                        except Exception as e:
                            print(f"🚨 Error while sending audio: {e}")
                            break

                        await asyncio.sleep(0.01)

                async def receive():
                    """Receives transcription results from the WebSocket."""
                    while True:
                        try:
                            result_str = await _wss.recv()
                            data = json.loads(result_str)

                            # Publish only the final transcription
                            if 'message_type' in data and data['message_type'] == 'FinalTranscript':
                                final_text = data['text']
                                print(f"📜 Final transcription: {final_text}")
                                pub_socket.send_string(final_text)
                        except websockets.exceptions.ConnectionClosedError as e:
                            print(f"⚠️ WebSocket closed: {e}")
                            break
                        except Exception as e:
                            print(f"🚨 Error while receiving transcription: {e}")
                            break

                # Run send and receive tasks concurrently
                await asyncio.gather(
                    send(),  # 🎤 Handle audio sending & ZMQ reception
                    receive()  # 📩 Handle transcription receiving
                )

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"🔄 WebSocket closed, reconnecting... {e}")
            await asyncio.sleep(1)  # 🔥 Wait and retry WebSocket connection

# Run the event loop
try:
    asyncio.run(send_receive())  # ✅ Runs everything together
except KeyboardInterrupt:
    print("\n🛑 Stopping transcription...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("✅ Clean-up completed.")
