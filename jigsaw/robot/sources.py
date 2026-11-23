"""Frame sources that need no robot (CONTRACTS.md section 3, S3 R2).

ReplaySource reads saved frames from a folder in name order. RenderSource renders piece backs with
render.photograph. Both yield Frame objects with BGR uint8 images, time.monotonic() stamps and no
intrinsics (K = D = None).
"""
import time
from collections.abc import Iterable, Iterator
from pathlib import Path

import cv2
import numpy as np

from jigsaw.render import photograph, piece_back
from jigsaw.types import Frame

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}


class ReplaySource:
    """Image files of a folder, in name order, then stop."""

    name = "replay"

    def __init__(self, folder: str | Path):
        self.paths = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
        self._closed = False

    def frames(self) -> Iterator[Frame]:
        for path in self.paths:
            if self._closed:
                return
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"cannot read image {path}")
            yield Frame(image, time.monotonic(), None, None)

    def close(self) -> None:
        self._closed = True


class RenderSource:
    """One rendered photograph per piece (row, col), front coordinates, in the given order.

    photograph_kwargs go to render.photograph (size, tilt, blur, noise, background, ...). Without
    angle_deg each frame gets an angle drawn uniformly from [0, 360) with rng.
    """

    name = "render"

    def __init__(self, rng: np.random.Generator, pieces: Iterable[tuple[int, int]], px_per_cell: float = 16.0,
                 **photograph_kwargs):
        self.rng, self.pieces, self.px_per_cell = rng, list(pieces), px_per_cell
        self.kwargs = photograph_kwargs
        self._closed = False

    def frames(self) -> Iterator[Frame]:
        backs: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}
        for r, c in self.pieces:
            if self._closed:
                return
            if (r, c) not in backs:
                backs[r, c] = piece_back(r, c, self.px_per_cell)
            kwargs = dict(self.kwargs)
            angle = kwargs.pop("angle_deg", None)
            if angle is None:
                angle = float(self.rng.uniform(0, 360))
            image = photograph(*backs[r, c], self.rng, angle, **kwargs)
            yield Frame(image, time.monotonic(), None, None)

    def close(self) -> None:
        self._closed = True
