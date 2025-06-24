# asr_client.py
import torch
import torchaudio
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "ai4bharat/indic-conformer-600m-multilingual", trust_remote_code=True
)


# Map full language names to ISO codes expected by the model
LANG_MAP = {
    "kannada": "kn",
    "hindi": "hi",
    "marathi": "mr",
    "english": "en",
    "tamil": "ta"
    # Add more if needed
}


def transcribe_audio(file_path: str, lang_code: str) -> str:
    print (lang_code)
    if lang_code == "en":
        # Use Whisper for English
        return transcribe_with_whisper(file_path)
    else:
        # Use Indic Conformer for regional languages
        return transcribe_with_conformer(file_path, lang_code)

def transcribe_with_conformer(audio_path: str, user_lang: str) -> str:
    try:
        lang_code = LANG_MAP.get(user_lang.lower())
        if lang_code is None:
            raise ValueError(f"Unsupported language: {user_lang}")

        wav, sr = torchaudio.load(audio_path)
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            wav = resampler(wav)

        # Run model inference
        result = model(wav, lang_code, "ctc")  # Use CTC mode for now
        return result

    except Exception as e:
        print(f"[ASR Error]: {e}")
        return ""
