import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import whisper
import ollama
import pyttsx3
import time
import os

# ---------- VOICE ----------
engine = pyttsx3.init()
engine.setProperty("rate", 180)

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

# ---------- LOAD MODEL ----------
print("Loading Whisper model...")
model = whisper.load_model("small")  # balanced for your PC

# ---------- SETTINGS ----------
fs = 44100
record_seconds = 8
wake_word = "jarvis"

def record_audio():
    print("\n🎤 Listening...")
    audio = sd.rec(int(record_seconds * fs), samplerate=fs, channels=1)
    sd.wait()
    file = "temp.wav"
    wav.write(file, fs, audio)
    return file

def transcribe(file):
    result = model.transcribe(file, language="en", fp16=False)
    return result["text"].strip()

# ---------- START ----------
speak("Jarvis is now online")

while True:

    audio_file = record_audio()
    text = transcribe(audio_file)

    print("You:", text)

    text_lower = text.lower()

    # Wake word check
    if wake_word not in text_lower:
        continue

    command = text_lower.replace(wake_word, "").strip()

    if command in ["stop", "exit", "shutdown"]:
        speak("Shutting down.")
        break

    if command == "":
        speak("Yes?")
        continue

    # AI RESPONSE
    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": command}]
        )

        reply = response["message"]["content"]
        speak(reply)

    except Exception as e:
        speak("Sorry, I had an error.")
        print(e)