"""One call from a camera frame to a decision: vision.read_grid then decode.decode_grid."""
import numpy as np

from jigsaw.decode import build_table, decode_grid
from jigsaw.patch import back_grid
from jigsaw.types import Decision, GridRead, Reject


class PieceReader:
    def __init__(self):
        self.table = build_table(back_grid())
        self.last_grid: GridRead | None = None

    def read(self, bgr: np.ndarray) -> Decision:
        from jigsaw.vision import read_grid
        gr = read_grid(bgr)
        self.last_grid = gr if isinstance(gr, GridRead) else None
        if isinstance(gr, Reject):
            return gr
        return decode_grid(gr.cells, gr.mask, self.table)
