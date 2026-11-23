"""Frame sources that need no robot: ReplaySource and RenderSource (S3, R2)."""
import cv2
import numpy as np

from jigsaw.reader import PieceReader
from jigsaw.robot.sources import RenderSource, ReplaySource
from jigsaw.types import Frame, FrameSource, Read


def _write(folder, name, value):
    img = np.zeros((8, 10, 3), np.uint8)
    img[:, :, 0] = value          # blue channel only, so a channel swap would show
    cv2.imwrite(str(folder / name), img)
    return img


def test_replay_yields_images_in_name_order_then_stops(tmp_path):
    b = _write(tmp_path, "b.png", 20)
    a = _write(tmp_path, "a.png", 10)
    c = _write(tmp_path, "c.jpg", 30)
    (tmp_path / "notes.txt").write_text("not an image")
    src = ReplaySource(tmp_path)
    frames = list(src.frames())
    assert [int(f.image[0, 0, 0]) for f in frames][:2] == [10, 20]
    assert len(frames) == 3
    assert abs(int(frames[2].image[0, 0, 0]) - 30) <= 2          # jpg is lossy
    assert np.array_equal(frames[0].image, a) and np.array_equal(frames[1].image, b)
    assert c.shape == frames[2].image.shape


def test_replay_frames_are_bgr_uint8_with_monotonic_time_and_no_intrinsics(tmp_path):
    for k in range(3):
        _write(tmp_path, f"{k:03d}.png", 50 + k)
    frames = list(ReplaySource(tmp_path).frames())
    assert all(isinstance(f, Frame) for f in frames)
    assert all(f.image.dtype == np.uint8 and f.image.shape == (8, 10, 3) for f in frames)
    assert all(int(f.image[0, 0, 0]) == 50 + k and f.image[0, 0, 2] == 0 for k, f in enumerate(frames))
    assert all(f.K is None and f.D is None for f in frames)
    ts = [f.t for f in frames]
    assert ts == sorted(ts)


def test_replay_close_stops_iteration(tmp_path):
    for k in range(5):
        _write(tmp_path, f"{k}.png", k)
    src = ReplaySource(tmp_path)
    it = src.frames()
    next(it)
    src.close()
    assert list(it) == []


def test_sources_satisfy_frame_source_protocol(tmp_path):
    assert isinstance(ReplaySource(tmp_path), FrameSource)
    assert isinstance(RenderSource(np.random.default_rng(0), [(0, 0)]), FrameSource)


def test_render_yields_one_readable_frame_per_piece():
    pieces = [(0, 0), (3, 2), (6, 4)]
    src = RenderSource(np.random.default_rng(1), pieces, size=(1280, 720), blur=0.5, noise=3)
    frames = list(src.frames())
    assert len(frames) == 3
    assert all(f.image.shape == (720, 1280, 3) and f.image.dtype == np.uint8 for f in frames)
    assert all(f.K is None and f.D is None for f in frames)
    reader = PieceReader()
    for (r, c), f in zip(pieces, frames):
        d = reader.read(f.image)
        assert isinstance(d, Read) and (d.row, d.col) == (r, c), d


def test_render_is_reproducible_from_the_seed_and_honours_a_fixed_angle():
    a = [f.image for f in RenderSource(np.random.default_rng(7), [(2, 2)], size=(400, 400)).frames()]
    b = [f.image for f in RenderSource(np.random.default_rng(7), [(2, 2)], size=(400, 400)).frames()]
    assert np.array_equal(a[0], b[0])
    up = next(RenderSource(np.random.default_rng(3), [(4, 1)], angle_deg=90, size=(1280, 720)).frames())
    d = PieceReader().read(up.image)
    assert isinstance(d, Read) and (d.row, d.col) == (4, 1)


def test_render_close_stops_iteration():
    src = RenderSource(np.random.default_rng(0), [(0, 0), (1, 1), (2, 2)], size=(300, 300))
    it = src.frames()
    next(it)
    src.close()
    assert list(it) == []
