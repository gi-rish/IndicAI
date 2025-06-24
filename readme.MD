A terminal‑based AI assistant that supports both **text** and **voice** interaction in Indian regional languages. Current pipeline:

```
User (voice/text, regional) → Whisper (ASR) → Deep‑Translator → GPT‑3.5/4 → gTTS (TTS) → Audio/Text reply
```

---

## ✨ Features

| Capability | Details |
|------------|---------|
| **Voice input** | Local Whisper transcribes speech; auto‑detects language |
| **Text input**  | Direct CLI prompt |
| **Language detection** | Whisper (voice) & `langdetect` (text) |
| **Translation** | `deep‑translator` converts regional → English |
| **LLM chat** | OpenAI GPT‑3.5 by default (memory buffer retained per session) |
| **Voice reply** | gTTS speaks GPT reply in same regional language |
| **Modes** | Chosen once per session (`text` or `voice`) |

---

## 🗂️ Project Structure

```
voicebot/
├── main.py            # Orchestrator with conversation loop
├── input_handler.py   # Handles text/voice input + language detection
├── transcriber.py     # Whisper transcription + mic recording
├── translator.py      # Regional → English translation (deep‑translator)
├── llm_client.py      # OpenAI GPT client (v1 SDK)
├── tts.py             # gTTS speech synthesis + playback
├── utils.py           # Helper (audio playback)
└── requirements.txt
```

---

## 🔧 Tools & Libraries

| Stage | Library / Service | Notes |
|-------|-------------------|-------|
| ASR   | `whisper`         | Local model, language auto‑detect |
| Record| `sounddevice`, `scipy` | Capture mic & save WAV |
| L‑Detect | `langdetect`   | Text‑only fallback |
| Translate | `deep‑translator` | Google Translate backend |
| LLM   | `openai>=1.x`     | GPT‑3.5 / GPT‑4, memory buffer supported |
| TTS   | `gTTS`            | Free TTS; good Hindi, weaker Kannada |
| Audio | `ffmpeg` / `ffplay` | Playback of MP3/WAV |

---

## ⚙️ Installation

```bash
# Create and activate venv
python3 -m venv voicebot-env
source voicebot-env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# System packages (Ubuntu)
sudo apt update
sudo apt install ffmpeg portaudio19-dev python3-pyaudio
```

`requirements.txt` contents:
```
openai
whisper
torch
sounddevice
scipy
deep-translator
langdetect
gTTS
```

---

## 🔑 Environment Variables

Set your OpenAI key once:
```bash
export OPENAI_API_KEY="sk-..."
```

---

## 🚀 Usage

```bash
python3 main.py
# Choose input mode: text or voice
```
- **Exit** any time by typing `exit` (text mode) or saying the word “exit” (voice mode).

---

## 🛣️ Roadmap

1. Replace gTTS with higher‑quality Kannada TTS (Google Cloud TTS / Bhashini)
2. Persist memory across sessions (simple JSON storage)
3. Add transcript logging per session
4. Optional GUI (Gradio) or Flask API wrapper