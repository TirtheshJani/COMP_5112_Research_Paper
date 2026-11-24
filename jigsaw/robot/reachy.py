"""The Reachy Mini Wireless behind the four Protocols of jigsaw.types (CONTRACTS.md section 3, S3 R6 to R11).

connect(host) returns a ReachyRobot that is a FrameSource, Gestures, AudioOut and AudioIn. This is the
only module that calls goto_target and push_audio_sample (CLAUDE.md rule 6). reachy_mini is imported
inside connect(), so `import jigsaw.robot.reachy` works without the SDK.

SDK facts used here, from reachy-mini 1.15.0:
- media.get_frame() returns (H, W, 3) uint8 BGR or None; the WebRTC client asks GStreamer for
  format=BGR and converts nothing (media/webrtc_client_gstreamer.py:170, read() at :346).
- camera.K is rescaled to the current resolution, camera.D is not resolution dependent
  (media/camera_base.py:90-103). Both read over the network: results/probes/p2.txt.
- goto_target blocks until the move ends (reachy_mini.py:724) and raises MoveBusyError
  (io/protocol.py:1145) while another move runs (io/ws_client.py:324).
- push_audio_sample is non-blocking, takes float32 (N,) and upmixes mono; start_playing() is a no-op on
  the remote client; both rates are 16000 (media/audio_base.py:116, :130-161; media_manager.py:298-340).
- get_audio_sample returns float32 (N, 2) or None (media/audio_base.py:188).
"""
import logging
import time
from collections.abc import Callable, Iterator

import numpy as np

from jigsaw.types import Frame

log = logging.getLogger(__name__)

FIRST_FRAME_TIMEOUT_S = 5.0
STALL_WARN_S = 2.0          # frames() logs a warning after this long without a new frame, and keeps waiting
DRAIN_MAX_READS = 600       # cap per stream when connect() drains; the audio appsink holds up to 500 buffers
                            # (media/webrtc_client_gstreamer.py:127), the video appsink 1 (:142)
DRAIN_MAX_S = 0.5           # and a time cap per stream: each SDK read waits up to 20 ms for live data
                            # (media/gstreamer_utils.py:132), so live audio may never let a read return None
HELP = ("Check three things: (1) the robot is powered on and has finished booting; (2) the laptop is on the "
        "same Wi-Fi as the robot (if reachy-mini.local does not resolve, pass the robot's IP address as host); "
        "(3) the conversation app is stopped in the robot's dashboard, because it holds the camera and audio.")

# (head pose keyword arguments in degrees, duration in seconds); each gesture ends at neutral.
NOD = (({"pitch": 10}, 0.3), ({"pitch": -6}, 0.3), ({}, 0.3))
SHAKE = (({"yaw": 10}, 0.3), ({"yaw": -10}, 0.4), ({}, 0.3))


def resample(pcm: np.ndarray, rate: int, out_rate: int) -> np.ndarray:
    """Mono float32 pcm from rate to out_rate: windowed-sinc low-pass when downsampling, then linear."""
    n_out = round(len(pcm) * out_rate / rate)
    if rate == out_rate or len(pcm) == 0:
        return pcm.astype(np.float32)
    x = pcm.astype(np.float64)
    if out_rate < rate and len(x) >= 63:             # a shorter signal would sit in the filter's zero padding
        fc = 0.45 * out_rate / rate                  # cycles per input sample, below the new Nyquist
        n = np.arange(-31, 32)
        h = 2 * fc * np.sinc(2 * fc * n) * np.hamming(len(n))
        x = np.convolve(x, h / h.sum(), mode="same")
    t = np.arange(n_out) * (rate / out_rate)
    return np.interp(t, np.arange(len(x)), x).astype(np.float32)


# UNVERIFIED: the 720p K correction is an orchestrator instruction (docs/jigsaw/handoff/DECISIONS.md entry 7 on
# main); no probe has measured it. A reading of where it comes from, also unverified: the SDK scales K by the
# 2592-row sensor height (media/camera_base.py:137-147), while 720p is a centred 3840 x 2160 crop scaled down 3x
# (2592 / 720 = 3.6, (2592 - 2160) / 2 = 216, 2592 / 2160 = 1.2).
def correct_k(K: np.ndarray, height: int) -> np.ndarray:
    """K for frames `height` rows high: at 720 rows fy = 1.2 * fy and cy = (3.6 * cy - 216) / 3, fx and cx as
    given; any other height returns K unchanged. Returns a new array."""
    K = np.array(K, dtype=float)
    if height == 720:
        K[1, 1] = 1.2 * K[1, 1]
        K[1, 2] = (3.6 * K[1, 2] - 216) / 3
    return K


def _is_move_busy(e: BaseException) -> bool:
    return any(c.__name__ == "MoveBusyError" for c in type(e).__mro__)


class ReachyRobot:
    """FrameSource, Gestures, AudioOut and AudioIn over one connected ReachyMini (`mini`).

    head_pose builds a head target from pitch/yaw keywords in degrees (reachy_mini.utils.create_head_pose).
    clock gives Frame.t, times the no-new-frame warning and times play(); play() blocks with sleep (tests inject
    fakes for both).
    """

    name = "reachy"

    def __init__(self, mini, head_pose: Callable[..., object], clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self.mini, self.head_pose, self._clock, self._sleep = mini, head_pose, clock, sleep
        media = mini.media
        self.out_rate = int(media.get_output_audio_samplerate())
        self.rate = int(media.get_input_audio_samplerate())
        media.start_playing()
        media.start_recording()
        self._closed = False
        self._play_until = 0.0
        self._k_note_logged = False

    # FrameSource

    def _intrinsics(self) -> tuple[np.ndarray | None, np.ndarray | None]:
        out = []
        for attr in ("K", "D"):
            try:
                v = getattr(self.mini.media.camera, attr)
            except Exception as e:  # the camera raises RuntimeError before its resolution is known
                log.info("camera.%s unavailable: %r", attr, e)
                v = None
            out.append(None if v is None else np.asarray(v, dtype=float))
        return out[0], out[1]

    def _k_for(self, K: np.ndarray | None, height: int) -> np.ndarray | None:
        if K is None:
            return None
        if height != 720 and not self._k_note_logged:
            log.warning("camera K is uncorrected for %d-row frames: the correction is known only for 720 rows", height)
            self._k_note_logged = True
        return correct_k(K, height)

    def frames(self) -> Iterator[Frame]:
        """New camera frames only: None and a frame byte-identical to the previous one are skipped.

        Each yielded image is a copy, so an SDK that reuses one buffer neither hides new frames nor changes
        frames already yielded. After STALL_WARN_S of waiting without a new frame it logs a warning (again every
        STALL_WARN_S) and keeps waiting. Time the caller spends between two frames does not count as waiting.
        """
        K, D = self._intrinsics()
        prev = None
        last_new = last_warn = self._clock()
        while not self._closed:
            try:
                image = self.mini.media.get_frame()
            except Exception:
                if self._closed:
                    return
                raise
            now = self._clock()
            if image is None or (prev is not None and np.array_equal(image, prev)):
                if now - last_warn >= STALL_WARN_S:
                    log.warning("no new camera frame for %.1f s; still waiting", now - last_new)
                    last_warn = now
                self._sleep(0.005)
                continue
            image = prev = image.copy()
            # UNVERIFIED: BGR channel order (media/webrtc_client_gstreamer.py:170); needs the red-object check in p2.
            yield Frame(image, now, self._k_for(K, image.shape[0]), D)
            last_new = last_warn = self._clock()     # the wait for the next frame starts when the caller asks

    def _wait_for_frame(self, timeout: float) -> bool:
        t0 = self._clock()
        while self._clock() - t0 < timeout:
            if self.mini.media.get_frame() is not None:
                return True
            self._sleep(0.02)
        return False

    def _drain(self) -> None:
        """Read and discard queued frames, then recorded audio, until the SDK returns None; each stream stops
        early after DRAIN_MAX_READS reads or DRAIN_MAX_S seconds."""
        counts = []
        for read in (self.mini.media.get_frame, self.read):
            n, t0 = 0, self._clock()
            while n < DRAIN_MAX_READS and self._clock() - t0 < DRAIN_MAX_S and read() is not None:
                n += 1
            counts.append(n)
        log.info("connect dropped %d stale frames and %d stale audio chunks (caps: %d reads, %g s per stream)",
                 counts[0], counts[1], DRAIN_MAX_READS, DRAIN_MAX_S)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for stop in ("stop_recording", "stop_playing"):
            try:
                getattr(self.mini.media, stop)()
            except Exception as e:
                log.warning("%s failed: %r", stop, e)
        self.mini.__exit__(None, None, None)

    # Gestures

    def _gesture(self, name: str, steps) -> None:
        # UNVERIFIED: goto_target blocks until the move ends and raises MoveBusyError (reachy_mini.py:724,
        # io/ws_client.py:324); seen only on the mockup simulator so far.
        for i, (kw, duration) in enumerate(steps):
            try:
                self.mini.goto_target(head=self.head_pose(**kw, degrees=True), duration=duration)
            except Exception as e:
                if not _is_move_busy(e):
                    raise
                where = "head not moved" if i == 0 else f"head left at {steps[i - 1][0]} degrees"
                log.warning("%s stopped at step %d of %d: robot busy with another move (%s); %s",
                            name, i + 1, len(steps), e, where)
                return

    def nod(self) -> None:
        self._gesture("nod", NOD)

    def shake(self) -> None:
        self._gesture("shake", SHAKE)

    # AudioOut

    def play(self, pcm: np.ndarray, rate: int) -> None:
        pcm = np.asarray(pcm, dtype=np.float32)
        if pcm.ndim != 1:
            raise ValueError(f"play expects mono pcm, got shape {pcm.shape}")
        pcm = resample(pcm, rate, self.out_rate)
        if len(pcm) == 0:
            return
        self._play_until = self._clock() + len(pcm) / self.out_rate
        # UNVERIFIED: push_audio_sample returns at once and plays at 16 kHz (media/audio_base.py:130-161).
        self.mini.media.push_audio_sample(pcm)
        self._sleep(max(0.0, self._play_until - self._clock()))

    def is_playing(self) -> bool:
        return self._clock() < self._play_until

    # AudioIn

    def read(self) -> np.ndarray | None:
        # UNVERIFIED: float32 (N, 2) or None at 16 kHz (media/audio_base.py:188).
        s = self.mini.media.get_audio_sample()
        if s is None or len(s) == 0:
            return None
        s = np.asarray(s, dtype=np.float32)
        return s.mean(axis=1, dtype=np.float32) if s.ndim == 2 else s


def connect(host: str | None = None) -> ReachyRobot:
    """Connect to the robot (reachy-mini.local when host is None), wait for the first camera frame, then drop
    the frames and recorded audio queued so far so that the caller starts from fresh data."""
    try:
        from reachy_mini import ReachyMini
        from reachy_mini.utils import create_head_pose
    except ImportError as e:
        raise ImportError("reachy-mini is not installed: uv sync --extra robot") from e
    where = host or "reachy-mini.local"
    kwargs = {"connection_mode": "network", "host": host} if host else {}
    try:
        mini = ReachyMini(**kwargs)
    except Exception as e:
        raise ConnectionError(f"Cannot connect to the Reachy Mini at {where}: {e}. {HELP}") from e
    robot = ReachyRobot(mini, create_head_pose)
    if not robot._wait_for_frame(FIRST_FRAME_TIMEOUT_S):
        robot.close()
        raise ConnectionError(f"Connected to the Reachy Mini at {where}, but no camera frame arrived in "
                              f"{FIRST_FRAME_TIMEOUT_S:g} s. {HELP}")
    robot._drain()
    return robot
