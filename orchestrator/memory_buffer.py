"""Short-term conversation buffer with fixed turn retention."""
from collections import deque
from typing import Deque, Dict, List, Literal

Role = Literal["user", "assistant"]
Entry = Dict[str, str]


class ConversationBuffer:
    def __init__(self, max_turns: int = 6) -> None:
        self.max_turns = max_turns
        self._buffer: Deque[Entry] = deque(maxlen=max_turns)

    def add(self, role: Role, content: str) -> None:
        self._buffer.append({"role": role, "content": content})

    def get_history(self) -> List[Entry]:
        return list(self._buffer)

    def get_formatted_history(self) -> str:
        lines = []
        for entry in self._buffer:
            lines.append(f"{entry['role']}: {entry['content']}")
        return "\n".join(lines)
