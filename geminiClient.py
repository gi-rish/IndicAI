# utils/gemini_client.py

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY is missing in .env!")

genai.configure(api_key=api_key)

# ✅ Use Gemini 1.5 Flash
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

def get_gemini_response(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return "Sorry, I couldn't translate that."
