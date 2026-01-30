import os
from openai import OpenAI

def get_client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def chat_json(messages, model: str):
    client = get_client()
    # Use JSON mode to keep routing clean
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return resp.choices[0].message.content

def chat_text(messages, model: str):
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content

def generate_python(messages, model: str):
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
    )
    return resp.choices[0].message.content

