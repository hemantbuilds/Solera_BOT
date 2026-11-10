#!/usr/bin/env python3
"""Picovoice Porcupine wake-word detector for Solera_BOT."""

import os
import struct
import subprocess
import threading
from pathlib import Path

import pvporcupine
import pyaudio
import zmq
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")
WAKEWORD_FILE_PATH = Path(__file__).resolve().parent / "solera_en_raspberry-pi_v3_0_0.ppn"
MP3_FILE_PATH = Path(__file__).resolve().parent / "sounds" / "bubble-pop-2-293341.mp3"

PUB_IP = "tcp://127.0.0.1:5560"
SUB_IP = "tcp://127.0.0.1:5557"

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind(PUB_IP)
print(f"Publishing START/STOP signals on {PUB_IP}")

sub_socket = context.socket(zmq.SUB)
sub_socket.connect(SUB_IP)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(f"Listening for responses on {SUB_IP}")


def play_mp3(file_path: Path) -> None:
    subprocess.run(
        ["mpg123", str(file_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def listen_for_responses() -> None:
    while True:
        try:
            message = sub_socket.recv_string()
            print(f"Response received: {message}")
            print("Sending STOP signal...")
            pub_socket.send_string("STOP")
        except Exception as e:
            print(f"Error in listening for responses: {e}")


listener_thread = threading.Thread(target=listen_for_responses, daemon=True)
listener_thread.start()


def wake_word_detection() -> None:
    if not ACCESS_KEY:
        raise SystemExit("PICOVOICE_ACCESS_KEY is missing. Set it in .env")

    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[str(WAKEWORD_FILE_PATH)],
        )
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        print("Listening for wake word...")
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print("Wake word detected! Playing cue and sending START...")
                threading.Thread(
                    target=play_mp3, args=(MP3_FILE_PATH,), daemon=True
                ).start()
                pub_socket.send_string("START")

    except pvporcupine.PorcupineActivationError as e:
        print(f"Porcupine Activation Error: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        if porcupine is not None:
            porcupine.delete()


if __name__ == "__main__":
    wake_word_detection()
