"""Stable (A1): announce after `need` equal reads, once per presentation; give up after `miss_limit` misses."""
from jigsaw.stable import Stable
from jigsaw.types import Read, Reject

A, A1, B = Read(3, 1, 0), Read(3, 1, 1), Read(5, 4, 2)
MISS, NONE = Reject("no_match"), Reject("no_grid")


def feed(s, decisions):
    return [s.update(d) for d in decisions]


def test_starts_with_nothing_announced():
    assert Stable().last is None


def test_three_equal_reads_announce_once():
    s = Stable()
    assert feed(s, [A, A, A]) == [None, None, "announce"]
    assert s.last == A
    assert feed(s, [A] * 10) == [None] * 10


def test_a_reject_between_reads_restarts_the_count():
    s = Stable()
    assert feed(s, [A, A, MISS, A, A, A]) == [None] * 5 + ["announce"]


def test_a_different_read_restarts_the_count():
    s = Stable()
    assert feed(s, [A, A, B, B, B]) == [None] * 4 + ["announce"]
    assert s.last == B


def test_the_same_piece_at_another_turn_is_not_announced_again():
    s = Stable()
    feed(s, [A, A, A])
    assert feed(s, [A1] * 5) == [None] * 5
    assert s.last == A


def test_another_piece_after_an_announcement_is_announced():
    s = Stable()
    feed(s, [A, A, A])
    assert feed(s, [B, B, B]) == [None, None, "announce"]
    assert s.last == B


def test_unreadable_piece_gives_up_once_at_the_miss_limit():
    s = Stable()
    out = feed(s, [MISS] * 20)
    assert out.index("give_up") == 14 and out.count("give_up") == 1
    assert s.last is None


def test_an_empty_view_never_gives_up():
    assert feed(Stable(), [NONE] * 100) == [None] * 100


def test_an_empty_view_ends_the_presentation():
    s = Stable()
    first = feed(s, [MISS] * 15 + [NONE] + [MISS] * 15)
    assert first.count("give_up") == 2 and first[14] == "give_up" and first[30] == "give_up"


def test_reads_that_never_settle_count_as_misses():
    s = Stable()
    out = feed(s, [A, B] * 10)
    assert out.count("announce") == 0 and out.index("give_up") == 14


def test_no_give_up_after_an_announcement():
    s = Stable()
    feed(s, [A, A, A])
    assert feed(s, [MISS] * 30) == [None] * 30


def test_the_announced_piece_shown_again_is_known_and_not_given_up():
    s = Stable()
    feed(s, [A, A, A, NONE])
    assert feed(s, [A, A, A] + [MISS] * 30) == [None] * 33


def test_need_and_miss_limit_are_parameters():
    s = Stable(need=1, miss_limit=2)
    assert feed(s, [A]) == ["announce"]
    s = Stable(need=1, miss_limit=2)
    assert feed(s, [MISS, MISS, MISS]) == [None, "give_up", None]
