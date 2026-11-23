# Risks and what-if scenarios

> **v2 update (23 Nov).** New risks with the frameless jigsaw: (1) the reader needs a coloured mat behind the piece; without it every frame is rejected (safe, but no demo), mitigation: bring a green card, or finish S1 P1; (2) fingers over the middle of a piece hide every complete window (11 of 60 rejected in the finger test, none wrong), mitigation: hold pieces by the knobs; (3) 3.6 mm cells need about 9 px per cell, so check p3 at the working distance; (4) a short-edge duplex flip puts the wrong grid behind every piece, mitigation: the alignment crosses, checked before cutting.

Today is 19 Nov. The talk is 30 Nov. The final paper date is not confirmed. This file lists what could happen, how likely it looks, what it would cost, and what to do. It also fixes the order in which things are cut.

## The schedule the plans assume

| Dates | Work | Terminals |
|---|---|---|
| 19 Nov | S0 | 1 |
| 20 to 22 Nov | S1, S3, S4, S5, S7 in parallel; focus check; first print | 5 |
| 22 to 25 Nov | S2 full runs; S6 app, dry run on the robot | 2 |
| 25 to 26 Nov | Physical test; backup clip | 1 plus the author |
| 27 to 28 Nov | S8; paper Results text; slides | 1 |
| 29 Nov | Rehearsal | |
| 30 Nov | Talk | |

There is about two days of slack. The scenarios below say where it goes.

## Scenarios

### 1. The robot's camera cannot read 5 mm cells at any comfortable distance

Likelihood: moderate. The estimate from the calibration constants is about 22 pixels per cell at 150 mm in the default 1280 x 720 mode, which is ample, but the lens's nearest focus distance over the WebRTC stream has not been measured, and video compression may soften edges.

Branches:
- Works at 40 mm pieces: no change.
- Works only with 60 mm pieces: S5 prints four pages; the puzzle is 300 x 480 mm. No other change.
- Works only at 1080p and resolution cannot be changed by a remote client: run the frame grabber on the robot over SSH with the local backend and feed saved frames to `ReplaySource`. The demo becomes near-live with a short delay. Costs half a day.
- Does not work: the physical test is dropped, the paper reports the two simulated experiments, and the talk shows the simulator and the rendered demo. The paper's main results do not depend on the robot.

Signal to watch: the S3 focus check. It is the first human task for this reason.

### 2. The WebRTC media stream does not work from the Windows laptop

Likelihood: low to moderate. The SDK ships GStreamer wheels for Windows, but this has not been run here, and the earlier project avoided GStreamer on Windows on purpose.

Response: one hour of debugging with the SDK troubleshooting page, then the SSH frame-grabber fallback above. Do not spend a day on it.

### 3. A wrong read appears on a strong-form pattern

Likelihood: low for single misreads (it would contradict a proved proposition, so it would mean a bug). Certain to be possible for reads with two or more misread cells.

Branches:
- One misread cell or none, and a wrong answer: a bug in vision, mirroring, turn labelling or the misread counter. Stop and debug. This is the most valuable thing the tests can find.
- Two or more misread cells: a real result. Report the rate. The paper already states that distance 2 gives no guarantee here and that the strong 3 x 3 torus did worse than the control on multi-error reads in the earlier simulation.

### 4. The experiments show no difference between the patterns under the four-window decoder

Likelihood: high. The 18 Nov pilot already found that the four-window decoder rejected every single misread on patterns without the strong form.

This is the expected outcome and the design was built around it: the dense-tori experiment under the single-window decoder is where the difference shows. The paper's honest statement is that the strong form matters when a reader has only one window, and that a consistency check over several windows gives similar protection on sparse patterns. Do not look for a condition that makes the puzzle show a difference.

### 5. The control patch has no pair of turned windows at distance 1

Likelihood: moderate for a 30 x 48 corner of a sparse torus. Then the "control" is strong-form by accident and the puzzle comparison is empty.

Response: S0 records it, and S2 scans for a control corner that does contain such pairs and reports both. If no corner does, the paper says so and relies on the dense tori.

### 6. Five terminals produce code that does not fit together

Likelihood: moderate without contracts, low with them.

Controls: S0 freezes the interfaces and ships fakes; each workstream owns a disjoint set of files; contract changes go through a written request; S8 audits conventions and adds an end-to-end test from PDF to spoken sentence.

Signal to watch: a workstream editing a file it does not own, or a pull request that changes `types.py`.

### 7. Usage limits or time run out with Ultracode on

Likelihood: moderate. Ultracode multiplies usage.

Response: it is on for S2 and S8 only. If limits are tight, run S2 at xhigh without Ultracode and dispatch only the exhaustive verifier subagent by hand; run S8 without Ultracode but keep subagents 1, 2 and 5 from its list.

### 8. The SDK changes during the week

Likelihood: moderate; the repository had a commit today.

Response: S3 pins the exact version on day one and nothing upgrades it before the talk.

### 9. The demo room is hostile (network isolation, bright projector light, noise)

Response: `DEMO_CHECKLIST.md` in S8. Voice input is off by default. A travel router or phone hotspot is tested in the rehearsal. The recorded clip is the last fallback.

### 10. The author has less time than planned

The human tasks are: focus check (20 minutes), print and cut (1 to 2 hours), listening test (10 minutes), dry run (30 minutes), physical test (45 minutes), rehearsal (30 minutes). About four hours in total, of which the focus check and printing are on the critical path.

## Cut order

Cut from the top. Never cut below the line.

1. MuJoCo frame source (S3 Task 6)
2. 3D panel of the viewer (S7 W8)
3. Voice input (S4 V7, V8; S6 A6)
4. The rest of the viewer (S7); use the recorded clip
5. Head gestures
6. Physical test on all 40 pieces; do 10 pieces at 8 angles and report it as a pilot

---

7. S6 demo loop on the robot with voice out
8. S2 experiments
9. S1, S0

## Decisions to make now

| Decision | Default if not made |
|---|---|
| Full cross or one-factor-at-a-time for the rendered puzzle sweep | Decided after S2's timing probe |
| Where the research code lives | Stays in the other folder; only pattern files are copied |
| Voice input in the talk | Built, off by default |
| How pieces are held in the physical test | Against a light card, fingers on the border |
