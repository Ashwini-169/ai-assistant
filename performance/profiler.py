"""Simple profiler for interaction latencies."""
import json
import time
from typing import Dict, Optional

from performance.metrics_logger import log_metrics


class Profiler:
    def __init__(self) -> None:
        self.marks: Dict[str, float] = {}

    def mark(self, name: str) -> None:
        self.marks[name] = time.perf_counter()

    def elapsed_ms(self, start: str, end: str) -> Optional[float]:
        if start in self.marks and end in self.marks:
            return (self.marks[end] - self.marks[start]) * 1000
        return None

    def record_and_log(self) -> None:
        metrics = {key: round((time.perf_counter() - ts) * 1000, 2) for key, ts in self.marks.items()}
        log_metrics(metrics)


def profile_interaction(metrics: Dict[str, float]) -> None:
    log_metrics(metrics)
