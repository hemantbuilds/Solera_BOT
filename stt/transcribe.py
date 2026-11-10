#!/usr/bin/env python3
"""AssemblyAI realtime speech-to-text publisher for Solera_BOT."""

import asyncio
import base64
import json
import os
from pathlib import Path

import pyaudio
import websockets
import zmq
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

AUTH_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER,
)

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5557")
print("Publishing transcriptions to tcp://127.0.0.1:5557")

sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://127.0.0.1:5560")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print("Listening for ZMQ commands on tcp://127.0.0.1:5560")


async def send_receive() -> None:
    if not AUTH_KEY:
        raise SystemExit("ASSEMBLYAI_API_KEY is missing. Set it in .env")

    while True:
        try:
            print(f"Connecting to WebSocket at {URL}")
            async with websockets.connect(
                URL,
                extra_headers=(("Authorization", AUTH_KEY),),
                ping_interval=5,
                ping_timeout=20,
            ) as _ws:
                await asyncio.sleep(0.1)
                print("Receiving SessionBegins ...")
                session_begins = await _ws.recv()
                print(session_begins)

                async def send() -> None:
                    transcription_active = False
                    print("Waiting for first ZMQ START/STOP message...")

                    while True:
                        try:
                            try:
                                message = sub_socket.recv_string(flags=zmq.NOBLOCK).strip().upper()
                                print(f"Received ZMQ Command: {message}")
                                if message == "START":
                                    transcription_active = True
                                    print("Transcription STARTED")
                                    stream.stop_stream()
                                    stream.start_stream()
                                elif message == "STOP":
                                    transcription_active = False
                                    print("Transcription STOPPED")
                            except zmq.Again:
                                pass

                            if transcription_active:
                                data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                                data = base64.b64encode(data).decode("utf-8")
                                await _ws.send(json.dumps({"audio_data": str(data)}))
                            else:
                                await asyncio.sleep(0.05)
                                continue
                        except websockets.exceptions.ConnectionClosedError as e:
                            print(f"WebSocket closed while sending audio: {e}")
                            break
                        except Exception as e:
                            print(f"Error while sending audio: {e}")
                            break

                        await asyncio.sleep(0.01)

                async def receive() -> None:
                    while True:
                        try:
                            result_str = await _ws.recv()
                            data = json.loads(result_str)
                            if data.get("message_type") == "FinalTranscript":
                                final_text = data.get("text", "")
                                print(f"Final transcription: {final_text}")
                                pub_socket.send_string(final_text)
                        except websockets.exceptions.ConnectionClosedError as e:
                            print(f"WebSocket closed: {e}")
                            break
                        except Exception as e:
                            print(f"Error while receiving transcription: {e}")
                            break

                await asyncio.gather(send(), receive())

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket closed, reconnecting... {e}")
            await asyncio.sleep(1)


try:
    asyncio.run(send_receive())
except KeyboardInterrupt:
    print("\nStopping transcription...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Clean-up completed.")
