import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import ollama
import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 180)

model = whisper.load_model("base")

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def record_audio(filename="audio.wav", duration=5, fs=44100):
    print("Listening...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    wav.write(filename, fs, recording)
    return filename

while True:
    input("Press ENTER and speak (or type 'exit'): ")

    audio_file = record_audio()

    result = model.transcribe(audio_file)
    text = result["text"]

    print("You:", text)

    if text.lower() in ["exit", "quit", "stop"]:
        speak("Goodbye.")
        break

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": text}]
    )

    reply = response["message"]["content"]
    speak(reply)