import pvporcupine
import pyaudio
import struct
import os
import zmq
import threading
import subprocess
import numpy as np
from scipy.signal import resample

# ---------------------- CONFIGURATION ---------------------- #
ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY"  # Replace with your Picovoice Access Key
WAKEWORD_FILE_PATH = "solera_en_raspberry-pi_v3_0_0.ppn"  # Path to your custom wake word model

# ZMQ Configuration
PUB_IP = "tcp://127.0.0.1:5560"  # PUB socket for sending START/STOP
SUB_IP = "tcp://127.0.0.1:5557"  # SUB socket for receiving responses

# Initialize ZMQ
context = zmq.Context()
pub_socket = context.socket(zmq.PUB)  # PUB socket for sending control signals
pub_socket.bind(PUB_IP)
print(f"Publishing START/STOP signals on {PUB_IP}")

sub_socket = context.socket(zmq.SUB)  # SUB socket for listening to responses
sub_socket.connect(SUB_IP)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(f"Listening for responses on {SUB_IP}")

def play_beep():
    """
    Plays a beep sound using 'play -n synth 0.1 sin 440'.
    """
    subprocess.run(["play", "-n", "synth", "0.1", "sin", "440"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ---------------------- FUNCTIONS ---------------------- #
def listen_for_responses():
    """
    Listens for responses from the ZMQ subscriber and sends a STOP signal.
    """
    while True:
        try:
            message = sub_socket.recv_string()
            print(f"Response received: {message}")

            if message.strip().lower() == "response received":
                print("Sending STOP signal...")
                pub_socket.send_string("STOP")

        except Exception as e:
            print(f"Error in listening for responses: {e}")

# Start the response listener in a separate thread
listener_thread = threading.Thread(target=listen_for_responses, daemon=True)
listener_thread.start()

def get_lowest_card_input_device():
    """
    Returns the device index of the input device with the lowest card number.
    """
    pa = pyaudio.PyAudio()
    lowest_card = None
    selected_device_index = None

    for i in range(pa.get_device_count()):
        device_info = pa.get_device_info_by_index(i)
        if device_info.get('maxInputChannels', 0) > 0:  # Check if it's an input device
            card_number = device_info.get('hostApi')  # Use hostApi as a proxy for card number
            if lowest_card is None or card_number < lowest_card:
                lowest_card = card_number
                selected_device_index = i

    pa.terminate()
    return selected_device_index

def get_supported_sample_rate(device_index):
    """
    Returns a supported sample rate for the given device.
    """
    pa = pyaudio.PyAudio()
    device_info = pa.get_device_info_by_index(device_index)
    supported_sample_rate = 16000  # Default to 16 kHz

    # Try common sample rates
    common_sample_rates = [16000, 44100, 48000, 22050, 8000]
    for rate in common_sample_rates:
        try:
            test_stream = pa.open(
                rate=rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=1024,
                input_device_index=device_index
            )
            test_stream.close()
            supported_sample_rate = rate
            break
        except OSError:
            continue

    pa.terminate()
    return supported_sample_rate

def resample_audio(data, original_rate, target_rate, target_length):
    """
    Resamples audio data from the original rate to the target rate and ensures the output has the target length.
    """
    ratio = target_rate / original_rate
    resampled_data = resample(data, int(len(data) * ratio))
    # Ensure the output has the exact target length
    if len(resampled_data) < target_length:
        # Pad with zeros if the resampled data is too short
        resampled_data = np.pad(resampled_data, (0, target_length - len(resampled_data)), mode='constant')
    elif len(resampled_data) > target_length:
        # Truncate if the resampled data is too long
        resampled_data = resampled_data[:target_length]
    return resampled_data.astype(np.int16)

def wake_word_detection():
    """
    Uses Porcupine to detect the wake word and sends a START signal upon detection.
    """
    try:
        # Initialize Porcupine with the default sample rate (16 kHz)
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[WAKEWORD_FILE_PATH],
            sensitivities=[0.5]  # Adjust sensitivity if needed
        )

        pa = pyaudio.PyAudio()
        selected_device_index = get_lowest_card_input_device()

        if selected_device_index is None:
            raise Exception("No input device found!")

        # Get the supported sample rate for the selected device
        supported_sample_rate = get_supported_sample_rate(selected_device_index)
        print(f"Using sample rate: {supported_sample_rate}")

        # Open the audio stream with the supported sample rate
        audio_stream = pa.open(
            rate=supported_sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=selected_device_index
        )

        print(f"Listening for wake word on device index {selected_device_index}...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            # Resample audio data to 16 kHz if necessary
            if supported_sample_rate != porcupine.sample_rate:
                pcm = resample_audio(np.array(pcm), supported_sample_rate, porcupine.sample_rate, porcupine.frame_length)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected! Playing beep and sending START signal...")
                play_beep()  # Play beep sound
                pub_socket.send_string("START")  # Send START signal

    except pvporcupine.PorcupineActivationError as e:
        print(f"Porcupine Activation Error: {e}")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        if 'audio_stream' in locals():
            audio_stream.close()
        if 'pa' in locals():
            pa.terminate()
        if 'porcupine' in locals():
            porcupine.delete()

# ---------------------- MAIN EXECUTION ---------------------- #
if __name__ == "__main__":
    wake_word_detection()
