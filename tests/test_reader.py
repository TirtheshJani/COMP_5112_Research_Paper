import numpy as np

from jigsaw.reader import PieceReader
from jigsaw.render import photograph, piece_back
from jigsaw.types import Read, Reject


def test_reader_on_a_720p_frame():
    rng = np.random.default_rng(11)
    g, a = piece_back(5, 1, 16)
    img = photograph(g, a, rng, 200, tilt=0.04, blur=0.6, noise=4, size=(1280, 720))
    reader = PieceReader()
    d = reader.read(img)
    assert isinstance(d, Read) and (d.row, d.col) == (5, 1) and reader.last_grid is not None
    assert isinstance(reader.read(np.zeros((720, 1280, 3), np.uint8)), Reject)
