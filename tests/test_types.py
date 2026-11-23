import numpy as np

from jigsaw import types as T
from jigsaw.fakes import FakeAudioIn, FakeAudioOut, FakeFrameSource, FakeGestures


def test_constants():
    assert (T.U, T.PIECE_CELLS, T.PUZZLE_ROWS, T.PUZZLE_COLS) == (5, 10, 7, 5)
    assert (T.GRID_ROWS, T.GRID_COLS) == (72, 52)
    assert abs(T.PIECE_MM - 36.0) < 1e-9


def test_read_is_hashable_and_frozen():
    assert T.Read(1, 2, 3) == T.Read(1, 2, 3)
    assert len({T.Read(1, 2, 3), T.Read(1, 2, 3)}) == 1


def test_fakes_satisfy_protocols():
    img = np.zeros((4, 4, 3), np.uint8)
    src = FakeFrameSource([img, img])
    frames = list(src.frames())
    assert len(frames) == 2 and frames[0].image.shape == (4, 4, 3) and frames[0].K is None
    assert isinstance(src, T.FrameSource)
    g = FakeGestures()
    g.nod()
    g.shake()
    assert g.calls == ["nod", "shake"] and isinstance(g, T.Gestures)
    out = FakeAudioOut()
    out.play(np.zeros(160, np.float32), 16000)
    assert out.played == [(160, 16000)] and out.is_playing() is False and isinstance(out, T.AudioOut)
    a = FakeAudioIn([np.ones(3, np.float32)])
    assert isinstance(a, T.AudioIn) and a.read().sum() == 3 and a.read() is None
