# Text-To-Speech Translation with Python and Google TTS
# By TechMakerAI on YouTube
#
from gtts import gTTS
import os
from io import BytesIO
from pygame import mixer
import time  # Import the time module

# Initialize the mixer
mixer.init()

# Create a BytesIO object to store audio
mp3audio = BytesIO()

# Text to be converted to speech
text = ('The history of prostitution in Bengal, India, is complex, intertwined with socio-economic factors and colonial influences. '
        'During British rule, prostitution thrived in urban centers like Kolkata, often regulated under colonial laws to cater to British soldiers. '
        'Women, largely from marginalized communities, were forced into the trade due to poverty, lack of education, or social displacement. '
        'The system perpetuated exploitation, with brothels often controlled by powerful middlemen. Post-independence, prostitution in Bengal remains '
        'a socio-economic issue, particularly in areas like Sonagachi, one of Asia\u2019s largest red-light districts. Efforts by NGOs and activists focus '
        'on rehabilitation, education, and healthcare for sex workers and their families.')

# Start the timer
start_time = time.perf_counter()

# Generate TTS using Google TTS
tts = gTTS(text, lang='en', tld='us')

# Stop the timer and calculate the elapsed time
#end_time = time.perf_counter()

#elapsed_time = end_time - start_time
#print(f"Time taken to generate TTS: {elapsed_time:.6f} seconds")

# Save TTS to the BytesIO object
tts.write_to_fp(mp3audio)
mp3audio.seek(0)

# Load and play the audio using pygame
mixer.music.load(mp3audio, "mp3")
mixer.music.play()

end_time = time.perf_counter()

elapsed_time = end_time - start_time
print(f"Time taken to generate TTS: {elapsed_time:.6f} seconds")
# Wait until the playback is finished
while mixer.music.get_busy():
    pass
