import json
from core.llm import chat_json
from core.prompts import ROUTER_PROMPT, SYSTEM_ANALYST

def route_question(user_question: str, model: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_ANALYST},
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": user_question},
    ]
    raw = chat_json(messages, model=model)
    return json.loads(raw)

