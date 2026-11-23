"""Map recognised text to one of four commands."""
from __future__ import annotations

import re
from typing import Literal

Command = Literal["ask", "again", "next", "stop"]

# Checked in order; stop wins over everything, so "stop saying that again" stops.
_TABLE: tuple[tuple[Command, tuple[str, ...]], ...] = (
    ("stop", ("that s enough", "thats enough", "stop")),
    ("again", ("say that again", "again", "repeat")),
    ("next", ("next piece", "next")),
    ("ask", ("where does this go", "where does it go", "where")),
)


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def match_command(text: str) -> Command | None:
    words = f" {_normalise(text)} "
    for command, phrases in _TABLE:
        if any(f" {p} " in words for p in phrases):
            return command
    return None
