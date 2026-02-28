"""VAD engine with optional webrtcvad backend and safe fallback."""

import array
import math
from typing import Optional

try:
    import webrtcvad  # type: ignore
except Exception:  # pylint: disable=broad-except
    webrtcvad = None


class VADEngine:
    def __init__(self, aggressiveness: int = 2, energy_threshold: float = 450.0):
        self.energy_threshold = energy_threshold
        self._webrtc: Optional[object] = None
        if webrtcvad is not None:
            self._webrtc = webrtcvad.Vad(max(0, min(3, aggressiveness)))

    def is_speech(self, audio_frame: bytes, sample_rate: int = 16000) -> bool:
        if not audio_frame:
            return False

        if self._webrtc is not None:
            frame = self._fit_frame(audio_frame, sample_rate)
            if frame is not None:
                try:
                    return bool(self._webrtc.is_speech(frame, sample_rate))
                except Exception:  # pylint: disable=broad-except
                    pass

        return self._energy_is_speech(audio_frame)

    @staticmethod
    def _fit_frame(audio_frame: bytes, sample_rate: int) -> bytes | None:
        bytes_per_sample = 2
        for frame_ms in (10, 20, 30):
            size = int(sample_rate * frame_ms / 1000) * bytes_per_sample
            if len(audio_frame) >= size:
                return audio_frame[:size]
        return None

    def _energy_is_speech(self, audio_frame: bytes) -> bool:
        if len(audio_frame) < 2:
            return False
        samples = array.array("h")
        samples.frombytes(audio_frame[: len(audio_frame) - (len(audio_frame) % 2)])
        if not samples:
            return False
        squares = sum(sample * sample for sample in samples)
        rms = math.sqrt(squares / len(samples))
        return rms >= self.energy_threshold
