import pvporcupine
import pyaudio
import struct
import os
import zmq
import threading
import subprocess  # Import subprocess for playing sound

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
print(f"✅ Publishing START/STOP signals on {PUB_IP}")

sub_socket = context.socket(zmq.SUB)  # SUB socket for listening to responses
sub_socket.connect(SUB_IP)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(f"📡 Listening for responses on {SUB_IP}")

def play_beep():
    """Plays a beep sound using 'play -n synth 0.1 sin 440'."""
    subprocess.run(["play", "-n", "synth", "0.1", "sin", "440"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ---------------------- FUNCTIONS ---------------------- #
def listen_for_responses():
    """Listens for any response from the ZMQ subscriber and sends a STOP signal."""
    while True:
        try:
            message = sub_socket.recv_string()
            print(f"📩 Response received: {message}")

            # Send STOP for any message received
            print("🚀 Sending STOP signal...")
            pub_socket.send_string("STOP")

        except Exception as e:
            print(f"⚠️ Error in listening for responses: {e}")

# Start the response listener in a separate thread
listener_thread = threading.Thread(target=listen_for_responses, daemon=True)
listener_thread.start()

def wake_word_detection():
    """Uses Porcupine to detect the wake word and sends a START signal upon detection."""
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[WAKEWORD_FILE_PATH]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("🎤 Listening for wake word...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("✅ Wake word detected! Playing beep and sending START signal...")
                play_beep()  # Play beep sound
                pub_socket.send_string("START")  # Send START signal

    except pvporcupine.PorcupineActivationError as e:
        print(f"⚠️ Porcupine Activation Error: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")

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
