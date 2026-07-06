import ollama
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 180)

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

while True:
    user = input("You: ")

    if user.lower() in ["exit", "quit", "stop"]:
        speak("Goodbye.")
        break

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": user}]
    )

    reply = response["message"]["content"]
    speak(reply)