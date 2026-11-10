import speech_recognition as sr

# Initialize recognizer
rec = sr.Recognizer()
rec.energy_threshold = 100  # Adjust if needed for your environment

# Function to capture audio and recognize speech
def recognize_speech():
    print("Adjusting for ambient noise. Please wait...")
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source, duration=1)
        print("Ready to listen. Speak into the microphone.")

        while True:
            try:
                print("Listening...")
                # Listen for short durations to make it more real-time
                audio = rec.listen(source, timeout=10, phrase_time_limit=10)

                # Recognize speech using Google Web Speech API
                text = rec.recognize_google(audio, language="en-EN")
                print(f"You said: {text}")
            except sr.UnknownValueError:
                print("Google Web Speech API could not understand the audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Web Speech API; {e}")
            except KeyboardInterrupt:
                print("\nExiting...")
                break

# Main function
if __name__ == "__main__":
    recognize_speech()
