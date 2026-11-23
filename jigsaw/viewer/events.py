"""In-process event bus between the app loop (publisher) and viewer clients (subscribers).

publish never blocks: each subscriber has its own bounded queue and loses its oldest events when it
falls behind. Events are the dicts of CONTRACTS section 5. The latest camera JPEG is kept apart from
the events and fetched by the page on each frame event.
"""
import threading
from collections import deque


class Subscription:
    """Iterator over one client's events. close() unregisters it, also before the first next()."""

    def __init__(self, bus: "EventBus", maxlen: int, heartbeat: float | None):
        self._bus = bus
        self._heartbeat = heartbeat
        self.items: deque = deque(maxlen=maxlen)
        self.cond = threading.Condition()

    def __iter__(self) -> "Subscription":
        return self

    def __next__(self) -> dict | None:
        with self.cond:
            while not self.items:
                if not self.cond.wait(self._heartbeat) and self._heartbeat is not None:
                    return None
            return self.items.popleft()

    def close(self) -> None:
        self._bus._remove(self)


class EventBus:
    def __init__(self, maxlen: int = 100):
        self._maxlen = maxlen
        self._subs: list[Subscription] = []
        self._lock = threading.Lock()
        self._frame: bytes | None = None

    def publish(self, event: dict) -> None:
        with self._lock:
            subs = list(self._subs)
        for sub in subs:
            with sub.cond:
                sub.items.append(event)        # deque(maxlen) drops the oldest
                sub.cond.notify()

    def subscribe(self, heartbeat: float | None = None) -> Subscription:
        """Register a client now and return its event iterator.

        With heartbeat (seconds) the iterator yields None after that long without an event, so a server
        can write a keep-alive and notice a closed connection. Without it, next() waits for an event.
        """
        sub = Subscription(self, self._maxlen, heartbeat)
        with self._lock:
            self._subs.append(sub)
        return sub

    def _remove(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subs:
                self._subs.remove(sub)

    def n_subscribers(self) -> int:
        with self._lock:
            return len(self._subs)

    def set_frame(self, jpeg: bytes) -> None:
        self._frame = jpeg

    def latest_frame(self) -> bytes | None:
        return self._frame
