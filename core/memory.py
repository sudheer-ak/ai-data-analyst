from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ChatMemory:
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def last(self, n: int = 8):
        return self.messages[-n:]

