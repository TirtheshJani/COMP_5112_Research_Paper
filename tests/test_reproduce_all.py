import importlib.util
from pathlib import Path

import pytest

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


def test_requires_the_robot_is_not_an_expected_skip():
    assert "requires the robot" not in ra.EXPECTED_SKIPS
    out = "SKIPPED [1] tests/robot_live/test_x.py:3: requires the robot\n5 passed, 1 skipped in 1.00s"
    assert not ra.classify_pytest(out)[2]


def test_live_skip_is_expected():
    reason = "live robot test: not run; set JIGSAW_LIVE=1 (and JIGSAW_HOST) with the robot on"
    out = f"SKIPPED [1] tests/robot_live/conftest.py:14: {reason}\n5 passed, 1 skipped in 1.00s"
    assert ra.classify_pytest(out)[2]


def test_extras_to_sync_excludes_robot():
    args = ra.extras_to_sync()
    names = args[1::2]
    assert args[0::2] == ["--extra"] * len(names)
    assert "robot" not in names
    assert {"dev", "print"} <= set(names)


def _pdf(path, pages=1, box=40):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path), pagesize=(200, 200), invariant=1)
    for _ in range(pages):
        c.rect(20, 20, box, 40, stroke=0, fill=1)
        c.showPage()
    c.save()
    return path


def test_compare_pdf_identical_bytes(tmp_path):
    pytest.importorskip("reportlab")
    a, b = _pdf(tmp_path / "a.pdf"), _pdf(tmp_path / "b.pdf")
    ok, msg = ra.compare_pdf(a, b)
    assert ok and "identical" in msg


def test_compare_pdf_one_pixel_difference_fails(tmp_path):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdfium2")
    a, b = _pdf(tmp_path / "a.pdf", box=40), _pdf(tmp_path / "b.pdf", box=40.2)
    ok, msg = ra.compare_pdf(a, b)
    assert not ok and "DIFFER" in msg


def test_compare_pdf_page_count_differs(tmp_path):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdfium2")
    ok, msg = ra.compare_pdf(_pdf(tmp_path / "a.pdf", pages=1), _pdf(tmp_path / "b.pdf", pages=2))
    assert not ok and "page counts differ" in msg


def test_main_refuses_a_dirty_tree(monkeypatch):
    class Done:
        def __init__(self, out):
            self.stdout = out

    monkeypatch.setattr(ra.subprocess, "run", lambda cmd, **kw: Done("abc123\n" if "rev-parse" in cmd else " M jigsaw/x.py\n"))
    monkeypatch.setattr(ra.sys, "argv", ["reproduce_all.py"])
    assert ra.main() == 2


HEADER = "experiment,pattern,decoder,arm,px_per_cell,tilt,blur,noise,finger,n,correct,seed,commit"


def _csv(path, rows, header=HEADER):
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_seed_and_n_unique(tmp_path):
    p = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,1,abc"])
    assert ra.seed_and_n(p) == (1, 300)


def test_two_seeds_raise(tmp_path):
    p = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,2,abc"])
    with pytest.raises(ValueError, match="seed"):
        ra.seed_and_n(p)


def test_two_n_raise(tmp_path):
    p = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,100,6,1,abc"])
    with pytest.raises(ValueError, match="n"):
        ra.seed_and_n(p)


def test_compare_identical_except_commit_passes(tmp_path):
    a = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,1,abc"])
    b = _csv(tmp_path / "b.csv", ["dense,o,single,f,,,,,,300,6,1,def", "dense,s,single,f,,,,,,300,5,1,def"])
    r = ra.compare_csvs(a, b)
    assert r["ok"] and r["rows_compared"] == 2 and r["rows_differing"] == 0 and r["columns"] == {}


def test_compare_one_count_differs_fails(tmp_path):
    a = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,1,abc"])
    b = _csv(tmp_path / "b.csv", ["dense,s,single,f,,,,,,300,5,1,def", "dense,o,single,f,,,,,,300,7,1,def"])
    r = ra.compare_csvs(a, b)
    assert not r["ok"] and r["rows_differing"] == 1 and r["columns"] == {"correct": 1}


def test_compare_missing_row_fails(tmp_path):
    a = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,1,abc"])
    b = _csv(tmp_path / "b.csv", ["dense,s,single,f,,,,,,300,5,1,def"])
    r = ra.compare_csvs(a, b)
    assert not r["ok"] and r["only_committed"] == 1 and r["only_regenerated"] == 0


def test_compare_extra_row_and_header_change_fail(tmp_path):
    a = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc"])
    b = _csv(tmp_path / "b.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,o,single,f,,,,,,300,6,1,abc"])
    assert ra.compare_csvs(a, b)["only_regenerated"] == 1
    c = _csv(tmp_path / "c.csv", ["dense,s,single,f,,,,,,300,5,1,abc"], header=HEADER + ",extra")
    assert not ra.compare_csvs(a, c)["ok"]


def test_compare_duplicate_key_raises(tmp_path):
    a = _csv(tmp_path / "a.csv", ["dense,s,single,f,,,,,,300,5,1,abc", "dense,s,single,f,,,,,,300,6,1,abc"])
    with pytest.raises(ValueError, match="duplicate"):
        ra.compare_csvs(a, a)


def test_same_bytes(tmp_path):
    (tmp_path / "a.md").write_bytes(b"x\n")
    (tmp_path / "b.md").write_bytes(b"x\n")
    (tmp_path / "c.md").write_bytes(b"y\n")
    assert ra.same_bytes(tmp_path / "a.md", tmp_path / "b.md")
    assert not ra.same_bytes(tmp_path / "a.md", tmp_path / "c.md")
    assert not ra.same_bytes(tmp_path / "a.md", tmp_path / "missing.md")


def test_has_frames(tmp_path):
    assert not ra.has_frames(tmp_path / "frames")
    (tmp_path / "frames").mkdir()
    assert not ra.has_frames(tmp_path / "frames")
    (tmp_path / "frames" / "f.npz").write_bytes(b"0")
    assert ra.has_frames(tmp_path / "frames")


def test_not_covered_lists_no_script_that_runs():
    assert "run_sim_dense.py" not in " ".join(ra.NOT_COVERED)
