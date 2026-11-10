import speech_recognition as sr
import asyncio
from queue import Queue

# Initialize recognizer
rec = sr.Recognizer()
rec.energy_threshold = 400  # Adjust for your environment
audio_queue = Queue()  # Queue to hold audio data for processing
text_queue = Queue()  # Queue to hold transcribed text for display

# Function to capture audio and enqueue for transcription
async def capture_audio():
    print("Adjusting for ambient noise. Please wait...")
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source, duration=1)
        print("Ready to listen. Speak into the microphone.")

        while True:
            try:
                print("Listening...")
                audio = rec.listen(source, timeout=5, phrase_time_limit=5)
                audio_queue.put(audio)  # Add the audio to the queue for processing
            except sr.WaitTimeoutError:
                print("Timeout: No speech detected.")
            except Exception as e:
                print(f"Error capturing audio: {e}")
            await asyncio.sleep(0.01)  # Yield to other tasks

# Function to process audio and transcribe speech
async def process_audio():
    while True:
        if not audio_queue.empty():
            audio = audio_queue.get()  # Get the audio from the queue
            try:
                # Recognize speech using Google Web Speech API
                text = rec.recognize_google(audio, language="en-EN")
                text_queue.put(text)  # Add the transcribed text to the queue for display
            except sr.UnknownValueError:
                print("Google Web Speech API could not understand the audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Web Speech API; {e}")
        await asyncio.sleep(0.01)  # Yield to other tasks

# Function to display transcribed text
async def display_text():
    while True:
        if not text_queue.empty():
            text = text_queue.get()  # Get the text from the queue
            print(f"You said: {text}")
        await asyncio.sleep(0.01)  # Yield to other tasks

# Main function to run all tasks concurrently
async def main():
    await asyncio.gather(
        capture_audio(),
        process_audio(),
        display_text(),
    )

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
