import pvporcupine
import pyaudio
import struct
import os

# Replace with your actual Picovoice Access Key
ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY"

# Path to your custom wake word model file (.ppn)
WAKEWORD_FILE_PATH = "solera_en_raspberry-pi_v3_0_0.ppn"

try:
    # Initialize Porcupine with custom wake word
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[WAKEWORD_FILE_PATH]
    )

    # Set up microphone stream
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print(f"Listening for wake word...")

    while True:
        # Read audio frame
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        # Process audio frame to detect wake word
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Wake word detected!")
            os.system("espeak 'bolo taara raa ra'")  # Replace with desired action

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
