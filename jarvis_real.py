import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import whisper
import ollama
import pyttsx3
import queue

engine = pyttsx3.init()
engine.setProperty("rate", 180)

model = whisper.load_model("base")

fs = 44100
record_seconds = 5

audio_queue = queue.Queue()

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def record():
    print("🎤 Listening...")
    audio = sd.rec(int(record_seconds * fs), samplerate=fs, channels=1)
    sd.wait()
    wav.write("temp.wav", fs, audio)
    return "temp.wav"

def wake_word_detected(text):
    return "jarvis" in text.lower()

while True:
    file = record()

    result = model.transcribe(file)
    text = result["text"].strip()

    print("You:", text)

    # Wake word system
    if not wake_word_detected(text):
        continue

    # Remove wake word
    command = text.lower().replace("jarvis", "").strip()

    if command in ["stop", "exit", "quit"]:
        speak("Shutting down.")
        break

    if command == "":
        speak("Yes?")
        continue

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": command}]
    )

    reply = response["message"]["content"]
    speak(reply)