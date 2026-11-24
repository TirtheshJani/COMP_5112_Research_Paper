"""Physical capture (S6 A8, A9) and offline decode (A10 to A12) on synthetic captures made with the renderer.

A fake operator hears each prompt and shows the piece: one frame of the empty mat, then one photograph held
still. Nothing here connects to a robot, plays sound or waits for a person.
"""
import ast
import csv
import importlib.util
import json
import re
from pathlib import Path

import cv2
import numpy as np
import pytest

from jigsaw import protocol
from jigsaw.fakes import FakeFrameSource
from jigsaw.render import MAT_BGR, photograph, piece_back
from jigsaw.types import PUZZLE_COLS, PUZZLE_ROWS, Frame

ROOT = Path(__file__).resolve().parents[1]
SIZE, PPC, ANGLES = (480, 480), 12, (0, 45)
COLUMNS = ("piece_row,piece_col,angle_deg,frame_file,kind,row,col,turn,reason,visible_cells,windows,px_per_cell,"
           "resolution,timestamp,commit").split(",")
PROMPT = re.compile(r"Piece row (\d+), column (\d+), angle (\d+)\.")
K = np.array([[500.0, 0, 240], [0, 500.0, 240], [0, 0, 1]])

# label (row, col, angle) -> what the operator really showed (row, col, angle)
SHOWN = {(0, 0, 45): (6, 4, 45), (1, 1, 0): (1, 1, 180)}
# label -> (index of a saved frame, the picture written over it after the capture): one wrong frame in an
# otherwise right presentation, for the decode. The capture itself saves no frame in which the piece moved.
SWAPPED = {(2, 2, 0): (3, (5, 0, 0))}


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_backs = {}


def picture(r, c, angle):
    if (r, c) not in _backs:
        _backs[r, c] = piece_back(r, c, PPC)
    return photograph(*_backs[r, c], np.random.default_rng(100 * r + 10 * c + angle), angle, size=SIZE, noise=2)


MAT = np.full((SIZE[1], SIZE[0], 3), MAT_BGR, np.uint8)


class Operator:
    """FrameSource and prompt/beep pair. Serves at most `limit` presentations, then the camera stops."""
    name = "operator"

    def __init__(self, limit=None, K=None):
        self.queue, self.prompts, self.beeps, self.limit, self.K = [], [], 0, limit, K

    def prompt(self, text):
        self.prompts.append(text)
        if self.limit is not None and len(self.prompts) > self.limit:
            return
        m = PROMPT.fullmatch(text)
        label = (int(m.group(1)) - 1, int(m.group(2)) - 1, int(m.group(3)))
        img = picture(*SHOWN.get(label, label))
        self.queue += [MAT] + [img] * (protocol.PRESENT_FRAMES + protocol.SET_FRAMES)

    def beep(self):
        self.beeps += 1

    def frames(self):
        t = 0.0
        while self.queue:
            t += 0.05
            yield Frame(self.queue.pop(0), t, self.K, None if self.K is None else np.zeros(5))

    def close(self):
        pass


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    out = tmp_path_factory.mktemp("frames")
    op = Operator()
    result = protocol.capture(op, out, op.prompt, op.beep, angles=ANGLES)
    for (r, c, a), (n, other) in SWAPPED.items():
        cv2.imwrite(str(out / protocol.folder_name(r, c, a) / f"f{n}.png"), picture(*other))
    return out, op, result


@pytest.fixture(scope="module")
def dp():
    return load("decode_physical")


@pytest.fixture(scope="module")
def decoded(captured, dp):
    return dp.decode_folder(captured[0], commit="abc1234")


# capture ---------------------------------------------------------------------------------------------------------

def test_capture_saves_every_presentation_with_its_label(captured):
    out, op, result = captured
    assert result == {"captured": 70, "skipped": 0, "complete": True}
    assert op.prompts[:3] == ["Piece row 1, column 1, angle 0.", "Piece row 1, column 1, angle 45.",
                              "Piece row 1, column 2, angle 0."]
    assert len(op.prompts) == 70 and op.beeps == 70
    folders = sorted(p for p in out.iterdir())
    assert len(folders) == PUZZLE_ROWS * PUZZLE_COLS * len(ANGLES)
    for f in folders:
        assert sorted(p.name for p in f.iterdir()) == [f"f{n}.{x}" for n in range(5) for x in ("json", "png")]
    side = json.loads((out / "r3_c1_a045" / "f2.json").read_text())
    assert (side["piece_row"], side["piece_col"], side["angle_deg"], side["frame"]) == (3, 1, 45, 2)
    assert side["resolution"] == "480x480" and side["K"] is None and side["time"]


def test_the_protocol_never_decodes():
    tree = ast.parse((ROOT / "jigsaw" / "protocol.py").read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("jigsaw"):
            imported |= {f"{node.module}.{a.name}" for a in node.names}
        elif isinstance(node, ast.Import):
            assert not any(a.name.startswith("jigsaw") for a in node.names)
    assert {m for m in imported if not m.startswith("jigsaw.types.")} == {"jigsaw.vision.paper_mask"}


def frames_of(images):
    return iter([Frame(img, n * 0.05, None, None) for n, img in enumerate(images)])


def test_wait_needs_a_change_then_a_still_piece():
    a, b = picture(3, 3, 0), picture(3, 3, 45)
    b_moved = np.roll(b, 60, axis=1)
    ref = protocol.paper_mask(a) > 0
    assert protocol.wait_for_piece(frames_of([a] * 20), ref) is None             # nothing changed
    assert protocol.wait_for_piece(frames_of([a] * 20), None) is None            # start: wait for an empty mat
    it = frames_of([a, a, b, b, b, b_moved, b, b, b, b, b, MAT])
    mask = protocol.wait_for_piece(it, ref)
    assert mask is not None and next(it).image is MAT                           # returned at the fifth still b
    it = frames_of([a, MAT, a, a, a, a, a, MAT])
    assert protocol.wait_for_piece(it, ref) is not None and next(it).image is MAT
    assert protocol.wait_for_piece(frames_of([a] * 5), ref, changed=True) is not None   # after a moved set


def saved_images(folder):
    return [cv2.imread(str(folder / f"f{n}.png"), cv2.IMREAD_COLOR) for n in range(protocol.SET_FRAMES)]


def test_a_set_is_saved_only_while_the_piece_stays_still(tmp_path):
    a = picture(3, 3, 0)
    jumped = np.roll(a, 60, axis=1)
    still, held = [a] * protocol.PRESENT_FRAMES, [a] * (protocol.PRESENT_FRAMES + protocol.SET_FRAMES)
    for name, images in [("left", [MAT, *still, a, a, MAT, *held]), ("jumped", [MAT, *still, a, jumped, *held])]:
        out = tmp_path / name
        beeps = []
        assert protocol.capture(FakeFrameSource(images), out, lambda text: None, lambda: beeps.append(1),
                                pieces=[(3, 3)], angles=(0,)) == {"captured": 1, "skipped": 0, "complete": True}
        assert beeps == [1] and all(np.array_equal(img, a) for img in saved_images(out / "r3_c3_a000")), name


def test_a_slow_turn_is_not_saved_mid_turn(tmp_path):
    # a steady turn of 0.6 degrees per frame from 0 to 45, then held: five frames of it stay within STILL_IOU
    # of the first (about 3.5 degrees on this rendering), ten frames do not
    back = piece_back(3, 3, PPC)

    def at(angle):
        return photograph(*back, np.random.default_rng(7), angle, size=SIZE, noise=2)

    turn = [at(0.6 * i) for i in range(76)]
    images = [MAT, *turn, *[at(45)] * 20]
    assert protocol.capture(FakeFrameSource(images), tmp_path, lambda text: None, lambda: None,
                            pieces=[(3, 3)], angles=(45,))["captured"] == 1
    final = protocol.paper_mask(at(45)) > 0
    overlaps = [protocol.iou(protocol.paper_mask(img) > 0, final) for img in saved_images(tmp_path / "r3_c3_a045")]
    assert min(overlaps) >= 0.95, overlaps


def test_resume_skips_what_exists_and_overwrites_nothing(tmp_path):
    pieces = [(0, 0), (4, 3)]
    first = Operator(limit=2)
    assert protocol.capture(first, tmp_path, first.prompt, first.beep, pieces=pieces, angles=ANGLES) == \
        {"captured": 2, "skipped": 0, "complete": False}
    before = {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in tmp_path.rglob("*") if p.is_file()}
    assert len(before) == 20
    (tmp_path / "r4_c3_a000.partial").mkdir()
    (tmp_path / "r4_c3_a000.partial" / "f0.png").write_bytes(b"left over")
    second = Operator()
    assert protocol.capture(second, tmp_path, second.prompt, second.beep, pieces=pieces, angles=ANGLES) == \
        {"captured": 2, "skipped": 2, "complete": True}
    assert second.prompts == ["Piece row 5, column 4, angle 0.", "Piece row 5, column 4, angle 45."]
    assert all((p.stat().st_mtime_ns, p.read_bytes()) == v for p, v in before.items())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["r0_c0_a000", "r0_c0_a045", "r4_c3_a000", "r4_c3_a045"]
    third = Operator()
    assert protocol.capture(third, tmp_path, third.prompt, third.beep, pieces=pieces, angles=ANGLES) == \
        {"captured": 0, "skipped": 4, "complete": True}
    assert third.prompts == []


def test_run_physical_prompts_through_the_robot_and_captures(tmp_path):
    rp = load("run_physical")
    robot = Operator(K=K)
    played = []
    robot.play = lambda pcm, rate: played.append((len(pcm), rate))
    robot.is_playing = lambda: False

    def synthesize(text):
        robot.prompt(text)
        return np.zeros(100, np.float32), 22050

    out = rp.main(["--out", str(tmp_path), "--pieces", "2,3"], robot=robot, synthesize=synthesize)
    assert out == {"captured": 8, "skipped": 0, "complete": True}
    assert robot.prompts[0] == "Piece row 2, column 3, angle 0." and len(robot.prompts) == 8
    assert played.count((100, 22050)) == 8 and len(played) == 16                # eight prompts, eight beeps
    side = json.loads((tmp_path / "r1_c2_a315" / "f4.json").read_text())
    assert np.allclose(side["K"], K)


# decode ----------------------------------------------------------------------------------------------------------

def test_turns_allowed_by_the_nominal_angle(dp):
    assert [sorted(dp.allowed_turns(a)) for a in range(0, 360, 45)] == \
        [[0], [0, 1], [1], [1, 2], [2], [2, 3], [3], [0, 3]]


def test_wilson_matches_published_values(dp):
    # Newcombe (1998), Statistics in Medicine 17:857, Table I, method 3 (score interval)
    for k, n, lo, hi in [(81, 263, 0.2553, 0.3662), (15, 148, 0.0624, 0.1605), (0, 20, 0.0, 0.1611),
                         (1, 29, 0.0061, 0.1718)]:
        got = dp.wilson(k, n)
        assert got == pytest.approx((lo, hi), abs=1e-4), (k, n, got)
    assert dp.wilson(20, 20)[1] == pytest.approx(1.0)


def test_one_row_per_frame_with_the_contract_columns(captured, decoded, dp, tmp_path):
    assert len(decoded) == 350
    path = tmp_path / "physical.csv"
    dp.write_csv(decoded, path)
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert reader.fieldnames == COLUMNS and len(rows) == 350
    first = rows[0]
    assert first["frame_file"] == "r0_c0_a000/f0.png" and first["commit"] == "abc1234"
    assert first["resolution"] == "480x480" and int(first["visible_cells"]) > 25 and int(first["windows"]) >= 1
    assert float(first["px_per_cell"]) == pytest.approx(PPC, rel=0.15)
    assert {r["kind"] for r in rows} <= {"correct", "rejected", "wrong"}
    rejected = [r for r in rows if r["kind"] == "rejected"]
    assert all(r["reason"] and r["row"] == "" for r in rejected)


def test_every_wrong_frame_is_a_deliberate_mislabel(decoded):
    """Hard-stop guard: a wrong row that the operator did not cause would be a wrong read (CLAUDE.md rule 5)."""
    expected = {}
    for label, shown in SHOWN.items():
        for n in range(5):
            expected[label, n] = shown
    for label, (n, shown) in SWAPPED.items():
        expected[label, n] = shown
    for r in decoded:
        if r["kind"] != "wrong":
            continue
        key = ((r["piece_row"], r["piece_col"], r["angle_deg"]), int(r["frame_file"][-5]))
        assert key in expected, f"WRONG READ not caused by a mislabel: {r}"
        row, col, angle = expected[key]
        assert (r["row"], r["col"]) == (row, col) and r["turn"] in protocol_turns(angle), r
    assert sum(r["kind"] == "wrong" for r in decoded) >= 9


def protocol_turns(angle):
    q, rem = divmod(angle % 360, 90)
    return {q % 4} if rem == 0 else {q % 4, (q + 1) % 4}


def test_label_check_catches_the_mislabelled_frames(decoded, dp):
    flags = dp.label_check(decoded)
    by_label = {(f["piece_row"], f["piece_col"], f["angle_deg"]): f for f in flags}
    assert set(by_label) == {(0, 0, 45), (1, 1, 0)}
    assert by_label[0, 0, 45]["problem"] == "piece" and by_label[0, 0, 45]["decoded"] == "row 7, column 5"
    assert by_label[1, 1, 0]["problem"] == "angle"
    single = [r for r in decoded if (r["piece_row"], r["piece_col"], r["angle_deg"]) == (2, 2, 0) and r["kind"] == "wrong"]
    assert [r["frame_file"] for r in single] == ["r2_c2_a000/f3.png"]


def write_sim(path):
    head = ("experiment,pattern,decoder,arm,px_per_cell,tilt,blur,noise,finger,n,correct,rejected,wrong,"
            "wrong_le1_misread,reads_le1_misread,mean_misread_cells,seed,commit")
    rows = ["puzzle,strong,grid,,8,0.0,0.0,0,False,1000,600,400,0,0,0,0,1,abc",
            "puzzle,strong,grid,,12,0.0,0.0,0,False,1000,950,50,0,0,0,0,1,abc",
            "puzzle,strong,grid,,12,0.05,1.0,4,False,1000,900,100,0,0,0,0,1,abc",
            "puzzle,strong,single,,12,0.0,0.0,0,False,1000,990,0,10,0,0,0,1,abc",
            "puzzle,orient,grid,,12,0.0,0.0,0,False,1000,940,50,10,0,0,0,1,abc",
            "puzzle,strong,grid,,24,0.0,0.0,0,False,1000,990,10,0,0,0,0,1,abc"]
    path.write_text("\n".join([head, *rows]) + "\n")


def test_decode_physical_writes_csv_summary_and_findings(captured, dp, tmp_path, capsys):
    sim = tmp_path / "sim_puzzle.csv"
    write_sim(sim)
    out, summary, findings = tmp_path / "physical.csv", tmp_path / "physical_summary.md", tmp_path / "findings"
    code = dp.main(["--frames", str(captured[0]), "--out", str(out), "--summary", str(summary), "--sim", str(sim),
                    "--findings", str(findings), "--allow-dirty"])
    assert code == 2                                                           # wrong reads present
    assert "WRONG READ: r2_c2_a000/f3.png" in capsys.readouterr().out
    text = summary.read_text()
    # prediction 4 compares only multiples of 90, where the robot like the simulation accepts one turn:
    # 35 primary frames at angle 0, one of them wrong (r1_c1_a000 shown upside down)
    assert "Robot, primary frames at nominal angles that are multiples of 90 (35 presentations): correct 34 (0.971" in text
    for needle in ["70 presentations", "Undistortion: off", "Prediction 1", "Prediction 4", "Nearest simulated px per cell: 12",
                   "| r0_c0_a045 | piece | row 7, column 5 |", "| r1_c1_a000 | angle |", "r2_c2_a000/f3.png"]:
        assert needle in text, needle
    assert text.count("| 12 | 0.05 | 1.0 | 4 | False |") == 1 and text.count("| 12 | 0.0 | 0.0 | 0 | False |") == 1
    assert "| 8 | 0.0 |" not in text and "| 24 | 0.0 |" not in text
    assert sorted(p.name for p in (findings / "r2_c2_a000").iterdir()) == ["f3.json", "f3.png"]
    assert len(list(out.read_text().splitlines())) == 351


def test_decode_physical_refuses_a_dirty_tree_without_allow_dirty(dp, monkeypatch, tmp_path):
    monkeypatch.setattr(dp, "git", lambda *args: " M jigsaw/app.py" if args[0] == "status" else "abc1234")
    assert dp.main(["--frames", str(tmp_path), "--out", str(tmp_path / "x.csv")]) == 1
    assert not (tmp_path / "x.csv").exists()


def test_an_unreadable_frame_stops_the_decode_and_names_the_file(dp, tmp_path):
    # a missing or corrupt PNG is a capture fault, not a decoder rejection: it must not enter the counts
    op = Operator()
    protocol.capture(op, tmp_path, op.prompt, op.beep, pieces=[(3, 2)], angles=(90,))
    (tmp_path / "r3_c2_a090" / "f2.png").write_bytes(b"not a png")
    with pytest.raises(ValueError, match=r"r3_c2_a090.f2\.png"):
        dp.decode_folder(tmp_path, commit="x")


def test_decode_with_undistort_reads_the_saved_intrinsics(dp, tmp_path):
    robot = Operator(K=K)
    protocol.capture(robot, tmp_path, robot.prompt, robot.beep, pieces=[(3, 2)], angles=(90,))
    rows = dp.decode_folder(tmp_path, commit="x", undistort=True)
    assert [r["kind"] for r in rows] == ["correct"] * 5 and rows[0]["turn"] == 1


def test_a_failed_imwrite_raises_and_leaves_no_complete_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol.cv2, "imwrite", lambda *a, **k: False)
    op = Operator()
    with pytest.raises(OSError, match="f0.png"):
        protocol.capture(op, tmp_path, op.prompt, op.beep, pieces=[(3, 2)], angles=(90,))
    assert not (tmp_path / "r3_c2_a090").exists()


@pytest.mark.parametrize("bad", ["8,1", "1,10", "0,1", "1,0", "2", "a,b", "1,2,3"])
def test_parse_pieces_rejects_out_of_range_or_malformed(bad):
    rp = load("run_physical")
    with pytest.raises(ValueError):
        rp.parse_pieces([bad])


def test_parse_pieces_accepts_the_corners():
    rp = load("run_physical")
    assert rp.parse_pieces(["1,1", f"{PUZZLE_ROWS},{PUZZLE_COLS}"]) == [(0, 0), (PUZZLE_ROWS - 1, PUZZLE_COLS - 1)]


def test_run_physical_main_exits_with_a_usage_error_on_a_bad_piece(tmp_path):
    rp = load("run_physical")
    with pytest.raises(SystemExit) as e:
        rp.main(["--out", str(tmp_path), "--pieces", "99,1"], robot=object(), synthesize=lambda t: None)
    assert e.value.code == 2


def test_decode_physical_uses_the_experiment_wilson(dp):
    from jigsaw.experiment.stats import wilson
    assert dp.wilson is wilson
    assert dp._share(7, 10).endswith("; {:.3f} to {:.3f})".format(*wilson(7, 10)))


def test_decode_physical_marks_a_dirty_run_in_the_commit_column(dp, monkeypatch, tmp_path):
    monkeypatch.setattr(dp, "git", lambda *args: " M jigsaw/app.py" if args[0] == "status" else "abc1234")
    seen = []
    monkeypatch.setattr(dp, "decode_folder", lambda frames, commit, undistort=False: seen.append(commit) or [])
    dp.main(["--frames", str(tmp_path), "--out", str(tmp_path / "x.csv"), "--summary", str(tmp_path / "s.md"),
             "--sim", str(tmp_path / "none.csv"), "--findings", str(tmp_path / "f"), "--allow-dirty"])
    assert seen == ["abc1234-dirty"]


def test_decode_physical_summary_does_not_call_a_wrong_frame_probably_operator_error(dp):
    assert "probably an operator error" not in Path(dp.__file__).read_text()
