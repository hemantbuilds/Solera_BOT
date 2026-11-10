import assemblyai as aai

aai.settings.api_key = "YOUR_ASSEMBLYAI_API_KEY"
transcriber = aai.Transcriber()

# Transcribe the audio file
transcript = transcriber.transcribe("./test.wav")

print(transcript.text)
