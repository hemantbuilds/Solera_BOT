import pyaudio

p = pyaudio.PyAudio()

device_index = 3  # Replace with your microphone's index
device_info = p.get_device_info_by_index(device_index)

print(f"Device Name: {device_info['name']}")
print(f"Supported Sample Rates: {device_info['defaultSampleRate']}")
p.terminate()
