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
    assert time.perf_counter() - t0 < 1.0
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
    assert bus.n_subscribers() == len(subs)


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


ANNOUNCE = {"type": "announce", "row": 3, "col": 1, "turn": 2, "text": "Row 4, column 2."}
BOARD = {"type": "board", "placed": [[3, 1]]}
HEAD = {"type": "head", "pose": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}


def _frame(t):
    return {"type": "frame", "t": t, "grid": None, "rvec": None, "tvec": None, "decision": {"kind": "reject", "reason": "no_grid"}}


def test_new_subscriber_first_gets_current_board_status_and_head():
    bus = EventBus()
    for e in (ANNOUNCE, BOARD, HEAD, _frame(1.0)):
        bus.publish(e)
    late = bus.subscribe(heartbeat=0.01)
    assert [next(late) for _ in range(4)] == [BOARD, ANNOUNCE, HEAD, None]


def test_empty_board_clears_remembered_status():
    bus = EventBus()
    bus.publish(ANNOUNCE)
    bus.publish({"type": "give_up", "text": "Show me again."})
    bus.publish({"type": "board", "placed": []})
    late = bus.subscribe(heartbeat=0.01)
    assert [next(late), next(late)] == [{"type": "board", "placed": []}, None]


def test_full_queue_drops_frames_before_other_events():
    bus = EventBus(maxlen=5)
    sub = bus.subscribe()
    bus.publish(ANNOUNCE)
    for t in range(10):
        bus.publish(_frame(float(t)))
    got = [next(sub) for _ in range(5)]
    assert got[0] == ANNOUNCE
    assert [g["t"] for g in got[1:]] == [6.0, 7.0, 8.0, 9.0]
