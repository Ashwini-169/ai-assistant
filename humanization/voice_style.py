"""Voice style profile for Indian neutral female tone."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceStyle:
    speech_rate: float = 0.92
    pitch_shift: float = -2.0  # percentage
    tone_description: str = "calm, conversational"


INDIAN_NEUTRAL_FEMALE = VoiceStyle()
