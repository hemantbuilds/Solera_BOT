import pvporcupine
import pyaudio
import struct
import os
import zmq
import threading
import subprocess
import numpy as np

# ---------------------- CONFIGURATION ---------------------- #
ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY"  # Picovoice Access Key
WAKEWORD_FILE_PATH = "solera_en_raspberry-pi_v3_0_0.ppn"  # Wake word model file

# ZMQ Configuration
PUB_IP = "tcp://127.0.0.1:5560"  # PUB socket for sending START/STOP
SUB_IP = "tcp://127.0.0.1:5557"  # SUB socket for receiving responses

# Initialize ZMQ
context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind(PUB_IP)
print(f"Publishing START/STOP signals on {PUB_IP}")

sub_socket = context.socket(zmq.SUB)
sub_socket.connect(SUB_IP)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(f"Listening for responses on {SUB_IP}")

def play_beep():
    """Plays a beep sound using 'play -n synth 0.1 sin 440'."""
    subprocess.run(["play", "-n", "synth", "0.1", "sin", "440"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def listen_for_responses():
    """Listens for ANY responses from the ZMQ subscriber and sends a STOP signal immediately."""
    while True:
        try:
            message = sub_socket.recv_string()
            print(f"Response received: {message}")
            pub_socket.send_string("STOP")
        except Exception as e:
            print(f"Error in listening for responses: {e}")

# Start response listener thread
threading.Thread(target=listen_for_responses, daemon=True).start()

def resample_audio(audio_data, original_rate, target_rate, frame_length):
    """Resamples audio using Sox and ensures correct frame length."""
    if original_rate == target_rate:
        return audio_data
    process = subprocess.Popen(
        ["sox", "-t", "raw", "-r", str(original_rate), "-e", "signed-integer", "-b", "16", "-c", "1", "-", 
         "-t", "raw", "-r", str(target_rate), "-"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    resampled_audio, _ = process.communicate(audio_data)

    # Ensure output size is correct (Porcupine requires exact frame length)
    expected_size = frame_length * 2  # 2 bytes per sample (16-bit PCM)
    if len(resampled_audio) != expected_size:
        print(f"Warning: Resampled audio size mismatch. Expected {expected_size}, got {len(resampled_audio)}")
        resampled_audio = resampled_audio[:expected_size].ljust(expected_size, b"\0")  # Pad or trim
    return resampled_audio

def wake_word_detection():
    """Detects wake word and sends START signal upon detection."""
    try:
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKEWORD_FILE_PATH])

        pa = pyaudio.PyAudio()

        # Assign correct microphone
        mic_index = 1
        device_info = pa.get_device_info_by_index(mic_index)
        mic_sample_rate = int(device_info["defaultSampleRate"])

        print(f"Using Mic: {device_info['name']} | Sample Rate: {mic_sample_rate} Hz")

        # Open microphone stream
        audio_stream = pa.open(
            rate=mic_sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=mic_index,
            frames_per_buffer=int((mic_sample_rate / 1000) * porcupine.frame_length / 16)
        )

        print("Listening for wake word...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)

            # Resample if needed
            if mic_sample_rate != 16000:
                pcm = resample_audio(pcm, mic_sample_rate, 16000, porcupine.frame_length)

            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            if porcupine.process(pcm) >= 0:
                print("Wake word detected! Playing beep and sending START signal...")
                play_beep()
                pub_socket.send_string("START")

    except pvporcupine.PorcupineActivationError as e:
        print(f"Porcupine Activation Error: {e}")

    except OSError as e:
        print(f"Audio Device Error: {e}")
        print("Try selecting a different input device using `arecord -l` and manually updating the script.")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        if 'audio_stream' in locals(): audio_stream.close()
        if 'pa' in locals(): pa.terminate()
        if 'porcupine' in locals(): porcupine.delete()

# ---------------------- MAIN EXECUTION ---------------------- #
if __name__ == "__main__":
    wake_word_detection()
