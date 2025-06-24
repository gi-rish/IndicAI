
from openai import OpenAI

client = OpenAI(api_key="sk-proj-_")



def get_gpt_response(history):
    response = client.chat.completions.create(
        model="gpt-4",
        max_tokens=100, 
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Keep your answers brief and to the point."            }
        ] + [
            {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}]
            } for msg in history
        ]
    )

    # Handle both new (list-based) and old (string) formats
    content = response.choices[0].message.content
    if isinstance(content, list):
        return content[0]["text"]
    return content  # it's already a plain string
