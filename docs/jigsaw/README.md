# Reachy Jigsaw: specs, plans and status (v2, 23 Nov 2026)

This folder holds the specs and plans for the software that lets a Reachy Mini Wireless read a two-sided jigsaw puzzle. Each `S*.md` file is one workstream (a spec, then a task-by-task plan) sized for one Claude Code terminal in its own git worktree. v2 (23 Nov) brings every file in line with the puzzle as printed: 35 real jigsaw pieces, picture on the front, one continuous strong-form de Bruijn grid on the back, no frames. Each workstream file starts with a "v2 update" box that overrides anything older below it.

Read in this order: this file, `CLAUDE.md`, `CONTRACTS.md`, then the workstream you are executing.

## What is being built

A person shows a piece grid-side up to the robot, over a coloured reading mat. The camera finds the grid, reads the cells it can see, and decodes every complete 5 x 5 window. All windows must agree on one placement; the piece is the one under the centre of the visible cells. The robot says the row, the column and how to turn the piece, and nods. The same reader feeds two simulated experiments and one physical test for the COMP 5112 paper, and the live demo for the talks on 30 Nov and 7 Dec.

```
frame source --> vision.read_grid --> decode.decode_grid --> stable filter --> voice + gesture
(robot | replay |  (mat silhouette,    (every complete      (3 equal reads)    viewer (3D + board)
 renderer)          grid lines,          5 x 5 window,                          CSV log
                    homography,          one placement)
                    cells + mask)             ^
                                   window table of the 72 x 52 back grid
```

All computation runs on the laptop. The robot supplies camera frames and microphone audio over WebRTC and plays speech and head movements.

## Status on 23 Nov

| ID | Workstream | Status |
|----|------------|--------|
| S0 | Foundation: repo, types, fakes, pattern files, CI | **Done** (built in chat on 23 Nov; 40 tests pass, ruff clean). Rerun on your PC to confirm |
| S1 | Decoders, frameless vision, renderer, pose, reader | **Done** for the reading-mat setup. Open: reading without a mat (P1) |
| S2 | Simulated experiments for the paper | To do (spec updated) |
| S3 | Robot I/O | **Started**: probes p1 to p4 written; p1 and p4 run against the SDK 1.15.0 simulator daemon; p2 and p3 need the robot |
| S4 | Voice | To do (spec updated) |
| S5 | Printing | **Done**: `print/reachy_debruijn_jigsaw.pdf` verified; builder in `jigsaw/printing.py`. Human: print, check, cut |
| S6 | App loop and physical test | To do (spec updated: 35 pieces, mat) |
| S7 | Viewer | To do (spec updated: 7 x 5 board) |
| S8 | Verification and rehearsal | To do |

## Order of execution from here

```
Now      You: rerun the tests on your PC; print the sheet; run probes p1 to p3 with the robot
Wave 1   S3   S4   S7                         three terminals in parallel
Wave 2   S2 (any time, needs only S1)   S6 (after S3 and S4)
Wave 3   S8
```

## Which model, which effort, Ultracode on or off

The copy-paste prompts, the skills for each terminal and the token-saving rules are in `PROMPTS.md`. Summary:

| ID | Model | Effort | Ultracode | Why |
|----|-------|--------|-----------|-----|
| S0 | none | | | Done. You rerun `uv run pytest` yourself |
| S1 remainder | Opus 5.5 | high | off | Optional: reading without a mat |
| S2 | Opus 5.5 | high | off | Numbers go into the paper; a Sonnet subagent makes the figures |
| S3 | Opus 5.5 | high | off | SDK details and the one physical robot; lookups go to the Haiku `sdk-scout` |
| S4 | Sonnet 5.5 | medium | off | Well-known local speech libraries and an exact prompt |
| S5 | none | | | Done. You print, check and cut |
| S6 | Opus 5.5 | high | off | Integration with you in the loop; produces the physical-test data |
| S7 | Sonnet 5.5 | high | off | Standard Flask and React work |
| S8 | Opus 5.5 | high | off | Parallel Sonnet `reviewer` subagents instead of Ultracode; Fable 5.2 optional for the claims check only |

No workstream uses xhigh or Ultracode: both multiply usage, and the prompts get the same independent checking from cheaper subagents. Use Haiku 5.5 only through the `sdk-scout` subagent.

How to start a terminal for a workstream:

```
cd C:\Users\TJ\Documents\GitHub\COMP_5112_Research_Paper
claude --model <model>
/effort <level>            (or /effort ultracode where the table says on)
> Read CLAUDE.md, docs/jigsaw/CONTRACTS.md and docs/jigsaw/S<N>_<name>.md (start with its v2 update box).
> Use the using-git-worktrees skill to create the worktree named in the file,
> then execute the plan with the executing-plans skill. Stop at every HUMAN step.
```

Model names and the Ultracode setting were checked on 19 Nov 2026. Confirm them in the `/model` and `/effort` menus of your installed version before starting.

## Rules that apply to every workstream

These are restated in `CLAUDE.md`, which S0 copies to the repo root.

1. Load the `karpathy-guidelines` skill first and follow it: state assumptions, write the minimum code, change only the files the workstream owns, and define a check for every step.
2. Use `test-driven-development`: write the failing test, run it, then write the code.
3. Use `systematic-debugging` before changing code in response to a failure.
4. Use `verification-before-completion` before saying a task is done. A task is done when its command has been run and its output matches the expected output in the plan.
5. Work in the worktree and branch named in the workstream file. Edit only the files listed under "Owns".
6. A wrong read on a strong-form pattern with at most one misread cell is a finding. Save the frame, stop, and report it. Do not tune it away.
7. Anything taken from Reachy Mini documentation but not run on the robot is marked `UNVERIFIED` in code comments and in the handoff note until a probe confirms it.
8. No em dashes in code, comments or documents.

## Subagents

Each workstream file has a "Subagent use" section. The general pattern:

- Explore subagents (read-only) for looking things up in the SDK clone or in `rocky_mini`. They return a short answer with file and line references, which keeps the main context small.
- General-purpose subagents for independent tasks that touch different files. The plan names which tasks may run in parallel and gives the prompt for each. Every prompt is self-contained: goal, files it may edit, files it must not edit, the test command, and what to return.
- One review subagent at the end of each workstream, using the `engineering:code-review` skill on the branch diff. It has not seen the implementation being written, so it reviews it cold.
- No parallel subagents for anything that connects to the robot or the daemon.

## Facts about the SDK that the plans rely on

Read from `reachy-mini` 1.15.0 on 23 Nov. "(sim)" means a probe ran it against the SDK's own daemon in mockup-simulator mode; "(probe)" means it still needs the robot.

- Python 3.11 or later; `pip install reachy-mini` (on Linux the GStreamer bindings need `libgirepository1.0-dev`; on Windows the wheels include GStreamer).
- `ReachyMini(connection_mode="network", host="reachy-mini.local")` connects to a remote robot; it is a context manager. Default port 8000. (sim)
- HTTP API under `/api`: `/api/daemon/status`, `/api/camera/specs`, `/api/state/full`. (sim)
- `mini.media.get_frame()` returns a BGR `(H, W, 3)` uint8 array or `None` (SDK docstring). (probe: p2)
- `mini.media.camera.K`, `.D`, `.resolution`; resolutions include 1280 x 720 at 30 and 60 fps, 1920 x 1080 and 2304 x 1296. (probe: p2, whether K and D come through WebRTC)
- `goto_target(head=create_head_pose(pitch=..., yaw=..., degrees=True), duration=...)` waits for the move to finish. (sim: p4)
- Media in the simulator needs the GStreamer webrtc plugin; without it the daemon starts but serves no camera. Camera work therefore needs the robot.
- The daemon owns the camera and audio. Stop the conversation app (`rocky_mini`) before the jigsaw app connects.

## Files in this folder

```
README.md             this file
PROMPTS.md            copy-paste prompts per terminal, models, skills, token rules
CLAUDE.md             rules for every Claude Code session (also at the repo root)
CONTRACTS.md          frozen interfaces (v2)
RISKS_WHAT_IF.md      scenario analysis and the cut order
S0 ... S8             one spec and plan per workstream, each with a v2 update box
handoff/              HANDOFF_S0, S1, S3_probes and S5 are written; others add theirs
reference/            jigsaw_proto.zip, the v1 prototype (framed squares), kept for history
```

The repo also has `.claude/agents/sdk-scout.md` (Haiku, read-only lookups) and `.claude/agents/reviewer.md` (Sonnet, code review), which the prompts use.
