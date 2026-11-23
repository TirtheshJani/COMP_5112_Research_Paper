# S6 App loop, steady filter and physical test

> **v2 update (23 Nov).** 35 pieces (7 x 5), front coordinates throughout, no `front_slot`. The app reads with `reader.PieceReader` and feeds `Stable`. The physical test is 35 pieces x 8 angles over the reading mat, logged with the CSV in CONTRACTS v2 section 6, using `scripts/probes/p3_live_read.py` as the starting point. Settle the turn sentence here. Working it through for a piece held up with the picture facing the person and the grid facing the robot (both upright): the robot sees the back turned k quarter turns counter-clockwise, so the person sees the picture turned k quarter turns clockwise, and the instruction is "turn it k quarter turns counter-clockwise" (k = 1: a quarter turn to the left; k = 2: upside down; k = 3: a quarter turn to the right). This is derived, not observed: check it on two real pieces at k = 1 and k = 3 before S4 records phrases, and write the result in the handoff.

| | |
|---|---|
| Terminal | Opus 5.5, effort high, Ultracode off |
| Branch and worktree | `feat/s6-app` in `.worktrees/s6-app` |
| Depends on | S1, S3 and S4 merged. Task 4 also needs `jigsaw/experiment/runner.py` and `stats.py` from S2 (merge S2 first, or cherry-pick those two files and their tests). S5 pieces printed for Tasks 5 and 6. S7 optional (the app publishes events whether or not a viewer is connected) |
| Blocks | S8, and the physical results in the paper |
| Owns | `jigsaw/stable.py`, `jigsaw/app.py`, `jigsaw/protocol.py`, `scripts/run_demo.py`, `scripts/run_physical.py`, `scripts/decode_physical.py`, `tests/test_stable.py`, `tests/test_app.py`, `tests/test_protocol.py`, `results/physical.csv`, `results/frames/` (ignored by git), `results/physical_summary.md` |
| Must not edit | core modules, `robot/`, `voice/`, `viewer/` |
| Human needed | Tasks 5, 6, 7 |
| Skills | `karpathy-guidelines`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `statistical-analysis`, `engineering:code-review` |

---

## Spec

### Problem

The parts exist separately: a decoder, a robot adapter, a voice. Two things still have to be built from them. The first is the live loop for the talk, in which a person holds up a piece and the robot answers once, clearly, and never with a wrong position. The second is the physical experiment for the paper: forty pieces at eight rotations, every frame saved, decoded afterwards with both decoders, and compared with the simulation.

### Goals

1. A demo loop that runs identically against the fakes, the renderer, a folder of saved frames and the robot.
2. An announcement only after three consecutive equal reads, exactly once per presentation of a piece.
3. A protocol script that collects about 320 labelled sets of frames without the operator touching the keyboard more than once per piece.
4. An offline script that produces `results/physical.csv` in the contract schema and a summary that tests predictions 1 and 4 of the paper.

### Non-goals

- No decision about which piece to pick up next, and no tracking of assembly progress beyond a set of announced pieces.
- No automatic detection of the true piece. The operator follows a fixed order, and the script checks the label.
- No retries that hide rejections. A rejected frame is logged as rejected.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| A1 | P0 | `Stable(need=3, miss_limit=15)` as in `CONTRACTS.md` | Tests below |
| A2 | P0 | `app.run(source, gestures, audio_out, bus=None, listener=None, decoder="four", max_frames=None)` implements the loop: frame, grey, optional undistort, `read_cells`, decode, `Stable`; on `announce`: publish events, speak, then nod; on `give_up`: publish, speak the rejection sentence, then shake | With `RenderSource` showing the same piece for 10 frames and fakes: exactly one `play` call and one `nod`. With 20 frames of a piece whose cells are corrupted: zero announcements, one `shake` |
| A3 | P0 | Never announce a wrong piece in tests | Over 200 rendered presentations with clutter, every announcement equals the truth |
| A4 | P0 | Frames that arrive while the robot is speaking or moving are discarded, and for the settling time measured by S3 probe 4 afterwards | Test with a fake clock |
| A5 | P0 | Events published to the bus follow `CONTRACTS.md` section 5; `bus=None` is allowed | Test collects events from a list-backed bus |
| A6 | P1 | Commands: `again` repeats the last announcement; `next` clears `Stable` so the same piece can be announced again; `stop` ends the loop; `ask` forces an immediate answer from the current frame if it decodes, else the rejection sentence | Tests with a scripted listener |
| A7 | P0 | `scripts/run_demo.py --source {robot,render,replay,mujoco} [--host] [--no-voice-in] [--viewer]` | Runs end to end with `--source render` on a machine with no robot |
| A8 | P0 | Protocol: for each piece in a fixed order and each of 8 nominal angles (0 to 315 in steps of 45), prompt by voice ("Piece row 2 column 3, angle 90"), wait until a quad has been visible for 5 consecutive frames, save the next 5 frames as PNG with a sidecar JSON (piece, nominal angle, time, resolution), then beep | `results/frames/` holds 40 x 8 x 5 files; a resume option continues after an interruption without overwriting |
| A9 | P0 | The protocol never decodes. Capture and decoding are separate, so the decoder cannot influence which frames are kept | Code inspection: `protocol.py` imports `vision.find_quad` only |
| A10 | P0 | `scripts/decode_physical.py` reads the saved frames, runs both decoders, and writes `results/physical.csv` | One row per frame and decoder; `kind` computed against the label; `misread_cells` computed against the true cells under the turn nearest the nominal angle |
| A11 | P0 | Label check | If more than half the frames of a presentation decode to the same piece and it is not the labelled piece, flag the presentation as a probable operator error in a separate column and exclude nothing automatically; list flagged presentations in the summary for the author to decide |
| A12 | P0 | `results/physical_summary.md`, generated: counts and Wilson intervals per decoder; prediction 1 (no wrong read with at most one misread cell); prediction 4 (robot proportions against the interval of the simulated proportions at the nearest pixels per cell and noise condition in `results/sim_puzzle.csv`) | File generated by the script from the CSVs |
| A13 | P1 | The turn sentence is confirmed with a real piece | Recorded in the handoff note; if wrong, a one-line fix request to S4 |

### Design notes

- The first frame of each presentation is the primary observation for the paper's physical test, and the five-frame set is kept for robustness. State this in the summary so that the analysis unit is clear: 320 presentations, not 1,600 independent reads.
- What 45-degree steps mean for the turn label. At nominal angle 45 the true quarter turn is ambiguous between two values. For angles that are multiples of 90, a wrong turn counts as wrong. For the odd multiples of 45, accept either adjacent turn as correct, and report the two groups separately.
- Order of speaking and moving. Speak, then gesture, unless S3 probe 4 showed that gestures do not disturb audio. Frames are ignored during both.
- Undistortion is applied if S3 recorded usable `K` and `D`. Keep it behind one flag and report in the summary whether it was on.
- Threading. One loop in the main thread. The command listener has its own worker inside `CommandListener`; the viewer server runs in its own thread started by `run_demo.py`. Do not add more.

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Settling time after speech and gesture | `HANDOFF_S3.md`, probe 4 | Yes for A4 (default 1.0 s) |
| Working distance and resolution | `HANDOFF_S3.md`, focus check | Yes for the physical test |
| How the piece is held (hand, or against a plain card) | Author. Default: against a light card, fingers on the border | No, but it is reported as a condition |

---

## Plan

### Task 1: Worktree, read the three handoff notes

- [ ] Create the worktree, `uv sync --extra dev --extra robot --extra voice --extra experiment`. Read `HANDOFF_S1.md`, `HANDOFF_S3.md`, `HANDOFF_S4.md`. List in your first message every item they mark `UNVERIFIED` that this workstream relies on.

### Task 2: Steady filter (A1)

- [ ] `tests/test_stable.py`:

```python
from jigsaw.types import Read, Reject
from jigsaw.stable import Stable

A, B = Read(1, 2, 0), Read(3, 4, 1)
NOQ, NOM = Reject("no_quad"), Reject("no_match")

def feed(s, seq):
    return [s.update(d) for d in seq]

def test_announces_once_after_three_equal_reads():
    assert feed(Stable(), [A, A, A, A, A]) == [None, None, "announce", None, None]

def test_interrupted_run_restarts():
    assert feed(Stable(), [A, A, NOM, A, A, A]) == [None, None, None, None, None, "announce"]

def test_new_piece_announces():
    assert feed(Stable(), [A, A, A, B, B, B]) == [None, None, "announce", None, None, "announce"]

def test_same_piece_again_after_it_left_view():
    assert feed(Stable(), [A, A, A, NOQ, NOQ, NOQ, A, A, A])[-1] == "announce"

def test_gives_up_once_after_fifteen_unreadable_frames():
    out = feed(Stable(), [NOM] * 20)
    assert out.count("give_up") == 1 and out.index("give_up") == 14

def test_no_quad_does_not_count_toward_giving_up():
    assert "give_up" not in feed(Stable(), [NOQ] * 40)

def test_disagreeing_reads_never_announce():
    assert "announce" not in feed(Stable(), [A, B, A, B, A, B])
```

- [ ] Run (fail), implement (about 35 lines), run (pass). Commit.

### Task 3: App loop (A2 to A7)

- [ ] `tests/test_app.py` using `RenderSource`, `FakeGestures`, `FakeAudioOut`, a list-backed bus and a stub `synthesize` (monkeypatched to return 0.1 s of silence). Cover A2, A3, A4, A5 and A6.
- [ ] Implement `app.run`. Target under 120 lines. Then `scripts/run_demo.py`.
- [ ] Run `uv run python scripts/run_demo.py --source render --no-voice-in --max-frames 200`. Expected: printed announcements that match the rendered truth, no exceptions. Commit.

### Task 4: Protocol and offline decode (A8 to A12)

- [ ] `tests/test_protocol.py` with `RenderSource` standing in for the camera and a fake prompt function: files and sidecars are written with the expected names; resume skips completed presentations.
- [ ] Test `decode_physical` on a small synthetic frame folder made by the renderer with known truth, including one deliberately mislabelled presentation (A11) and one frame with a flipped cell drawn into the image.
- [ ] Implement `protocol.py`, `scripts/run_physical.py`, `scripts/decode_physical.py` (which reuses `experiment.runner.classify`, `count_misread` and `experiment.stats.wilson` from S2). Commit.

### Task 5: Dry run on the robot. HUMAN: robot on, five printed pieces

- [ ] `uv run python scripts/run_demo.py --source robot --no-voice-in --viewer` (the viewer flag is a no-op if S7 is not merged). The author holds five different pieces at different angles. Record for each: announced, correct, time from presentation to speech.
- [ ] Confirm the turn sentence (A13): hold one piece so that the picture side, seen by the author, is rotated a quarter turn clockwise from upright. The robot should say to turn it a quarter turn counter-clockwise. Record the result.
- [ ] If anything is announced wrongly, stop. Save the frames. Use `systematic-debugging`. Do not continue to Task 6 until the cause is understood.

### Task 6: Physical test. HUMAN: all forty pieces, about 45 minutes

- [ ] Fix the conditions and write them at the top of `results/physical_summary.md` before starting: date, room, lighting, distance, resolution, card stock, how pieces are held, SDK version, commit hash.
- [ ] `uv run python scripts/run_physical.py --host <host> --out results/frames/run1`. The author follows the spoken prompts.
- [ ] `uv run python scripts/decode_physical.py --frames results/frames/run1 --out results/physical.csv`.
- [ ] Read the generated summary. Report to the author: the counts, whether predictions 1 and 4 held, and any flagged presentations. Commit the CSV and summary (frames stay out of git; note where they are stored).

### Task 7: Backup recording. HUMAN

- [ ] Record a two-minute screen and camera capture of the demo with five pieces, for use in the talk if the live demo fails.

### Task 8: Review, handoff, pull request

### Subagent use

- Tasks 2 and 4 are independent (different files; Task 4 needs only the core and S2's helpers). After Task 1, dispatch one general-purpose subagent for Task 4's capture half (`protocol.py`, `run_physical.py`, its tests) while the main session does Tasks 2 and 3. Keep `decode_physical.py` in the main session, because it carries the analysis decisions in the design notes.
- Before Task 6, one fresh subagent with `scientific-critical-thinking`: "Read the Spec section of `docs/jigsaw/S6_app_physical.md` and `jigsaw/protocol.py`. List every way the capture procedure could bias the result toward the hypothesis that strong-form patterns never give wrong reads (for example: frames dropped on failure, operator seeing decoder output, selection of frames). Return a list with a severity for each."
- Review subagent with `engineering:code-review` at the end: "Review `feat/s6-app`. Look for: any path where `app.run` can speak without `Stable` returning `announce`; frames being decoded while audio is playing; an exception in the listener or the bus stopping the loop; the turn-label rule for odd multiples of 45 degrees in `decode_physical.py`. Do not edit files."
- No subagent runs anything against the robot.

### What could go wrong

| If | Then |
|---|---|
| The robot announces a wrong piece | Finding. Save frames, count misread cells in them. Two or more misread cells explains it and is reportable; one or zero means a bug in vision, labelling or mirroring |
| Reject rate on the robot is high (over 30 percent) | Report it. Then, with the author, try one change at a time: distance, resolution, lighting, matte stock. Each change is a new run folder, and the summary lists all runs |
| A hand in view breaks the quad finder | Hold against a card; this is already the default condition |
| The simulation interval does not contain the robot rates (prediction 4 fails) | Report it as a result. Record which simulated condition was used for the comparison and why |
| Only part of the test is finished before the talk | The resume option keeps what exists. Report the number of presentations completed |
| Wi-Fi drops frames | `Stable` tolerates gaps. If the stream stalls for more than 5 seconds, the app says so and waits; it does not exit |

### Definition of done

Unit tests pass without a robot; demo runs on the robot for five pieces; `results/physical.csv` and summary committed; backup clip recorded; handoff written; pull request open.
