"""
jarvis_realtime.py — v5

Upgrades over jarvis_final.py:
  - No more fixed-duration recording (5s / 8s windows).
  - Uses WebRTC Voice Activity Detection (VAD) to detect when you start
    and stop speaking, so it captures exactly one utterance at a time.
  - Feels closer to a real conversation: talk whenever you want, pause when
    you're done, no waiting around for a timer to run out.

How it works:
  1. The microphone streams continuously in small 30ms frames.
  2. Each frame is classified as "speech" or "silence" by webrtcvad.
  3. Once enough consecutive speech frames appear, we start recording an
     utterance (including a short pre-roll buffer so we don't clip the
     first word).
  4. Once enough consecutive silence frames appear after that, the
     utterance is considered finished and gets sent to Whisper.
  5. The transcribed text is checked for the wake word, then passed to
     Ollama, and the reply is spoken aloud.

Tuning knobs are all in the SETTINGS section below.
"""

import collections
import queue
import sys

import numpy as np
import sounddevice as sd
import webrtcvad
import whisper
import ollama
import pyttsx3

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16000          # webrtcvad requires 8000, 16000, 32000, or 48000
FRAME_MS = 30                # webrtcvad requires 10, 20, or 30 ms frames
VAD_AGGRESSIVENESS = 2       # 0 (least aggressive) - 3 (most aggressive filtering of non-speech)

PRE_ROLL_MS = 300            # audio kept before speech is detected, to avoid clipping the first word
SILENCE_TIMEOUT_MS = 700     # how much trailing silence ends an utterance
MIN_SPEECH_MS = 250          # ignore blips shorter than this (coughs, clicks, etc.)
MAX_UTTERANCE_S = 15         # hard cap so a stuck mic doesn't record forever

WAKE_WORD = "jarvis"
WHISPER_MODEL_SIZE = "small"   # "base" is faster / less accurate, "small" is a good CPU balance
OLLAMA_MODEL = "llama3.2:3b"

FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
FRAME_BYTES = FRAME_SAMPLES * 2  # 16-bit PCM = 2 bytes/sample

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------
print("Loading Whisper model...")
whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)

vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 180)

audio_q: "queue.Queue[bytes]" = queue.Queue()


def speak(text: str) -> None:
    print("Jarvis:", text)
    tts_engine.say(text)
    tts_engine.runAndWait()


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    audio_q.put(bytes(indata))


def frames_to_float32(frames: bytes) -> np.ndarray:
    """Convert raw 16-bit PCM bytes into the float32 array Whisper expects."""
    audio_int16 = np.frombuffer(frames, dtype=np.int16)
    return audio_int16.astype(np.float32) / 32768.0


def listen_for_utterance() -> np.ndarray:
    """
    Blocks until one full utterance (speech, bounded by silence) has been
    captured, then returns it as a float32 numpy array ready for Whisper.
    """
    pre_roll_frames = collections.deque(maxlen=PRE_ROLL_MS // FRAME_MS)
    triggered = False
    voiced_frames = []
    silence_run_ms = 0
    speech_run_ms = 0

    print("\n🎤 Listening...")

    while True:
        frame = audio_q.get()
        if len(frame) != FRAME_BYTES:
            continue  # skip partial frames

        is_speech = vad.is_speech(frame, SAMPLE_RATE)

        if not triggered:
            pre_roll_frames.append(frame)
            if is_speech:
                speech_run_ms += FRAME_MS
                if speech_run_ms >= MIN_SPEECH_MS:
                    # Speech confirmed - start the utterance, including pre-roll
                    triggered = True
                    voiced_frames.extend(pre_roll_frames)
                    silence_run_ms = 0
            else:
                speech_run_ms = 0
        else:
            voiced_frames.append(frame)
            if is_speech:
                silence_run_ms = 0
            else:
                silence_run_ms += FRAME_MS

            total_ms = len(voiced_frames) * FRAME_MS
            if silence_run_ms >= SILENCE_TIMEOUT_MS or total_ms >= MAX_UTTERANCE_S * 1000:
                break

    raw_audio = b"".join(voiced_frames)
    return frames_to_float32(raw_audio)


def main():
    speak("Jarvis is now online")

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SAMPLES,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    )

    with stream:
        while True:
            audio_array = listen_for_utterance()

            if audio_array.size == 0:
                continue

            result = whisper_model.transcribe(audio_array, language="en", fp16=False)
            text = result["text"].strip()

            if not text:
                continue

            print("You:", text)
            text_lower = text.lower()

            if WAKE_WORD not in text_lower:
                continue

            command = text_lower.replace(WAKE_WORD, "").strip()

            if command in ["stop", "exit", "shutdown"]:
                speak("Shutting down.")
                break

            if command == "":
                speak("Yes?")
                continue

            try:
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{"role": "user", "content": command}],
                )
                reply = response["message"]["content"]
                speak(reply)
            except Exception as e:
                speak("Sorry, I had an error.")
                print(e)


if __name__ == "__main__":
    main()
