"""In-process event bus between the app loop (publisher) and viewer clients (subscribers).

publish never blocks: each subscriber has its own bounded queue. When a slow client's queue is full,
its oldest frame event is dropped first, so board, announce, give_up and head events are kept as long
as there are frames to drop. The bus remembers the last board, the last spoken sentence (announce or
give_up, cleared by an empty board) and the last head pose, and replays them to each new subscriber,
so a page opened or reconnected mid-demo shows the current board.

Events are the dicts of CONTRACTS section 5. They are shared between subscribers and serialised later,
so the publisher must not change an event after publishing it. The latest camera JPEG is kept apart
from the events and fetched by the page on each frame event.
"""
import threading
from collections import deque


class Subscription:
    """Iterator over one client's events. close() unregisters it, also before the first next()."""

    def __init__(self, bus: "EventBus", maxlen: int, heartbeat: float | None):
        self._bus = bus
        self._maxlen = maxlen
        self._heartbeat = heartbeat
        self.items: deque = deque()
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

    def _push(self, event: dict) -> None:
        with self.cond:
            if len(self.items) >= self._maxlen:
                frame = next((e for e in self.items if e.get("type") == "frame"), None)
                if frame is not None:
                    self.items.remove(frame)
                else:
                    self.items.popleft()
            self.items.append(event)
            self.cond.notify()


class EventBus:
    def __init__(self, maxlen: int = 100):
        self._maxlen = maxlen
        self._subs: list[Subscription] = []
        self._lock = threading.Lock()
        self._frame: bytes | None = None
        self._state: dict[str, dict] = {}     # "board", "status", "head": last event of each

    def publish(self, event: dict) -> None:
        kind = event.get("type")
        with self._lock:
            if kind == "board":
                self._state["board"] = event
                if not event["placed"]:
                    self._state.pop("status", None)
            elif kind in ("announce", "give_up"):
                self._state["status"] = event
            elif kind == "head":
                self._state["head"] = event
            subs = list(self._subs)
        for sub in subs:
            sub._push(event)

    def subscribe(self, heartbeat: float | None = None) -> Subscription:
        """Register a client now and return its event iterator, starting with the remembered state.

        With heartbeat (seconds) the iterator yields None after that long without an event, so a server
        can write a keep-alive and notice a closed connection. Without it, next() waits for an event.
        """
        sub = Subscription(self, self._maxlen, heartbeat)
        with self._lock:
            for key in ("board", "status", "head"):
                if key in self._state:
                    sub._push(self._state[key])
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
