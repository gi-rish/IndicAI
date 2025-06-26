
from openai import OpenAI

client = OpenAI(api_key="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")



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
