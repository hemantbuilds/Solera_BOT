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


async def generate_and_play(chunk):
    """Generate audio for a given text chunk and play it immediately."""
    start_time = time.perf_counter()

    # Generate audio
    tts = gTTS(chunk, lang='en', tld='us')
    mp3audio = BytesIO()
    tts.write_to_fp(mp3audio)
    mp3audio.seek(0)

    end_time = time.perf_counter()
    print(f"Generated TTS for chunk: '{chunk}' in {end_time - start_time:.2f} seconds")

    # Play the audio
    mixer.music.load(mp3audio, "mp3")
    mixer.music.play()

    # Wait until playback is complete
    while mixer.music.get_busy():
        await asyncio.sleep(0.1)


async def main():
    for chunk in chunks:
        await generate_and_play(chunk)  # Generate and play each chunk sequentially


# Run the asyncio event loop
asyncio.run(main())
