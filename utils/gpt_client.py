# utils/gpt_client.py

from openai import OpenAI
import os

client = OpenAI(api_key="")

def get_gpt_response(text: str, chat_history=None) -> str:
    messages = [{"role": "user", "content": text}]
    if chat_history:
        messages = chat_history + messages

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return response.choices[0].message.content

