"""Lightweight emotion heuristic engine."""
from dataclasses import dataclass
from typing import Literal

Sentiment = Literal["positive", "neutral", "negative"]


@dataclass
class EmotionState:
    user_sentiment: Sentiment = "neutral"
    conversation_depth: int = 0


class EmotionEngine:
    def __init__(self) -> None:
        self.state = EmotionState()

    def _estimate_sentiment(self, text: str) -> Sentiment:
        lowered = text.lower()
        if any(word in lowered for word in ["thank", "great", "good", "love"]):
            return "positive"
        if any(word in lowered for word in ["bad", "hate", "angry", "upset"]):
            return "negative"
        return "neutral"

    def update(self, user_text: str, assistant_text: str | None = None) -> EmotionState:
        self.state.user_sentiment = self._estimate_sentiment(user_text)
        self.state.conversation_depth += 1
        return self.state

    def emotional_context(self) -> str:
        return (
            f"User sentiment: {self.state.user_sentiment}. "
            f"Conversation depth: {self.state.conversation_depth}."
        )
