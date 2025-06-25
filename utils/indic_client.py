# utils/indic_client.py
import requests

def get_indic_response(text: str, lang: str, history=None) -> str:
    payload = {
        "text": text,
        "language": lang,
        "history": history or []
    }

    res = requests.post("http://localhost:5000/indic-ai", json=payload)
    return res.json().get("response", "")
