"""App loop (S6 A2 to A6) with RenderSource and the fakes. Nothing here moves a robot or plays sound."""
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import pytest

from jigsaw import app
from jigsaw.fakes import FakeAudioOut, FakeFrameSource, FakeGestures
from jigsaw.render import photograph, piece_back
from jigsaw.robot.sources import RenderSource
from jigsaw.types import Frame, Read, Reject
from jigsaw.voice.phrases import phrase_read, phrase_reject

ROOT = Path(__file__).resolve().parents[1]
SIZE = (640, 480)
K = np.array([[600.0, 0, 320], [0, 600.0, 240], [0, 0, 1]])


def silent(text):
    return np.zeros(8, np.float32), 16000


class Spoken:
    """synthesize stand-in that remembers the sentences."""

    def __init__(self):
        self.texts = []

    def __call__(self, text):
        self.texts.append(text)
        return silent(text)


class ListBus:
    def __init__(self, log=None):
        self.events, self.jpegs, self.log = [], [], log

    def publish(self, event):
        self.events.append(event)
        if self.log is not None:
            self.log.append(event["type"])

    def set_frame(self, jpeg):
        self.jpegs.append(jpeg)

    def of(self, kind):
        return [e for e in self.events if e["type"] == kind]


class Script:
    """Listener that returns one scripted command per poll (None when the script is exhausted)."""

    def __init__(self, commands):
        self.commands = list(commands)

    def poll(self):
        return self.commands.pop(0) if self.commands else None


def shot(r, c, angle, seed=0, grid=None, ppc=16):
    gray, alpha = piece_back(r, c, ppc, grid=grid)
    return photograph(gray, alpha, np.random.default_rng(seed), angle, size=SIZE)


def corrupted_frames(n, seed=1):
    grid = np.random.default_rng(seed).integers(0, 2, (72, 52)).astype(np.uint8)
    return [shot(2, 2, 10, seed=s, grid=grid) for s in range(n)]


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TimedSource:
    """Frames with given time stamps; the clock never runs behind the newest frame."""
    name = "timed"

    def __init__(self, images, times, clock, K=None, D=None):
        self.images = images if isinstance(images, list) else [images] * len(times)
        self.times, self.clock, self.K, self.D = times, clock, K, D

    def frames(self):
        for image, t in zip(self.images, self.times):
            self.clock.now = max(self.clock.now, t)
            yield Frame(image, t, self.K, self.D)

    def close(self):
        pass


def test_ten_frames_of_one_piece_give_one_play_and_one_nod():
    src = RenderSource(np.random.default_rng(0), [(3, 2)] * 10, angle_deg=90, size=SIZE)
    gestures, audio = FakeGestures(), FakeAudioOut()
    out = app.run(src, gestures, audio, synthesize=silent)
    assert len(audio.played) == 1 and gestures.calls == ["nod"]
    assert out["announced"] == [Read(3, 2, 1)] and out["gave_up"] == 0


def test_a_corrupted_piece_gives_no_announcement_and_one_shake():
    gestures, audio, spoken = FakeGestures(), FakeAudioOut(), Spoken()
    out = app.run(FakeFrameSource(corrupted_frames(20)), gestures, audio, synthesize=spoken)
    assert out["announced"] == [] and out["gave_up"] == 1
    assert gestures.calls == ["shake"] and len(audio.played) == 1
    assert not spoken.texts[0].startswith("Row")


class ScriptedReader:
    """PieceReader stand-in that returns the given decisions in order."""

    def __init__(self, decisions):
        self.decisions, self.last_grid = list(decisions), None

    def read(self, image):
        return self.decisions.pop(0)


def test_a_give_up_names_the_last_reject_reason_of_the_presentation(monkeypatch):
    # the 15th miss is a Read that has not settled; the sentence still names why the piece could not be read
    decisions = [Reject("no_window")] * 14 + [Read(3, 2, 1)]
    monkeypatch.setattr(app, "PieceReader", lambda: ScriptedReader(decisions))
    spoken = Spoken()
    out = app.run(FakeFrameSource([np.zeros((4, 4, 3), np.uint8)] * 15), FakeGestures(), FakeAudioOut(),
                  synthesize=spoken)
    assert out["gave_up"] == 1 and spoken.texts == [phrase_reject("no_window")]


def test_an_empty_view_clears_the_reject_reason(monkeypatch):
    decisions = [Reject("no_window"), Reject("no_grid")] + [Read(3, 2, 1), Read(1, 1, 0)] * 8
    monkeypatch.setattr(app, "PieceReader", lambda: ScriptedReader(decisions))
    spoken = Spoken()
    out = app.run(FakeFrameSource([np.zeros((4, 4, 3), np.uint8)] * 18), FakeGestures(), FakeAudioOut(),
                  synthesize=spoken)
    assert out["gave_up"] == 1 and spoken.texts == [phrase_reject("")]


def test_events_follow_the_contract_and_are_json():
    mat = np.full((SIZE[1], SIZE[0], 3), (70, 150, 60), np.uint8)
    images = [shot(3, 2, 90, seed=s) for s in range(4)] + [mat]
    clock, bus = Clock(), ListBus()
    app.run(TimedSource(images, [0.0, 0.1, 0.2, 10.0, 10.1], clock, K=K, D=np.zeros(5)), FakeGestures(), FakeAudioOut(),
            bus=bus, clock=clock, synthesize=silent)
    for e in bus.events:
        json.dumps(e)
    assert [e["type"] for e in bus.events] == ["board", "frame", "frame", "frame", "announce", "board", "frame", "frame"]
    assert bus.events[0] == {"type": "board", "placed": []}
    frames = bus.of("frame")
    assert len(bus.jpegs) == 5 and all(j[:2] == b"\xff\xd8" for j in bus.jpegs)
    first = frames[0]
    assert set(first) == {"type", "t", "grid", "rvec", "tvec", "decision"}
    assert first["decision"] == {"kind": "read", "row": 3, "col": 2, "turn": 1}
    assert len(first["grid"]) == 4 and all(0 <= x <= SIZE[0] and 0 <= y <= SIZE[1] for x, y in first["grid"])
    assert len(first["rvec"]) == 3 and len(first["tvec"]) == 3 and first["tvec"][2] > 0
    assert bus.of("announce") == [{"type": "announce", "row": 3, "col": 2, "turn": 1, "text": phrase_read(Read(3, 2, 1))}]
    assert bus.of("board")[-1] == {"type": "board", "placed": [[3, 2]]}
    assert frames[-1] == {"type": "frame", "t": 10.1, "grid": None, "rvec": None, "tvec": None,
                          "decision": {"kind": "reject", "reason": "no_grid"}}


def test_grid_corners_come_from_the_homography():
    images = [shot(3, 2, 90, seed=s) for s in range(1)]
    bus = ListBus()
    app.run(FakeFrameSource(images), FakeGestures(), FakeAudioOut(), bus=bus, synthesize=silent)
    from jigsaw.reader import PieceReader
    reader = PieceReader()
    reader.read(images[0])
    g = reader.last_grid
    h, w = g.cells.shape
    p = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float) @ g.H.T
    expected = p[:, :2] / p[:, 2:]
    assert np.allclose(bus.of("frame")[0]["grid"], expected, atol=0.1)
    assert bus.of("frame")[0]["rvec"] is None     # no K, no pose


def test_order_is_publish_then_speak_then_gesture():
    log = []

    class Audio(FakeAudioOut):
        def play(self, pcm, rate):
            log.append("play")

    class Gestures(FakeGestures):
        def nod(self):
            log.append("nod")

        def shake(self):
            log.append("shake")

    images = [shot(3, 2, 90, seed=s) for s in range(3)]
    app.run(FakeFrameSource(images), Gestures(), Audio(), bus=ListBus(log), synthesize=silent)
    assert [x for x in log if x != "frame"] == ["board", "announce", "board", "play", "nod"]
    log.clear()
    app.run(FakeFrameSource(corrupted_frames(15)), Gestures(), Audio(), bus=ListBus(log), synthesize=silent)
    assert [x for x in log if x != "frame"] == ["board", "give_up", "play", "shake"]


def test_frames_during_speech_motion_and_settling_are_dropped():
    clock = Clock()

    class Audio(FakeAudioOut):
        def play(self, pcm, rate):
            clock.now += 2.0

    class Gestures(FakeGestures):
        def nod(self):
            clock.now += 1.0

    end = 0.2 + 2.0 + 1.0                                   # speech 0.2 to 2.2, nod 2.2 to 3.2
    times = [0.0, 0.1, 0.2, 1.0, 2.5, end + app.SETTLE_S - 0.1, end + app.SETTLE_S + 0.1, end + app.SETTLE_S + 0.2]
    bus = ListBus()
    out = app.run(TimedSource(shot(3, 2, 90), times, clock), Gestures(), Audio(), bus=bus, clock=clock,
                  synthesize=silent)
    assert [e["t"] for e in bus.of("frame")] == [0.0, 0.1, 0.2, times[6], times[7]]
    assert out["dropped"] == 3 and out["frames"] == 8


def test_frames_while_audio_is_playing_are_dropped():
    class Busy(FakeAudioOut):
        def is_playing(self):
            return True

    bus = ListBus()
    out = app.run(FakeFrameSource([shot(3, 2, 90)] * 5), FakeGestures(), Busy(), bus=bus, synthesize=silent)
    assert bus.of("frame") == [] and out["dropped"] == 5


def test_max_frames_bounds_the_run():
    bus = ListBus()
    out = app.run(FakeFrameSource([shot(3, 2, 90)] * 10), FakeGestures(), FakeAudioOut(), bus=bus, max_frames=2,
                  synthesize=silent)
    assert out["frames"] == 2 and len(bus.of("frame")) == 2 and out["announced"] == []


def test_stop_ends_the_loop():
    bus = ListBus()
    out = app.run(FakeFrameSource([shot(3, 2, 90)] * 10), FakeGestures(), FakeAudioOut(), bus=bus,
                  listener=Script([None, None, "stop"]), synthesize=silent)
    assert out["frames"] == 3 and len(bus.of("frame")) == 2


def test_again_repeats_the_last_announcement():
    spoken = Spoken()
    gestures = FakeGestures()
    app.run(FakeFrameSource([shot(3, 2, 90)] * 4), gestures, FakeAudioOut(), listener=Script([None] * 3 + ["again"]),
            synthesize=spoken)
    assert spoken.texts == [phrase_read(Read(3, 2, 1))] * 2 and gestures.calls == ["nod"]


def test_next_lets_the_same_piece_be_announced_again():
    clock = Clock()
    times = [0.1 * i for i in range(3)] + [10 + 0.1 * i for i in range(4)]
    out = app.run(TimedSource(shot(3, 2, 90), times, clock), FakeGestures(), FakeAudioOut(), clock=clock,
                  listener=Script([None] * 3 + ["next"]), synthesize=silent)
    assert out["announced"] == [Read(3, 2, 1)] * 2


def test_without_next_the_same_piece_is_not_announced_again():
    clock = Clock()
    times = [0.1 * i for i in range(3)] + [10 + 0.1 * i for i in range(4)]
    out = app.run(TimedSource(shot(3, 2, 90), times, clock), FakeGestures(), FakeAudioOut(), clock=clock,
                  synthesize=silent)
    assert out["announced"] == [Read(3, 2, 1)]


def test_ask_answers_from_the_current_frame():
    gestures = FakeGestures()
    out = app.run(FakeFrameSource([shot(3, 2, 90)]), gestures, FakeAudioOut(), listener=Script(["ask"]),
                  synthesize=silent)
    assert out["announced"] == [Read(3, 2, 1)] and gestures.calls == ["nod"]
    gestures, spoken = FakeGestures(), Spoken()
    out = app.run(FakeFrameSource(corrupted_frames(1)), gestures, FakeAudioOut(), listener=Script(["ask"]),
                  synthesize=spoken)
    assert out["announced"] == [] and out["gave_up"] == 1 and gestures.calls == ["shake"]


def test_ask_then_steady_reads_do_not_announce_twice():
    clock = Clock()
    out = app.run(TimedSource(shot(3, 2, 90), [0.0] + [5 + 0.1 * i for i in range(5)], clock), FakeGestures(),
                  FakeAudioOut(), clock=clock, listener=Script(["ask"]), synthesize=silent)
    assert out["announced"] == [Read(3, 2, 1)]


# A3 gate -------------------------------------------------------------------------------------------------------

GATE_N = 200
GATE_MAX_FRAMES = 20           # more than Stable's miss_limit, so an unreadable presentation gives up
FINDINGS = ROOT / "results" / "findings"


class Presentation:
    """One piece held still: RenderSource frames until the robot answers (nod or shake)."""
    name = "presentation"

    def __init__(self, inner):
        self.inner, self.images, self.answered = inner, [], False

    def frames(self):
        for f in self.inner.frames():
            if self.answered:
                return
            self.images.append(f.image)
            yield f

    def close(self):
        self.inner.close()


class Answering(FakeGestures):
    def __init__(self, presentation):
        super().__init__()
        self.p = presentation

    def nod(self):
        super().nod()
        self.p.answered = True

    def shake(self):
        super().shake()
        self.p.answered = True


def save_finding(i, truth, announced, cond, images):
    folder = FINDINGS / f"app_gate_{i:03d}"
    folder.mkdir(parents=True, exist_ok=True)
    for n, img in enumerate(images):
        cv2.imwrite(str(folder / f"frame_{n:02d}.png"), img)
    (folder / "decision.json").write_text(json.dumps({"truth": truth.__dict__, "announced": [a.__dict__ for a in announced],
                                                     "condition": cond}, indent=1, default=str))
    return folder


def test_gate_200_presentations_never_announce_a_wrong_piece_or_turn():
    rng = np.random.default_rng(20261123)
    counts, findings = Counter(), []
    for i in range(GATE_N):
        r, c, k = int(rng.integers(7)), int(rng.integers(5)), int(rng.integers(4))
        cond = dict(angle_deg=90 * k + float(rng.uniform(-35, 35)), tilt=float(rng.uniform(0, 0.08)),
                    blur=float(rng.uniform(0, 1.2)), noise=float(rng.uniform(0, 8)), light=float(rng.uniform(0, 1)),
                    finger=bool(rng.random() < 0.3), background=str(rng.choice(["mat"] * 18 + ["clutter", "plain"])))
        ppc = float(rng.uniform(10, 18))
        p = Presentation(RenderSource(rng, [(r, c)] * GATE_MAX_FRAMES, px_per_cell=ppc, size=SIZE, **cond))
        gestures, bus = Answering(p), ListBus()
        out = app.run(p, gestures, FakeAudioOut(), bus=bus, synthesize=silent)
        truth = Read(r, c, k)
        # every gesture is accounted for: a nod per announcement, a shake per give-up, at most one answer
        assert gestures.calls.count("nod") == len(out["announced"]), (i, gestures.calls, out)
        assert gestures.calls.count("shake") == out["gave_up"] and len(gestures.calls) <= 1, (i, gestures.calls, out)
        if any(a != truth for a in out["announced"]):
            counts["wrong"] += 1
            findings.append(save_finding(i, truth, out["announced"], {**cond, "px_per_cell": ppc}, p.images))
        elif out["announced"]:
            counts["correct"] += 1
        elif out["gave_up"]:
            counts["given_up"] += 1
        else:
            # Stable answers within miss_limit < GATE_MAX_FRAMES frames unless an empty view (no_grid) resets it
            reasons = [e["decision"].get("reason") for e in bus.of("frame")]
            assert "no_grid" in reasons, (i, reasons)
            counts["silent"] += 1
    print(f"\nA3 gate over {GATE_N} presentations: correct {counts['correct']}, given up {counts['given_up']}, "
          f"silent (no_grid) {counts['silent']}, wrong {counts['wrong']}")
    assert counts["wrong"] == 0, f"WRONG ANNOUNCE: {findings}"
    # not a tuned threshold: it only stops a gate that announces nothing from passing (observed 187 of 200,
    # Wilson 95 percent interval 0.892 to 0.962, so the floor of 0.75 is far below anything this code produces)
    assert counts["correct"] >= 150, counts


# scripts/run_demo.py (A7) ---------------------------------------------------------------------------------------

def load_run_demo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_demo", ROOT / "scripts" / "run_demo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def demo(monkeypatch):
    """run_demo with silent synthesis; connecting to a robot fails the test unless a test replaces it."""
    from jigsaw.robot import reachy
    from jigsaw.voice import tts

    def no_robot(host=None):
        raise AssertionError("the robot path was constructed")

    monkeypatch.setattr(tts, "synthesize", silent)
    monkeypatch.setattr(reachy, "connect", no_robot)
    return load_run_demo()


def test_run_demo_render_runs_end_to_end_without_a_robot(demo):
    gestures, audio = FakeGestures(), FakeAudioOut()
    out = demo.main(["--source", "render", "--max-frames", "12", "--seed", "3"], gestures=gestures, audio_out=audio)
    src = demo.render_source(3)
    truth = {Read(r, c, round(src.kwargs["angle_deg"] / 90) % 4) for r, c in src.pieces[:12]}
    assert out["frames"] == 12 and out["announced"] and set(out["announced"]) <= truth
    assert gestures.calls.count("nod") == len(out["announced"]) == len(audio.played)


def test_run_demo_replay_runs_end_to_end_without_a_robot(demo, tmp_path):
    for n in range(4):
        cv2.imwrite(str(tmp_path / f"a_{n}.png"), shot(3, 2, 90, seed=n))
        cv2.imwrite(str(tmp_path / f"b_{n}.png"), shot(1, 4, 180, seed=n))
    gestures = FakeGestures()
    out = demo.main(["--source", "replay", "--frames", str(tmp_path)], gestures=gestures, audio_out=FakeAudioOut())
    assert out["frames"] == 8 and out["announced"][0] == Read(3, 2, 1) and gestures.calls[0] == "nod"


def test_run_demo_robot_path_uses_connect_and_the_listener(demo, monkeypatch):
    from jigsaw.robot import reachy
    from jigsaw.voice import stt

    class Robot(FakeGestures, FakeAudioOut):
        name, rate = "robot", 16000

        def __init__(self):
            FakeGestures.__init__(self)
            FakeAudioOut.__init__(self)
            self.closed = False

        def frames(self):
            for n in range(5):
                yield Frame(shot(3, 2, 90, seed=n), float(n), None, None)

        def close(self):
            self.closed = True

        def read(self):
            return None

    robot, hosts, listeners = Robot(), [], []

    class Listener:
        def __init__(self, audio_in, is_muted):
            listeners.append((audio_in, is_muted))

        def warm(self):
            pass

        def poll(self):
            return None

        def close(self):
            listeners.append("closed")

    monkeypatch.setattr(reachy, "connect", lambda host=None: hosts.append(host) or robot)
    monkeypatch.setattr(stt, "CommandListener", Listener)
    out = demo.main(["--source", "robot", "--host", "10.0.0.100"])
    assert hosts == ["10.0.0.100"] and robot.closed and robot.calls == ["nod"] and len(robot.played) == 1
    assert listeners[0][0] is robot and listeners[-1] == "closed" and out["announced"] == [Read(3, 2, 1)]
    robot.closed, listeners[:] = False, []
    demo.main(["--source", "robot", "--no-voice-in"])
    assert listeners == []


def test_run_demo_viewer_publishes_to_an_event_bus(demo, monkeypatch):
    from jigsaw.viewer import server
    buses = []
    monkeypatch.setattr(server, "serve", lambda bus, **kw: buses.append(bus.subscribe()))
    demo.main(["--source", "render", "--max-frames", "3", "--viewer"], gestures=FakeGestures(), audio_out=FakeAudioOut())
    sub = buses[0]
    kinds = [sub.items.popleft()["type"] for _ in range(len(sub.items))]
    assert kinds[:2] == ["board", "frame"] and "announce" in kinds


def test_a_dropped_frame_ends_the_run_of_equal_reads(monkeypatch):
    # two reads, a dropped frame (audio playing), then one read: not three in a row, so no announcement
    decisions = [Read(3, 2, 1)] * 3
    monkeypatch.setattr(app, "PieceReader", lambda: ScriptedReader(decisions))
    audio = FakeAudioOut()
    states = iter([False, False, True, False])
    audio.is_playing = lambda: next(states)
    out = app.run(FakeFrameSource([np.zeros((4, 4, 3), np.uint8)] * 4), FakeGestures(), audio, synthesize=silent)
    assert out["dropped"] == 1 and out["announced"] == []


def test_an_ask_that_gave_up_stops_stable_giving_up_again(monkeypatch):
    decisions = [Reject("no_window")] * 5 + [Reject("low_contrast")] * 12
    monkeypatch.setattr(app, "PieceReader", lambda: ScriptedReader(decisions))
    spoken = Spoken()
    listener = Script([None] * 5 + ["ask"])
    out = app.run(FakeFrameSource([np.zeros((4, 4, 3), np.uint8)] * 17), FakeGestures(), FakeAudioOut(),
                  listener=listener, synthesize=spoken, clock=lambda: -1e9)
    assert out["gave_up"] == 1 and out["dropped"] == 0
