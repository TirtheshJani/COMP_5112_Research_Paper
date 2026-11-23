"""Probe 5 (P1 Task 5): does a nod or a shake during frame capture or audio playback drop frames or glitch
the audio, and how long after a gesture do the frames settle? MOVES THE ROBOT AND PLAYS A TONE.

    python scripts/probes/p5_motion_media.py [--host reachy-mini.local] --move

Nothing moves and nothing plays without --move. The robot is driven only through ReachyRobot from
jigsaw.robot.reachy: nod() and shake() for motion, play() for sound (CLAUDE.md rule 6).

A thread reads robot.frames() (new frames only) through three phases:
  1. still   STILL_S seconds with the head still and no sound: the baseline frame rate, largest gap between
             new frames, and frame-difference noise.
  2. motion  nod, shake, nod, shake, each followed by SETTLE_WAIT_S seconds of stillness.
  3. audio   a TONE_S second 440 Hz tone; one nod and one shake while it plays. The operator then answers
             whether the tone had a gap, a click or a pitch change.
Frame drops: new frames per second and the largest gap between new frames in each gesture's window,
against the still phase.

Settling time.
  Metric: mean absolute difference between consecutive new frames, in grey levels (0 to 255), after
  converting to grey and shrinking to 160 x 90 pixels (frame_diff).
  Threshold: twice the 95th percentile of that difference over the still phase, and at least 0.5 grey
  levels (still_threshold).
  A gesture has settled at the first new frame after nod() or shake() returns from which N_STILL
  consecutive differences are all below the threshold; the settling time is that frame's arrival time
  minus the moment the gesture returned (settling_time). It includes the camera pipeline's latency, which
  is what the app has to wait for anyway. The value for S6 is the largest settling time over the four
  gestures of the motion phase, or "none" if any of them did not settle within SETTLE_WAIT_S.

Writes results/probes/motion_media.md, which ends with the single line "settling_time_s: <value>"
(S6 copies it into app.py), and tees the console to results/probes/p5.txt.
UNVERIFIED on the robot until this probe has run.
"""
import argparse
import threading
import time
from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np

from jigsaw.robot.reachy import ReachyRobot, connect

OUT = Path(__file__).resolve().parents[2] / "results" / "probes"
STILL_S = 5.0
SETTLE_WAIT_S = 2.5
TONE_S = 6.0
N_STILL = 5
SMALL = (160, 90)                    # (width, height) for frame_diff


def frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute grey-level difference of two BGR frames, both shrunk to SMALL."""
    ga, gb = (cv2.resize(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), SMALL, interpolation=cv2.INTER_AREA) for x in (a, b))
    return float(np.mean(np.abs(ga.astype(np.float32) - gb.astype(np.float32))))


def still_threshold(still_diffs: Sequence[float]) -> float:
    """Twice the 95th percentile of the differences measured with the head still, at least 0.5 grey levels."""
    return max(0.5, 2.0 * float(np.percentile(still_diffs, 95)))


def settling_time(times: Sequence[float], diffs: Sequence[float], t_end: float, threshold: float,
                  n_still: int = N_STILL) -> float | None:
    """Seconds from t_end to the first frame j after it with diffs[j - 1 : j - 1 + n_still] all below threshold.

    diffs[k] is the difference between frames k and k + 1, so len(diffs) == len(times) - 1. None if no frame
    qualifies before the frames run out.
    """
    for j in range(1, len(times)):
        if times[j] <= t_end:
            continue
        run = diffs[j - 1:j - 1 + n_still]
        if len(run) < n_still:
            return None
        if all(d < threshold for d in run):
            return times[j] - t_end
    return None


def frame_stats(times: Sequence[float], t0: float, t1: float) -> tuple[int, float, float]:
    """(new frames in [t0, t1], frames per second, largest gap in seconds, window edges included)."""
    inside = [t for t in times if t0 <= t <= t1]
    gaps = np.diff([t0, *inside, t1])
    return len(inside), len(inside) / (t1 - t0), float(gaps.max())


def settling_value(settles: Sequence[float | None]) -> str:
    if not settles or any(s is None for s in settles):
        return "none"
    return f"{max(settles):.2f}"


def report(lines: Sequence[str], settles: Sequence[float | None]) -> str:
    """The markdown body followed by the single last line "settling_time_s: <value>"."""
    return "\n".join([*lines, "", f"settling_time_s: {settling_value(settles)}"]) + "\n"


class FrameLog:
    """Reads robot.frames() in a thread; keeps each new frame's time and its difference to the previous one."""

    def __init__(self, robot: ReachyRobot):
        self.times: list[float] = []
        self.diffs: list[float] = []          # diffs[k] is between frames k and k + 1
        self.shape = None
        self._thread = threading.Thread(target=self._run, args=(robot,), daemon=True)
        self._thread.start()

    def _run(self, robot: ReachyRobot) -> None:
        prev = None
        for f in robot.frames():
            if prev is not None:
                self.diffs.append(frame_diff(prev, f.image))
            self.times.append(f.t)
            self.shape, prev = f.image.shape, f.image

    def join(self) -> None:
        self._thread.join(timeout=5)


def gesture(robot: ReachyRobot, name: str) -> tuple[str, float, float]:
    t0 = time.monotonic()
    getattr(robot, name)()
    return name, t0, time.monotonic()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=None, help="robot address (default: reachy-mini.local)")
    ap.add_argument("--move", action="store_true", help="let the head nod and shake and play the tone")
    a = ap.parse_args()
    if not a.move:
        print("Dry run. Add --move to let the head nod and shake (10 degrees) and play a 440 Hz tone.")
        return
    from _tee import tee
    tee("p5")
    robot = connect(a.host)
    log = FrameLog(robot)
    print(f"phase 1: {STILL_S:g} s still and silent")
    t0 = time.monotonic()
    time.sleep(STILL_S)
    t_still = (t0, time.monotonic())

    print("phase 2: nod, shake, nod, shake")
    motion = []
    for name in ("nod", "shake", "nod", "shake"):
        motion.append(gesture(robot, name))
        time.sleep(SETTLE_WAIT_S)

    print(f"phase 3: {TONE_S:g} s tone with a nod and a shake")
    play_errors: list[str] = []

    def play() -> None:
        try:
            t = np.arange(int(TONE_S * 16000)) / 16000
            robot.play((0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 16000)
        except Exception as e:  # noqa: BLE001 (a probe reports every failure)
            play_errors.append(repr(e))

    player = threading.Thread(target=play)
    player.start()
    time.sleep(1.0)
    with_tone = []
    for name in ("nod", "shake"):
        n, t0, t1 = gesture(robot, name)
        with_tone.append((f"{n} + tone", t0, t1))
        time.sleep(1.0)
    player.join()
    heard = input("Did the tone have a gap, a click or a pitch change while the head moved? [y/n] ").strip().lower()
    robot.close()
    log.join()

    times, diffs = log.times, log.diffs
    still_diffs = [d for t, d in zip(times[1:], diffs) if t_still[0] <= t <= t_still[1]]
    if not still_diffs:
        print("No frames in the still phase: nothing to measure.")
        return
    thr = still_threshold(still_diffs)
    settles = [settling_time(times, diffs, t1, thr) for _, _, t1 in motion]
    settles = [s if s is not None and s <= SETTLE_WAIT_S else None for s in settles]   # later frames are phase 3

    lines = [f"# Probe 5: motion and media ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Host: {a.host or 'reachy-mini.local'}. Frame shape: {log.shape}. New frames logged: {len(times)}.", "",
             "| Window | Seconds | New frames | Frames per second | Largest gap (s) |", "|---|---|---|---|---|"]
    for label, t0, t1 in [("still", *t_still), *motion, *with_tone]:
        n, fps, gap = frame_stats(times, t0, t1)
        lines.append(f"| {label} | {t1 - t0:.2f} | {n} | {fps:.1f} | {gap:.3f} |")
    lines += ["", f"Settling threshold: {thr:.2f} grey levels (twice the 95th percentile of still-phase frame "
              f"differences, at least 0.5); {N_STILL} consecutive differences below it.",
              "Settling after each motion-phase gesture (s): "
              + ", ".join(f"{name} {'none' if s is None else f'{s:.2f}'}" for (name, _, _), s in zip(motion, settles)),
              "", f"Audio: operator heard a gap, click or pitch change while the head moved: {heard or 'no answer'}.",
              f"play() errors: {'; '.join(play_errors) or 'none'}."]
    text = report(lines, settles)
    (OUT / "motion_media.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
