#!/usr/bin/env python3
"""gTTS speech generator — speaks agent responses from ZMQ."""

import asyncio
import queue
import threading
from io import BytesIO

import zmq
from gtts import gTTS
from pygame import mixer

mixer.init()

context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://127.0.0.1:5556")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://127.0.0.1:5569")
print("Publishing Finished messages to tcp://127.0.0.1:5569")

message_queue: queue.Queue[str] = queue.Queue()


def zmq_listener() -> None:
    while True:
        message_queue.put(sub_socket.recv_string())


def split_message_into_chunks(message: str, chunk_size: int = 20) -> list[str]:
    words = message.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


async def generate_audio(chunk: str, index: int):
    try:
        tts = gTTS(chunk, lang="en", tld="us")
        mp3audio = BytesIO()
        tts.write_to_fp(mp3audio)
        mp3audio.seek(0)
        return mp3audio
    except Exception as e:
        print(f"Error generating TTS for chunk_{index}: {e}")
        return None


async def play_audio(audio, index: int) -> None:
    try:
        print(f"Playing chunk_{index}...")
        mixer.music.load(audio, "mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)
        print(f"Finished playing chunk_{index}.")
    except Exception as e:
        print(f"Error playing chunk_{index}: {e}")


async def process_message(message: str) -> None:
    print(f"Processing message: {message}")
    if message.lower().startswith("response"):
        message = message[len("response") :].strip()

    for index, chunk in enumerate(split_message_into_chunks(message)):
        audio = await generate_audio(chunk, index)
        if audio:
            await play_audio(audio, index)


async def process_messages() -> None:
    loop = asyncio.get_event_loop()
    while True:
        message = await loop.run_in_executor(None, message_queue.get)

        if message.lower() == "thinking":
            await process_message(message)
            try:
                final_message = await asyncio.wait_for(
                    loop.run_in_executor(None, message_queue.get), timeout=12.0
                )
                print(f"Received final message within timeout: {final_message}")
                await process_message(final_message)
            except asyncio.TimeoutError:
                print("No final message received within timeout.")

            pub_socket.send_string("Finished")
            print("Published: Finished")
        else:
            await process_message(message)


threading.Thread(target=zmq_listener, daemon=True).start()
asyncio.run(process_messages())
