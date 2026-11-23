"""R6, R7, R9, R10 on the robot. A person watches the gestures and listens to the tone (HUMAN)."""
import time
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[2] / "results" / "probes"


def test_50_frames_in_under_10_s(robot):
    it = robot.frames()
    next(it)                                   # drop what queued up since connect
    t0 = time.monotonic()
    frames = [next(it) for _ in range(50)]
    elapsed = time.monotonic() - t0
    distinct = 1 + sum(not np.array_equal(a.image, b.image) for a, b in zip(frames, frames[1:]))
    print(f"\n50 frames in {elapsed:.2f} s, {distinct} distinct, shape {frames[0].image.shape}, "
          f"K is None: {frames[0].K is None}, D is None: {frames[0].D is None}")
    assert elapsed < 10
    assert all(f.image.dtype == np.uint8 and f.image.ndim == 3 and f.image.shape[2] == 3 for f in frames)


def test_nod_then_shake_each_under_1_5_s(robot):
    for name in ("nod", "shake"):
        t0 = time.monotonic()
        getattr(robot, name)()
        elapsed = time.monotonic() - t0
        print(f"\n{name}: {elapsed:.2f} s")
        assert elapsed < 1.5
        time.sleep(1.0)


def test_one_second_1_khz_tone(robot):
    rate = 22050                               # exercises the resampler, like Piper output
    t = np.arange(rate) / rate
    tone = (0.3 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    t0 = time.monotonic()
    robot.play(tone, rate)
    elapsed = time.monotonic() - t0
    print(f"\ntone: play() returned after {elapsed:.2f} s, is_playing {robot.is_playing()}")
    assert 0.95 <= elapsed < 1.3
    assert not robot.is_playing()


def test_three_second_recording_saved_as_wav(robot):
    while robot.read() is not None:            # drop the backlog recorded since connect
        pass
    chunks, t0 = [], time.monotonic()
    while time.monotonic() - t0 < 3.0:
        c = robot.read()
        if c is None:
            time.sleep(0.01)
        else:
            chunks.append(c)
    audio = np.concatenate(chunks)
    peak = float(np.abs(audio).max())
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "recording_3s.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(robot.rate)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"\nrecording: {len(audio)} samples ({len(audio) / robot.rate:.2f} s at {robot.rate} Hz), "
          f"peak {peak:.4f} ({20 * np.log10(max(peak, 1e-9)):.1f} dBFS), saved {path.name}")
    assert audio.dtype == np.float32 and audio.ndim == 1
    assert 0.85 * 3 * robot.rate <= len(audio) <= 1.15 * 3 * robot.rate
