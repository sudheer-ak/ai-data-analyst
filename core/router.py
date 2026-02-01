import json
from core.llm import chat_json
from core.prompts import ROUTER_PROMPT, SYSTEM_ANALYST

def route_question(user_question: str, model: str, has_df: bool = True) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_ANALYST},
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": user_question},
    ]

    raw = chat_json(messages, model=model)
    route = json.loads(raw)

    if has_df and route.get("tool") == "none":
        route["tool"] = "eda"
        route["reason"] = "Dataset is loaded; forcing analysis tool to avoid hallucinated responses."

    return route

