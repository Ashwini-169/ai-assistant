"""Assistant state machine for safe semi-duplex flow."""

import threading
from enum import Enum


class AssistantState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


_STATE_ICON = {
    AssistantState.IDLE: "⚪",
    AssistantState.LISTENING: "🔵",
    AssistantState.THINKING: "🟡",
    AssistantState.SPEAKING: "🟢",
    AssistantState.INTERRUPTED: "🔴",
}


class AssistantStateController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = AssistantState.IDLE

    def set_state(self, state: AssistantState) -> None:
        with self._lock:
            self._state = state

    def get_state(self) -> AssistantState:
        with self._lock:
            return self._state

    def visual_label(self) -> str:
        state = self.get_state()
        return f"{_STATE_ICON[state]} {state.value}"
