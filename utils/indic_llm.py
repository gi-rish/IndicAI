# utils/indic_llm.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

try:
    model_name = "tiiuae/falcon-rw-1b"
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    MODEL_READY = True
except Exception as e:
    print(f"[IndicLLM Load Error] {e}")
    MODEL_READY = False


def get_indic_response(text: str, lang: str) -> str:
    if not MODEL_READY:
        return f"(IndicLLM unavailable) Echoing input in {lang}: {text}"

    prompt = f"{text}"
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    output = model.generate(input_ids, max_new_tokens=100, do_sample=True, temperature=0.7)
    return tokenizer.decode(output[0], skip_special_tokens=True)
