"""Thread-safe interruption signal for semi-duplex barge-in."""

import threading


class InterruptController:
    def __init__(self) -> None:
        self._flag = threading.Event()

    def trigger(self) -> None:
        self._flag.set()

    def clear(self) -> None:
        self._flag.clear()

    def is_triggered(self) -> bool:
        return self._flag.is_set()
