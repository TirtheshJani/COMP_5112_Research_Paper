import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("reproduce_all", Path(__file__).resolve().parent.parent / "scripts" / "reproduce_all.py")
ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ra)

VOICE = "SKIPPED [2] tests/test_voice_tts.py:8: Piper voice file absent (assets/voice/README.md)"


def test_expected_skip_passes():
    out = f"{VOICE}\n210 passed, 2 skipped in 5.00s"
    summary, skips, ok = ra.classify_pytest(out)
    assert summary == "210 passed, 2 skipped in 5.00s"
    assert skips == [("tests/test_voice_tts.py:8", "Piper voice file absent (assets/voice/README.md)", 2, True)]
    assert ok


def test_unexpected_skip_fails():
    out = f"{VOICE}\nSKIPPED [1] tests/test_printing.py:7: could not import 'reportlab'\n210 passed, 3 skipped in 5.00s"
    _, skips, ok = ra.classify_pytest(out)
    assert [s[3] for s in skips] == [True, False]
    assert not ok


def test_no_summary_line_fails():
    summary, skips, ok = ra.classify_pytest("collected nothing useful")
    assert summary == "(no summary line)"
    assert skips == []
    assert not ok


def test_no_skips_passes():
    assert ra.classify_pytest("212 passed in 4.00s")[2]


def test_failures_fail():
    assert not ra.classify_pytest("1 failed, 211 passed in 4.00s")[2]
