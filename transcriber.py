import whisper
import sounddevice as sd
from scipy.io.wavfile import write

model = whisper.load_model("base")

def record_audio(filename="input.wav", duration=5, fs=16000):
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, audio)
    print("Saved to:", filename)

# def transcribe_voice(file_path):
#     result = model.transcribe(file_path)
#     return result["text"]

def transcribe_voice(file_path):
    result = model.transcribe(file_path)
    text = result["text"]
    lang = result["language"]
    return text, lang
