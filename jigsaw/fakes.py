"""Test doubles for the hardware Protocols in jigsaw.types (CONTRACTS.md section 4)."""
import time
from collections.abc import Iterator

import numpy as np

from jigsaw.types import Frame


class FakeFrameSource:
    name = "fake"

    def __init__(self, images, K=None, D=None):
        self.images, self.K, self.D, self.closed = list(images), K, D, False

    def frames(self) -> Iterator[Frame]:
        for img in self.images:
            yield Frame(img, time.monotonic(), self.K, self.D)

    def close(self) -> None:
        self.closed = True


class FakeGestures:
    def __init__(self):
        self.calls: list[str] = []

    def nod(self) -> None:
        self.calls.append("nod")

    def shake(self) -> None:
        self.calls.append("shake")


class FakeAudioOut:
    def __init__(self):
        self.played: list[tuple[int, int]] = []

    def play(self, pcm: np.ndarray, rate: int) -> None:
        self.played.append((len(pcm), rate))

    def is_playing(self) -> bool:
        return False


class FakeAudioIn:
    rate = 16000

    def __init__(self, chunks):
        self.chunks = list(chunks)

    def read(self) -> np.ndarray | None:
        return self.chunks.pop(0) if self.chunks else None
