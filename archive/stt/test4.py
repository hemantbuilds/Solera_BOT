import speech_recognition as sr
import asyncio
from queue import Queue

# Initialize recognizer
rec = sr.Recognizer()
rec.energy_threshold = 100  # Adjust for sensitivity
audio_chunks = [Queue(), Queue(), Queue()]  # Separate queues for each function
text_queue = Queue()  # Queue to synchronize transcribed text

# Function to record audio and put it in its respective queue
async def record_audio(index):
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source, duration=0.5)  # Quick adjustment
        print(f"Microphone {index} is ready.")
        while True:
            try:
                audio = rec.listen(source, timeout=None, phrase_time_limit=None)
                audio_chunks[index].put(audio)
                print(f"Recorded audio chunk in function {index}.")
            except Exception as e:
                print(f"Error recording audio in function {index}: {e}")
            await asyncio.sleep(0.01)

# Function to process audio and transcribe text
async def process_audio(index):
    while True:
        if not audio_chunks[index].empty():
            audio = audio_chunks[index].get()
            try:
                text = rec.recognize_google(audio, language="en-EN")
                text_queue.put((index, text))  # Add the text with its index
                print(f"Function {index} transcribed: {text}")
            except sr.UnknownValueError:
                print(f"Function {index}: Could not understand the audio.")
            except sr.RequestError as e:
                print(f"Function {index}: Request error - {e}")
            except Exception as e:
                print(f"Function {index}: Transcription error - {e}")
        await asyncio.sleep(0.01)

# Function to synchronize and display text
async def display_text():
    last_index = -1
    while True:
        if not text_queue.empty():
            index, text = text_queue.get()
            if index == (last_index + 1) % 3:  # Ensure text is displayed in order
                print(text, end=" ", flush=True)
                last_index = index
        await asyncio.sleep(0.01)

# Main function to run tasks concurrently
async def main():
    await asyncio.gather(
        record_audio(0),
        record_audio(1),
        record_audio(2),
        process_audio(0),
        process_audio(1),
        process_audio(2),
        display_text(),
    )

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Exit gracefully on Ctrl+C
