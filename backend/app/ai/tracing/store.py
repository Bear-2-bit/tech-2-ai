from collections import deque
from threading import Lock

from app.schemas.trace import TraceSummary


class TraceStore:
    def __init__(self, max_size: int = 100):
        self._items: deque[TraceSummary] = deque(maxlen=max_size)
        self._lock = Lock()

    def add(self, trace: TraceSummary) -> None:
        with self._lock:
            self._items.appendleft(trace)

    def list(self) -> list[TraceSummary]:
        with self._lock:
            return list(self._items)