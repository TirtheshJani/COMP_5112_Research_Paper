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
from jigsaw.robot.reachy import ReachyRobot, connect, correct_k
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


class InPlaceMedia(StubMedia):
    """An SDK that writes every frame into one buffer and returns that same array each time."""

    def __init__(self, values):
        super().__init__()
        self.buf, self.values = img(0), list(values)

    def get_frame(self):
        if not self.values:
            raise RuntimeError("no more frames")
        self.buf[...] = self.values.pop(0)
        return self.buf


def test_frames_from_one_reused_buffer_are_new_and_stay_unchanged():
    frames = list(itertools.islice(ReachyRobot(StubMini(InPlaceMedia([1, 1, 2, 3])), pose).frames(), 3))
    assert [int(f.image[0, 0, 0]) for f in frames] == [1, 2, 3]       # read after the buffer was overwritten


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


def test_frames_do_not_count_time_the_consumer_spends_between_frames(caplog):
    clock = FakeClock()
    media = TickingMedia(clock, 0.25, [img(1), None, None, img(2)])
    it = ReachyRobot(StubMini(media), pose, clock=clock).frames()
    with caplog.at_level(logging.WARNING, logger="jigsaw.robot.reachy"):
        next(it)
        clock.t += 10.0                        # the caller is busy (an operator prompt) for 10 s
        assert int(next(it).image[0, 0, 0]) == 2
    assert not any("no new camera frame" in r.getMessage() for r in caplog.records)


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


# Camera intrinsics: the 720p correction (arithmetic only; no probe has measured it)

K_SDK_720 = np.array([[667.26921422, 0.0, 635.29201994],      # K the SDK gave at 1280 x 720, results/probes/p2.txt
                      [0.0, 556.41052461, 368.97888105],
                      [0.0, 0.0, 1.0]])


def test_correct_k_at_720_rows_scales_fy_and_moves_cy_only():
    K = correct_k(K_SDK_720, 720)
    assert K[1, 1] == pytest.approx(667.692629532, abs=1e-6)        # 1.2 * 556.41052461
    assert K[1, 2] == pytest.approx(370.774657260, abs=1e-6)        # (3.6 * 368.97888105 - 216) / 3
    assert K[0, 0] == K_SDK_720[0, 0] and K[0, 2] == K_SDK_720[0, 2]
    assert K[0, 1] == 0 and K[1, 0] == 0 and list(K[2]) == [0, 0, 1]
    assert K_SDK_720[1, 1] == 556.41052461                          # the input is not modified


def test_correct_k_keeps_a_centred_principal_point_centred():
    K = correct_k(np.array([[600.0, 0, 640], [0, 500, 360], [0, 0, 1]]), 720)
    assert np.allclose(K, [[600, 0, 640], [0, 600, 360], [0, 0, 1]])


@pytest.mark.parametrize("height", [1080, 2592, 4])
def test_correct_k_leaves_other_heights_untouched(height):
    assert np.array_equal(correct_k(K_SDK_720, height), K_SDK_720)


def test_frames_carry_the_corrected_k_at_720_rows():
    media = StubMedia(frames=[np.zeros((720, 1280, 3), np.uint8)])
    media.camera.K = K_SDK_720
    f = next(ReachyRobot(StubMini(media), pose).frames())
    assert np.array_equal(f.K, correct_k(K_SDK_720, 720))


def test_frames_at_other_heights_keep_the_sdk_k_and_log_that_once(caplog):
    media = StubMedia(frames=[img(1), img(2), img(3)])
    with caplog.at_level(logging.WARNING, logger="jigsaw.robot.reachy"):
        frames = list(itertools.islice(ReachyRobot(StubMini(media), pose).frames(), 3))
    assert all(np.array_equal(f.K, StubCamera.K) for f in frames)
    assert sum("uncorrected" in r.getMessage() for r in caplog.records) == 1


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


class BusyAfter(StubMini):
    """goto_target succeeds `n` times, then raises MoveBusyError."""

    def __init__(self, n):
        super().__init__()
        self.n = n

    def goto_target(self, head=None, **kw):
        if len(self.moves) >= self.n:
            raise MoveBusyError("a move is already running")
        super().goto_target(head=head, **kw)


@pytest.mark.parametrize("n, where", [(0, "head not moved"), (1, "head left at {'pitch': 10}"),
                                      (2, "head left at {'pitch': -6}")])
def test_move_busy_partway_through_a_nod_logs_where_the_head_was_left(caplog, n, where):
    mini = BusyAfter(n)
    with caplog.at_level(logging.WARNING, logger="jigsaw.robot.reachy"):
        ReachyRobot(mini, pose).nod()
    assert len(mini.moves) == n
    msgs = [r.getMessage() for r in caplog.records if "busy" in r.getMessage()]
    assert len(msgs) == 1 and where in msgs[0]


def test_other_motion_errors_are_raised():
    mini = StubMini()

    def broken(**kw):
        raise TimeoutError("no answer")
    mini.goto_target = broken
    with pytest.raises(TimeoutError):
        ReachyRobot(mini, pose).nod()


# Audio out (R9)

def fake_sleep(clock: FakeClock, slept: list):
    def sleep(s):
        slept.append(s)
        clock.t += s
    return sleep


def test_play_resamples_22050_to_16000_with_the_right_length_and_blocks():
    mini, clock, slept = StubMini(), FakeClock(), []
    robot = ReachyRobot(mini, pose, clock=clock, sleep=fake_sleep(clock, slept))
    pcm = np.sin(2 * np.pi * 440 * np.arange(11025) / 22050).astype(np.float32)   # 0.5 s
    robot.play(pcm, 22050)
    out = np.concatenate(mini.media.pushed)
    assert out.dtype == np.float32 and out.ndim == 1
    assert len(out) == 8000
    assert sum(slept) == pytest.approx(0.5)                            # blocks for the duration
    # still a 440 Hz tone after resampling
    spectrum = np.abs(np.fft.rfft(out))
    assert abs(np.argmax(spectrum) * 16000 / len(out) - 440) < 5


def test_play_at_the_output_rate_pushes_samples_unchanged():
    mini = StubMini()
    pcm = np.linspace(-0.5, 0.5, 1600).astype(np.float32)
    ReachyRobot(mini, pose).play(pcm, 16000)
    assert np.array_equal(np.concatenate(mini.media.pushed), pcm)


def test_is_playing_is_true_until_the_duration_has_passed():
    clock, seen = FakeClock(), []

    def sleep(s):                                   # play() sleeps once, for the whole duration
        seen.append(robot.is_playing())
        clock.t += s - 0.01
        seen.append(robot.is_playing())             # 10 ms before the end
        clock.t += 0.01
    robot = ReachyRobot(StubMini(), pose, clock=clock, sleep=sleep)
    assert robot.is_playing() is False
    robot.play(np.zeros(4800, np.float32), 16000)   # 0.3 s
    seen.append(robot.is_playing())
    assert seen == [True, True, False]


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


def test_connect_drains_stale_frames_and_audio_before_returning(monkeypatch):
    stale_audio = [np.full((320, 2), 0.1, np.float32) for _ in range(3)]
    media = StubMedia(frames=[img(k) for k in range(5)], audio=stale_audio)
    _fake_sdk(monkeypatch, lambda **kw: StubMini(media))
    robot = connect()
    assert media.frames == [] and media.audio == []
    assert robot.read() is None


class EndlessMedia(StubMedia):
    """An SDK that never returns None: a new frame and an audio chunk on every call."""

    def __init__(self):
        super().__init__()
        self.frame_reads = self.audio_reads = 0

    def get_frame(self):
        self.frame_reads += 1
        return img(self.frame_reads % 256)

    def get_audio_sample(self):
        self.audio_reads += 1
        return np.zeros((320, 2), np.float32)


def test_connect_drain_is_bounded_when_the_sdk_never_returns_none(monkeypatch):
    media = EndlessMedia()
    _fake_sdk(monkeypatch, lambda **kw: StubMini(media))
    connect()
    assert 1 < media.frame_reads <= 1 + reachy.DRAIN_MAX_READS          # 1 = the first frame connect waits for
    assert 0 < media.audio_reads <= reachy.DRAIN_MAX_READS


class SlowEndlessMedia(EndlessMedia):
    """Like the SDK when live data keeps arriving: every read waits about 10 ms and returns data."""

    def get_frame(self):
        time.sleep(0.01)
        return super().get_frame()

    def get_audio_sample(self):
        time.sleep(0.01)
        return super().get_audio_sample()


def test_connect_drain_also_stops_after_a_time_limit(monkeypatch):
    media = SlowEndlessMedia()
    _fake_sdk(monkeypatch, lambda **kw: StubMini(media))
    monkeypatch.setattr(reachy, "DRAIN_MAX_S", 0.05)
    connect()
    assert media.frame_reads <= 1 + 6 and media.audio_reads <= 6       # reads of 10 ms or more fit 0.05 s at most 5 times


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


def test_frames_wait_with_the_injected_sleep_not_the_real_one():
    clock, slept = FakeClock(), []
    media = StubMedia(frames=[img(1), None, None, img(2)])
    it = ReachyRobot(StubMini(media), pose, clock=clock, sleep=fake_sleep(clock, slept)).frames()
    next(it), next(it)
    assert slept == [0.005, 0.005]


def test_wait_for_frame_uses_the_injected_clock_and_sleep():
    clock, slept = FakeClock(), []
    robot = ReachyRobot(StubMini(StubMedia()), pose, clock=clock, sleep=fake_sleep(clock, slept))
    assert robot._wait_for_frame(1.0) is False
    assert sum(slept) >= 1.0 and set(slept) == {0.02}


def test_resample_of_a_signal_shorter_than_the_filter_keeps_its_level():
    out = reachy.resample(np.ones(10, np.float32), 48000, 16000)
    assert len(out) == 3
    assert out == pytest.approx(1.0, abs=1e-6)
