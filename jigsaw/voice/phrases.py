"""Sentences the robot speaks. Pure functions, no audio libraries."""
from __future__ import annotations

from jigsaw.types import Read

# Derivation: turn = k means the camera sees the back rotated k quarter turns counter-clockwise from upright.
# To make it upright the person rotates it k quarter turns clockwise as seen from the back, which is k quarter
# turns counter-clockwise as seen from the picture side. Wording: the spec's design notes say
# "counter-clockwise / clockwise"; the author's S4 prompt chose "to the left / to the right" instead, and that is used here.
# S6 confirms these on real pieces; until then they are unconfirmed physically.
TURN_SENTENCE: dict[int, str] = {
    0: "It is the right way up.",
    1: "Turn it a quarter turn to the left.",
    2: "Turn it upside down.",
    3: "Turn it a quarter turn to the right.",
}

REJECT_DEFAULT = "I cannot read that one. Show me again."
REJECT_SENTENCE: dict[str, str] = {
    "no_grid": "Show me the grid side, over the green card.",
    "no_window": "Move your fingers to the edge of the piece.",
}


def phrase_read(read: Read) -> str:
    """Row and column are zero-based in code and one-based when spoken."""
    return f"Row {read.row + 1}, column {read.col + 1}. {TURN_SENTENCE[read.turn]}"


def phrase_reject(reason: str) -> str:
    return REJECT_SENTENCE.get(reason, REJECT_DEFAULT)
