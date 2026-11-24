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
    assert reader.read(np.zeros((720, 1280, 3), np.uint8)) == Reject("no_grid")
    assert reader.last_grid is None


def test_reader_on_a_turned_piece():
    rng = np.random.default_rng(12)
    g, a = piece_back(2, 3, 16)
    reader = PieceReader()
    d = reader.read(photograph(g, a, rng, 90 * 3 + 10, tilt=0.03, blur=0.5, noise=3, size=(1280, 720)))
    assert d == Read(2, 3, 3)


def test_reader_rejects_from_the_decoder_when_cells_are_scrambled():
    # a readable grid whose cells decode to no window: the Reject comes from decode_grid, not from vision
    rng = np.random.default_rng(13)
    g, a = piece_back(4, 2, 16)
    blocks = np.random.default_rng(0).integers(0, 2, (g.shape[0] // 16 + 1, g.shape[1] // 16 + 1))
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    scrambled = np.where(blocks[yy // 16, xx // 16] == 1, 255, 0).astype(np.uint8)
    reader = PieceReader()
    d = reader.read(photograph(scrambled, a, rng, 0, size=(1280, 720)))
    assert isinstance(d, Reject) and d.reason != "no_grid"
