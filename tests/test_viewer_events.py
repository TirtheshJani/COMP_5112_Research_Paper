import threading
import time

from jigsaw.viewer.events import EventBus


def test_two_subscribers_both_receive_in_order():
    bus = EventBus()
    a, b = bus.subscribe(), bus.subscribe()
    for i in range(3):
        bus.publish({"type": "board", "placed": [], "i": i})
    assert [next(a)["i"] for _ in range(3)] == [0, 1, 2]
    assert [next(b)["i"] for _ in range(3)] == [0, 1, 2]


def test_slow_subscriber_drops_oldest_and_does_not_block():
    bus = EventBus(maxlen=100)
    slow = bus.subscribe()
    t0 = time.perf_counter()
    for i in range(250):
        bus.publish({"i": i})
    assert time.perf_counter() - t0 < 0.25
    got = [next(slow)["i"] for _ in range(100)]
    assert got == list(range(150, 250))


def test_publish_takes_under_1_ms():
    bus = EventBus()
    subs = [bus.subscribe() for _ in range(5)]
    n = 1000
    t0 = time.perf_counter()
    for i in range(n):
        bus.publish({"type": "frame", "t": i})
    assert (time.perf_counter() - t0) / n < 1e-3
    assert len(subs) == 5


def test_subscriber_blocks_until_publish_from_other_thread():
    bus = EventBus()
    sub = bus.subscribe()
    threading.Timer(0.05, bus.publish, args=({"type": "give_up", "text": "x"},)).start()
    assert next(sub)["type"] == "give_up"


def test_heartbeat_yields_none_when_idle():
    bus = EventBus()
    sub = bus.subscribe(heartbeat=0.01)
    assert next(sub) is None


def test_closed_subscriber_is_removed():
    bus = EventBus()
    sub = bus.subscribe()
    assert bus.n_subscribers() == 1
    sub.close()
    assert bus.n_subscribers() == 0


def test_frame_store():
    bus = EventBus()
    assert bus.latest_frame() is None
    bus.set_frame(b"\xff\xd8abc")
    assert bus.latest_frame() == b"\xff\xd8abc"
