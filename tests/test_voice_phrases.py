import pytest

from jigsaw.types import Read
from jigsaw.voice.phrases import phrase_read, phrase_reject


@pytest.mark.parametrize(
    "turn,sentence",
    [
        (0, "It is the right way up."),
        (1, "Turn it a quarter turn to the left."),
        (2, "Turn it upside down."),
        (3, "Turn it a quarter turn to the right."),
    ],
)
def test_phrase_read_turns(turn, sentence):
    assert phrase_read(Read(3, 1, turn)) == f"Row 4, column 2. {sentence}"


def test_phrase_read_is_one_based():
    assert phrase_read(Read(0, 0, 0)).startswith("Row 1, column 1. ")
    assert phrase_read(Read(6, 4, 2)).startswith("Row 7, column 5. ")


@pytest.mark.parametrize(
    "reason,text",
    [
        ("no_grid", "Show me the grid side, over the green card."),
        ("no_window", "Move your fingers to the edge of the piece."),
        ("low_contrast", "I cannot read that one. Show me again."),
        ("no_match", "I cannot read that one. Show me again."),
        ("ambiguous", "I cannot read that one. Show me again."),
        ("inconsistent", "I cannot read that one. Show me again."),
        ("off_puzzle", "I cannot read that one. Show me again."),
        ("anything", "I cannot read that one. Show me again."),
    ],
)
def test_phrase_reject(reason, text):
    assert phrase_reject(reason) == text


def test_no_em_dash():
    for t in range(4):
        assert not {"—", "–"} & set(phrase_read(Read(0, 0, t)))
