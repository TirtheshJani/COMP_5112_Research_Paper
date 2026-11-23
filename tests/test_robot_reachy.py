"""ReachyRobot and connect() against a stub mini object (S3, R6 to R11). No robot, no reachy_mini."""
import itertools
import logging
import subprocess
import sys
import threading
import time
import types

import numpy as np
import pytest

from jigsaw.robot import reachy
from jigsaw.robot.reachy import ReachyRobot, connect
from jigsaw.types import AudioIn, AudioOut, Frame, FrameSource, Gestures


class MoveBusyError(RuntimeError):
    """Same class name as reachy_mini.io.protocol.MoveBusyError."""


class StubCamera:
    K = np.eye(3) * 2.0
    D = np.arange(5, dtype=float)


class StubMedia:
    def __init__(self, frames=(), audio=()):
        self.camera = StubCamera()
        self.frames, self.audio = list(frames), list(audio)
        self.calls: list[str] = []
        self.pushed: list[np.ndarray] = []

    def get_frame(self):
        return self.frames.pop(0) if self.frames else None

    def start_playing(self):
        self.calls.append("start_playing")

    def stop_playing(self):
        self.calls.append("stop_playing")

    def start_recording(self):
        self.calls.append("start_recording")

    def stop_recording(self):
        self.calls.append("stop_recording")

    def get_output_audio_samplerate(self):
        return 16000

    def get_input_audio_samplerate(self):
        return 16000

    def push_audio_sample(self, data):
        self.pushed.append(np.array(data))

    def get_audio_sample(self):
        return self.audio.pop(0) if self.audio else None


class StubMini:
    def __init__(self, media=None, busy=False):
        self.media = media or StubMedia()
        self.moves: list[tuple[dict, float]] = []
        self.busy = busy
        self.exited = 0

    def goto_target(self, head=None, antennas=None, duration=0.5, method=None, body_yaw=0.0):
        if self.busy:
            raise MoveBusyError("a move is already running")
        self.moves.append((head, duration))

    def __exit__(self, *exc):
        self.exited += 1


def pose(**kw):
    return dict(kw)          # stands in for reachy_mini.utils.create_head_pose


def img(v):
    return np.full((4, 6, 3), v, np.uint8)


# Protocols and import hygiene

def test_robot_satisfies_all_four_protocols():
    robot = ReachyRobot(StubMini(), pose)
    for proto in (FrameSource, Gestures, AudioOut, AudioIn):
        assert isinstance(robot, proto)
    assert robot.rate == 16000


def test_importing_jigsaw_robot_does_not_import_reachy_mini():
    code = "import sys, jigsaw.robot.reachy, jigsaw.robot.sources; print('reachy_mini' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


def test_start_playing_and_start_recording_are_called_once_at_construction():
    mini = StubMini()
    robot = ReachyRobot(mini, pose)
    robot.play(np.zeros(160, np.float32), 16000)
    robot.read()
    assert mini.media.calls.count("start_playing") == 1
    assert mini.media.calls.count("start_recording") == 1


# Frames (R6)

def test_frames_skip_none_and_carry_bgr_image_time_k_and_d():
    media = StubMedia(frames=[None, img(1), None, None, img(2), img(3)])
    robot = ReachyRobot(StubMini(media), pose)
    it = robot.frames()
    frames = [next(it) for _ in range(3)]
    assert [int(f.image[0, 0, 0]) for f in frames] == [1, 2, 3]
    assert all(isinstance(f, Frame) for f in frames)
    assert np.array_equal(frames[0].K, StubCamera.K) and np.array_equal(frames[0].D, StubCamera.D)
    assert frames[0].image is not None and frames[0].image.dtype == np.uint8
    ts = [f.t for f in frames]
    assert ts == sorted(ts)


class FakeClock:
    def __init__(self, t: float = 100.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


class TickingMedia(StubMedia):
    """A camera whose every get_frame() call takes `step` seconds of the injected clock."""

    def __init__(self, clock: FakeClock, step: float, frames):
        super().__init__(frames=frames)
        self.clock, self.step = clock, step

    def get_frame(self):
        self.clock.t += self.step
        return super().get_frame()


def test_frames_skip_a_frame_identical_to_the_previous_one():
    media = StubMedia(frames=[img(1), img(1), None, img(1), img(2), img(2).copy(), img(1)])
    frames = list(itertools.islice(ReachyRobot(StubMini(media), pose).frames(), 3))
    assert [int(f.image[0, 0, 0]) for f in frames] == [1, 2, 1]


@pytest.mark.parametrize("n_nothing_new, n_warnings", [(7, 0), (8, 1), (16, 2)])
def test_frames_warn_every_2_s_without_a_new_frame_and_keep_waiting(caplog, n_nothing_new, n_warnings):
    clock = FakeClock()
    nothing_new = [None if k % 2 else img(1) for k in range(n_nothing_new)]     # None and repeats alike
    media = TickingMedia(clock, 0.25, [img(1), *nothing_new, img(2)])
    it = ReachyRobot(StubMini(media), pose, clock=clock).frames()
    with caplog.at_level(logging.WARNING, logger="jigsaw.robot.reachy"):
        first, second = next(it), next(it)
    assert int(second.image[0, 0, 0]) == 2
    assert second.t - first.t == pytest.approx(0.25 * (n_nothing_new + 1))      # Frame.t comes from the clock
    assert sum("no new camera frame" in r.getMessage() for r in caplog.records) == n_warnings


def test_frames_have_none_intrinsics_when_the_camera_cannot_give_them():
    class NoIntrinsics:
        @property
        def K(self):
            raise RuntimeError("resolution not set")
        D = None

    media = StubMedia(frames=[img(5)])
    media.camera = NoIntrinsics()
    f = next(ReachyRobot(StubMini(media), pose).frames())
    assert f.K is None and f.D is None


def test_close_stops_frames_and_releases_the_robot_once():
    mini = StubMini(StubMedia(frames=[img(1)]))
    robot = ReachyRobot(mini, pose)
    it = robot.frames()
    next(it)
    threading.Timer(0.05, robot.close).start()
    assert list(it) == []                 # get_frame returns None from here on; close ends the loop
    robot.close()
    assert mini.exited == 1
    assert "stop_recording" in mini.media.calls and "stop_playing" in mini.media.calls


# Gestures (R7)

@pytest.mark.parametrize("gesture, axis", [("nod", "pitch"), ("shake", "yaw")])
def test_gesture_stays_small_short_and_ends_at_neutral(gesture, axis):
    mini = StubMini()
    getattr(ReachyRobot(mini, pose), gesture)()
    heads = [h for h, _ in mini.moves]
    assert len(heads) >= 2
    assert all(set(h) <= {"pitch", "yaw", "degrees"} for h in heads)
    assert all(h.get("degrees", True) for h in heads)
    assert all(abs(h.get("pitch", 0)) <= 12 and abs(h.get("yaw", 0)) <= 12 for h in heads)
    assert any(abs(h.get(axis, 0)) > 3 for h in heads)                     # it visibly moves on its axis
    other = "yaw" if axis == "pitch" else "pitch"
    assert all(h.get(other, 0) == 0 for h in heads)
    assert heads[-1].get("pitch", 0) == 0 and heads[-1].get("yaw", 0) == 0  # back to neutral
    assert sum(d for _, d in mini.moves) < 1.5


def test_move_busy_is_logged_not_raised(caplog):
    robot = ReachyRobot(StubMini(busy=True), pose)
    with caplog.at_level(logging.WARNING, logger="jigsaw.robot.reachy"):
        robot.nod()
        robot.shake()
    assert sum("busy" in r.getMessage().lower() for r in caplog.records) == 2


def test_other_motion_errors_are_raised():
    mini = StubMini()

    def broken(**kw):
        raise TimeoutError("no answer")
    mini.goto_target = broken
    with pytest.raises(TimeoutError):
        ReachyRobot(mini, pose).nod()


# Audio out (R9)

def test_play_resamples_22050_to_16000_with_the_right_length_and_blocks():
    mini = StubMini()
    robot = ReachyRobot(mini, pose)
    pcm = np.sin(2 * np.pi * 440 * np.arange(11025) / 22050).astype(np.float32)   # 0.5 s
    t0 = time.monotonic()
    robot.play(pcm, 22050)
    elapsed = time.monotonic() - t0
    out = np.concatenate(mini.media.pushed)
    assert out.dtype == np.float32 and out.ndim == 1
    assert len(out) == 8000
    assert 0.45 <= elapsed < 0.8
    # still a 440 Hz tone after resampling
    spectrum = np.abs(np.fft.rfft(out))
    assert abs(np.argmax(spectrum) * 16000 / len(out) - 440) < 5


def test_play_at_the_output_rate_pushes_samples_unchanged():
    mini = StubMini()
    pcm = np.linspace(-0.5, 0.5, 1600).astype(np.float32)
    ReachyRobot(mini, pose).play(pcm, 16000)
    assert np.array_equal(np.concatenate(mini.media.pushed), pcm)


def test_is_playing_is_true_until_the_duration_has_passed():
    robot = ReachyRobot(StubMini(), pose)
    seen = []
    t = threading.Thread(target=robot.play, args=(np.zeros(4800, np.float32), 16000))   # 0.3 s
    assert robot.is_playing() is False
    t.start()
    time.sleep(0.1)
    seen.append(robot.is_playing())
    t.join()
    seen.append(robot.is_playing())
    assert seen == [True, False]


def test_play_rejects_stereo():
    with pytest.raises(ValueError):
        ReachyRobot(StubMini(), pose).play(np.zeros((100, 2), np.float32), 16000)


# Audio in (R10)

def test_read_returns_mono_float32_or_none():
    stereo = np.column_stack([np.full(320, 0.2), np.full(320, 0.4)]).astype(np.float32)
    robot = ReachyRobot(StubMini(StubMedia(audio=[None, stereo])), pose)
    assert robot.read() is None
    chunk = robot.read()
    assert chunk.dtype == np.float32 and chunk.shape == (320,)
    assert np.allclose(chunk, 0.3)
    assert robot.read() is None


# connect (R11)

def _fake_sdk(monkeypatch, factory):
    sdk = types.ModuleType("reachy_mini")
    sdk.ReachyMini = factory
    utils = types.ModuleType("reachy_mini.utils")
    utils.create_head_pose = pose
    monkeypatch.setitem(sys.modules, "reachy_mini", sdk)
    monkeypatch.setitem(sys.modules, "reachy_mini.utils", utils)


def test_failed_connect_names_power_wifi_and_conversation_app(monkeypatch):
    def refuse(**kw):
        raise ConnectionError("could not reach daemon")
    _fake_sdk(monkeypatch, refuse)
    with pytest.raises(ConnectionError) as err:
        connect("10.0.0.7")
    msg = str(err.value).lower()
    assert "10.0.0.7" in msg and "power" in msg and "wi-fi" in msg and "conversation app" in msg
    assert "could not reach daemon" in msg


def test_connect_without_camera_frames_fails_with_the_same_advice(monkeypatch):
    made = []

    def factory(**kw):
        made.append(StubMini(StubMedia(frames=[])))
        return made[-1]
    _fake_sdk(monkeypatch, factory)
    monkeypatch.setattr(reachy, "FIRST_FRAME_TIMEOUT_S", 0.2)
    with pytest.raises(ConnectionError) as err:
        connect()
    assert "conversation app" in str(err.value).lower()
    assert made[0].exited == 1                                               # robot released


def test_connect_passes_host_and_returns_a_robot(monkeypatch):
    seen = []

    def factory(**kw):
        seen.append(kw)
        return StubMini(StubMedia(frames=[img(9)]))
    _fake_sdk(monkeypatch, factory)
    robot = connect("10.0.0.100")
    assert isinstance(robot, ReachyRobot)
    assert seen == [{"connection_mode": "network", "host": "10.0.0.100"}]
    seen.clear()
    connect()
    assert seen == [{}]
