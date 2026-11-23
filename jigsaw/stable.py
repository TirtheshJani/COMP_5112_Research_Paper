"""Steady filter between per-frame decisions and what the robot says (CONTRACTS section 3, S6 A1).

A presentation is the time a piece is in view; a no_grid reject (nothing on the mat) ends it.

- "announce" when the same Read has arrived `need` times in a row and its piece (row, col) differs from
  the last announced piece. The same piece at another turn is not announced again; `next` in the app
  makes a new Stable for that.
- "give_up" once per presentation, when `miss_limit` frames have passed without an answer: every frame
  that is neither no_grid nor the one completing a stable read counts as a miss.
- After an answer (an announcement, or the announced piece read stably again) the presentation gives up
  no more.
"""
from typing import Literal

from jigsaw.types import Decision, Read

Event = Literal["announce", "give_up"]


class Stable:
    def __init__(self, need: int = 3, miss_limit: int = 15):
        self.need, self.miss_limit = need, miss_limit
        self.last: Read | None = None      # last announced Read
        self._run: Read | None = None      # Read being counted
        self._count = 0
        self._misses = 0
        self._answered = False             # this presentation has been answered or given up

    def update(self, d: Decision) -> Event | None:
        if not isinstance(d, Read):
            self._run, self._count = None, 0
            if d.reason == "no_grid":
                self._misses, self._answered = 0, False
                return None
        else:
            if d == self._run:
                self._count += 1
            else:
                self._run, self._count = d, 1
            if self._count == self.need:
                self._answered = True
                if self.last is None or (d.row, d.col) != (self.last.row, self.last.col):
                    self.last = d
                    return "announce"
                return None
        if self._answered:
            return None
        self._misses += 1
        if self._misses >= self.miss_limit:
            self._answered = True
            return "give_up"
        return None
