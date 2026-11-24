"""Pure helpers of probes 5 (motion and media) and 6 (focus check). No robot: the probes only run on Friday."""
import importlib.util
import sys
import time
import types
from pathlib import Path

import numpy as np
import pytest

from jigsaw.robot import reachy
from jigsaw.types import Frame, Read, Reject

PROBES = Path(__file__).resolve().parents[1] / "scripts" / "probes"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, PROBES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


p5 = load("p5_motion_media")
p6 = load("p6_focus")


# Probe 5: frame difference, still threshold, settling time, frame statistics

def test_frame_diff_is_the_mean_grey_level_change():
    a = np.full((720, 1280, 3), 100, np.uint8)
    assert p5.frame_diff(a, a.copy()) == 0
    assert p5.frame_diff(a, a + 10) == pytest.approx(10, abs=0.01)
    half = a.copy()
    half[:, :640] += 20                                    # half the picture changes by 20 grey levels
    assert p5.frame_diff(a, half) == pytest.approx(10, abs=0.01)


def test_still_threshold_is_twice_the_95th_percentile_of_still_differences():
    assert p5.still_threshold(np.linspace(0, 2, 101)) == pytest.approx(3.8)


def test_still_threshold_has_a_floor_of_half_a_grey_level():
    assert p5.still_threshold([0.0] * 10) == 0.5


TIMES = [k / 10 for k in range(21)]                        # 21 frames, 0.0 to 2.0 s


def test_settling_time_is_the_first_frame_after_the_gesture_that_starts_a_still_run():
    diffs = [10.0] * 8 + [0.1] * 12                        # pairs up to the frame at 0.8 s move
    assert p5.settling_time(TIMES, diffs, t_end=0.5, threshold=1.0, n_still=5) == pytest.approx(0.4)


def test_settling_time_restarts_after_a_single_moving_pair():
    diffs = [10.0] * 8 + [0.1] * 12
    diffs[10] = 10.0                                       # the frame at 1.1 s still moves
    assert p5.settling_time(TIMES, diffs, t_end=0.5, threshold=1.0, n_still=5) == pytest.approx(0.7)


def test_settling_time_when_frames_are_already_still_at_the_end_of_the_gesture():
    assert p5.settling_time(TIMES, [0.1] * 20, t_end=0.5, threshold=1.0, n_still=5) == pytest.approx(0.1)


def test_settling_time_is_none_when_frames_never_settle():
    assert p5.settling_time(TIMES, [10.0] * 20, t_end=0.5, threshold=1.0, n_still=5) is None


def test_frame_stats_counts_frames_and_the_largest_gap_inside_a_window():
    n, fps, gap = p5.frame_stats([0.0, 0.1, 0.2, 0.6, 0.7], 0.05, 0.75)
    assert n == 4 and fps == pytest.approx(4 / 0.7) and gap == pytest.approx(0.4)


def test_frame_stats_of_a_window_without_frames():
    assert p5.frame_stats([0.0, 0.1], 0.8, 1.0) == (0, 0.0, pytest.approx(0.2))


@pytest.mark.parametrize("settles, value", [([0.31, 0.456, 0.2], "0.46"), ([0.3, None], "none"), ([], "none")])
def test_report_ends_with_exactly_one_settling_line(settles, value):
    text = p5.report(["# Probe 5", "", "body"], settles)
    lines = text.rstrip("\n").split("\n")
    assert lines[-1] == f"settling_time_s: {value}"
    assert sum(line.startswith("settling_time_s:") for line in lines) == 1


class FailingCamera:
    def frames(self):
        yield Frame(np.zeros((90, 160, 3), np.uint8), 0.0, None, None)
        raise RuntimeError("camera gone")


def test_frame_log_join_raises_when_its_thread_failed():
    log = p5.FrameLog(FailingCamera())
    with pytest.raises(RuntimeError, match="frame thread") as err:
        log.join()
    assert "camera gone" in str(err.value.__cause__)
    assert log.times == [0.0]


class StubRobot:
    """Gives no frames until closed; nod() fails like a motor fault."""

    def __init__(self):
        self.closed = False

    def frames(self):
        while not self.closed:
            time.sleep(0.005)
        yield from ()

    def nod(self):
        raise RuntimeError("motor fault")

    def close(self):
        self.closed = True


@pytest.fixture
def p5_move_run(monkeypatch, tmp_path):
    """p5.main() with --move, output in tmp_path, no tee and no still phase; connect() is set by the test."""
    monkeypatch.setitem(sys.modules, "_tee", types.SimpleNamespace(tee=lambda name: None))
    monkeypatch.setattr(sys, "argv", ["p5_motion_media.py", "--move"])
    monkeypatch.setattr(p5, "OUT", tmp_path)
    monkeypatch.setattr(p5, "STILL_S", 0.0)
    return tmp_path


def test_p5_move_run_removes_an_old_report_before_it_connects(monkeypatch, p5_move_run):
    (p5_move_run / "motion_media.md").write_text("settling_time_s: 0.40\n", encoding="utf-8")

    def refuse(host):
        raise ConnectionError("no robot")
    monkeypatch.setattr(p5, "connect", refuse)
    with pytest.raises(ConnectionError):
        p5.main()
    assert not (p5_move_run / "motion_media.md").exists()


def test_p5_closes_the_robot_when_a_phase_fails(monkeypatch, p5_move_run):
    robot = StubRobot()
    monkeypatch.setattr(p5, "connect", lambda host: robot)
    with pytest.raises(RuntimeError, match="motor fault"):
        p5.main()
    closed = robot.closed
    robot.close()                                          # ends the frame thread if main did not
    assert closed


# Probe 6: pixels per cell, decision kind, summary, recommendation, report, CSV

def test_px_per_cell_of_a_scaled_rotated_and_shifted_grid():
    s, a = 12.0, np.deg2rad(30)
    H = np.array([[s * np.cos(a), -s * np.sin(a), 300], [s * np.sin(a), s * np.cos(a), 200], [0, 0, 1]])
    assert p6.px_per_cell(H, (10, 10)) == pytest.approx(12.0)


def test_px_per_cell_is_the_mean_of_the_two_cell_sides():
    assert p6.px_per_cell(np.diag([10.0, 14.0, 1.0]), (8, 6)) == pytest.approx(12.0)


def test_kind_checks_row_column_and_turn():
    assert p6.kind(Read(3, 1, 2), 3, 1, 2) == "correct"
    assert p6.kind(Read(3, 1, 0), 3, 1, 2) == "wrong"          # right cell, wrong turn
    assert p6.kind(Read(3, 2, 2), 3, 1, 2) == "wrong"
    assert p6.kind(Reject("no_grid"), 3, 1, 2) == "rejected"


def test_p6_needs_the_true_turn(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "_tee", types.SimpleNamespace(tee=lambda name: None))
    monkeypatch.setattr(sys, "argv", ["p6_focus.py", "--piece", "4", "2"])

    def refuse(host=None):
        raise ConnectionError("no robot in a unit test")
    monkeypatch.setattr(reachy, "connect", refuse)
    with pytest.raises(SystemExit) as err:
        p6.main()
    assert err.value.code == 2 and "--turn" in capsys.readouterr().err


def rows_for(resolution, distance, correct, rejected=0, wrong=0, px=12.0):
    kinds = ["correct"] * correct + ["rejected"] * rejected + ["wrong"] * wrong
    return [{"resolution": resolution, "distance_cm": distance, "frame": i, "piece": "R4 C2", "kind": k,
             "decision": k, "px_per_cell": None if k == "rejected" else px} for i, k in enumerate(kinds)]


def test_summarize_counts_each_condition_in_resolution_then_distance_order():
    rows = rows_for("1920x1080", 15, 20, px=27.0) + rows_for("1280x720", 30, 10, rejected=10, px=8.0) \
        + rows_for("1280x720", 15, 19, rejected=1, px=16.0) + rows_for("1280x720", 40, 0, rejected=20)
    s = p6.summarize(rows)
    assert [(c["resolution"], c["distance_cm"]) for c in s] == [("1280x720", 15), ("1280x720", 30), ("1280x720", 40),
                                                                ("1920x1080", 15)]
    assert (s[0]["frames"], s[0]["correct"], s[0]["rejected"], s[0]["wrong"]) == (20, 19, 1, 0)
    assert s[0]["read_rate"] == pytest.approx(0.95) and s[0]["median_px"] == pytest.approx(16.0)
    assert s[1]["read_rate"] == pytest.approx(0.5)
    assert s[2]["median_px"] is None


def test_recommend_prefers_the_highest_read_rate():
    s = p6.summarize(rows_for("1280x720", 15, 20) + rows_for("1280x720", 30, 19, rejected=1))
    assert (p6.recommend(s)["resolution"], p6.recommend(s)["distance_cm"]) == ("1280x720", 15)


def test_recommend_breaks_a_tie_by_the_larger_distance():
    s = p6.summarize(rows_for("1280x720", 20, 20) + rows_for("1920x1080", 30, 20))
    assert (p6.recommend(s)["resolution"], p6.recommend(s)["distance_cm"]) == ("1920x1080", 30)


def test_recommend_breaks_a_tie_at_one_distance_by_1280x720():
    s = p6.summarize(rows_for("1920x1080", 20, 20) + rows_for("1280x720", 20, 20))
    assert (p6.recommend(s)["resolution"], p6.recommend(s)["distance_cm"]) == ("1280x720", 20)


def test_recommend_needs_90_percent_correct_and_no_wrong_read():
    assert p6.recommend(p6.summarize(rows_for("1280x720", 20, 17, rejected=3))) is None
    assert p6.recommend(p6.summarize(rows_for("1280x720", 20, 19, wrong=1))) is None
    assert p6.recommend(p6.summarize(rows_for("1280x720", 20, 18, rejected=2)))["distance_cm"] == 20


def test_focus_report_has_a_row_per_condition_and_the_recommendation():
    s = p6.summarize(rows_for("1280x720", 20, 20) + rows_for("1280x720", 40, 2, rejected=18))
    text = p6.report(s, p6.recommend(s))
    assert "| 1280x720 | 20 | 20 | 20 | 0 | 0 | 1.00 | 12.0 |" in text
    assert "| 1280x720 | 40 | 20 | 2 | 18 | 0 | 0.10 | 12.0 |" in text
    assert "Recommended: 1280x720 at 20 cm" in text
    assert "Recommended: none" in p6.report(s[1:], None)


def test_csv_round_trip_keeps_missing_px_per_cell(tmp_path):
    rows = rows_for("1280x720", 30, 1, rejected=1, px=8.25)
    path = tmp_path / "focus_1280x720.csv"
    p6.write_rows(path, rows)
    assert p6.read_rows([path]) == rows


def test_p4_dry_run_does_not_open_its_log(monkeypatch, capsys):
    p4 = load("p4_nod")
    teed = []
    monkeypatch.setitem(sys.modules, "_tee", types.SimpleNamespace(tee=teed.append))
    monkeypatch.setattr(sys, "argv", ["p4_nod.py"])
    p4.main()
    assert "Dry run" in capsys.readouterr().out
    assert teed == []                                       # results/probes/p4.txt is committed evidence
