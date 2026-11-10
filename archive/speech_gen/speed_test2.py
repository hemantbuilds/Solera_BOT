from gtts import gTTS
from io import BytesIO
from pygame import mixer
import asyncio
import time

# Initialize pygame mixer
mixer.init()

# Text to be converted to speech
text = ('The history of prostitution in Bengal, India, is complex, intertwined with socio-economic factors and colonial influences. '
        'During British rule, prostitution thrived in urban centers like Kolkata, often regulated under colonial laws to cater to British soldiers. '
        'Women, largely from marginalized communities, were forced into the trade due to poverty, lack of education, or social displacement. '
        'The system perpetuated exploitation, with brothels often controlled by powerful middlemen. Post-independence, prostitution in Bengal remains '
        'a socio-economic issue, particularly in areas like Sonagachi, one of Asia’s largest red-light districts. Efforts by NGOs and activists focus '
        'on rehabilitation, education, and healthcare for sex workers and their families.')

# Split the text into smaller chunks
chunks = text.split('. ')
chunks = [chunk.strip() + '.' for chunk in chunks if chunk.strip()]  # Ensure proper punctuation for each chunk


async def generate_audio(chunk, index):
    """Generate audio for a given text chunk."""
    try:
        start_time = time.perf_counter()
        tts = gTTS(chunk, lang='en', tld='us')
        mp3audio = BytesIO()
        tts.write_to_fp(mp3audio)
        mp3audio.seek(0)
        end_time = time.perf_counter()
        print(f"Generated TTS for chunk_{index}: '{chunk}' in {end_time - start_time:.2f} seconds")
        return mp3audio
    except Exception as e:
        print(f"Error processing chunk_{index}: {e}")
        return None


async def play_audio(audio, index):
    """Play the audio chunk."""
    try:
        print(f"Playing chunk_{index}...")
        mixer.music.load(audio, "mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)  # Allow other coroutines to run while playing audio
        print(f"Finished playing chunk_{index}.")
    except Exception as e:
        print(f"Error playing chunk_{index}: {e}")


async def main():
    for index, chunk in enumerate(chunks):
        # Generate the audio for the current chunk
        audio = await generate_audio(chunk, index)
        if audio:
            # Play the audio once it's ready
            await play_audio(audio, index)


# Run the asyncio event loop
asyncio.run(main())
