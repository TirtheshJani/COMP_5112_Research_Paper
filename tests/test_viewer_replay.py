import importlib.util
from pathlib import Path

import numpy as np

from jigsaw.viewer.events import EventBus

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tests" / "data" / "events_sample.jsonl"
KEYS = {
    "frame": {"type", "t", "grid", "rvec", "tvec", "decision"},
    "announce": {"type", "row", "col", "turn", "text"},
    "give_up": {"type", "text"},
    "board": {"type", "placed"},
    "head": {"type", "pose"},
}


def _replay():
    spec = importlib.util.spec_from_file_location("replay_events", ROOT / "scripts" / "replay_events.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sample_follows_contract_v2_section_5():
    events = _replay().load_events(SAMPLE)
    assert 35 <= len(events) <= 45
    for e in events:
        assert set(e) == KEYS[e["type"]], e
        if e["type"] == "frame":
            d = e["decision"]
            if d["kind"] == "read":
                assert np.array(e["grid"]).shape == (4, 2)
                assert len(e["rvec"]) == 3 and len(e["tvec"]) == 3
                assert 0 <= d["row"] < 7 and 0 <= d["col"] < 5 and 0 <= d["turn"] < 4
            else:
                assert d["kind"] == "reject" and d["reason"]
                assert e["grid"] is None and e["rvec"] is None and e["tvec"] is None
        elif e["type"] == "announce":
            assert 0 <= e["row"] < 7 and 0 <= e["col"] < 5
        elif e["type"] == "head":
            assert len(e["pose"]) == 16
    kinds = {e["type"] for e in events}
    assert kinds == set(KEYS)
    ts = [e["t"] for e in events if e["type"] == "frame"]
    assert ts == sorted(ts)


def test_sample_grids_match_rendered_frames():
    rp = _replay()
    events = rp.load_events(SAMPLE)
    for i, e in enumerate(events):
        if e["type"] == "frame" and e["decision"]["kind"] == "read":
            jpeg, grid = rp.render_frame(e, seed=i)
            assert jpeg[:2] == b"\xff\xd8"
            np.testing.assert_allclose(grid, e["grid"], atol=1.0)


def test_replay_one_loop_publishes_everything_in_order():
    rp = _replay()
    events = rp.load_events(SAMPLE)
    bus = EventBus(maxlen=1000)
    sub = bus.subscribe()
    sleeps = []
    rp.replay(bus, events, rate=10, loops=2, sleep=sleeps.append)
    got = [next(sub) for _ in range(2 * len(events))]
    assert [g["type"] for g in got] == [e["type"] for e in events] * 2
    assert got[: len(events)][-1] == events[-1]
    t = [g["t"] for g in got if g["type"] == "frame"]
    assert all(b > a for a, b in zip(t, t[1:]))           # time keeps increasing across loops
    assert sleeps and all(abs(s - 0.1) < 1e-9 for s in sleeps)
    assert bus.latest_frame()[:2] == b"\xff\xd8"
