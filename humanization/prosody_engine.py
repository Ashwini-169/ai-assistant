"""Deterministic prosody adjustments before TTS."""
from typing import Tuple

FILLERS = ["Hmm, ", "Okay, "]


def shorten_sentence(text: str, max_len: int = 240) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def apply_prosody(text: str, use_filler: bool = True) -> Tuple[str, str]:
    filler = FILLERS[0] if use_filler else ""
    adjusted = shorten_sentence(text)
    adjusted = adjusted.replace(",", ", ...")
    return filler + adjusted, filler
