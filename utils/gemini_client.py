import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

# For testing purposes, use a hardcoded API key if environment variable is not found
api_key = os.getenv("GEMINI_API_KEY")
# Remove hardcoded API key and rely solely on environment variable
if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY is missing in environment!")

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
