# S8 Verification, cross-review and demo readiness

> **v2 update (23 Nov).** Run with Fable 5.2, xhigh, Ultracode on. Add to the checks: rerun `tests/test_printing.py` and `tests/test_vision.py` from a clean clone; compare `results/physical.csv` against the answer key page; confirm no `UNVERIFIED` marks remain in `jigsaw/robot/`.

| | |
|---|---|
| Terminal | Opus 5.5 (or Fable 5.2), effort xhigh, Ultracode on |
| Branch and worktree | `chore/s8-verify` in `.worktrees/s8-verify`, created from `main` after S1 to S7 are merged |
| Depends on | every other workstream merged, or explicitly cut |
| Blocks | the Results text of the paper and the talk |
| Owns | `docs/jigsaw/VERIFICATION_REPORT.md`, `docs/jigsaw/DEMO_CHECKLIST.md`, `scripts/reproduce_all.py`, `results/_repro/` |
| Must not edit | any source file. Problems found are written up and fixed by a short follow-up session in the owning workstream's files |
| Skills | `karpathy-guidelines`, `verification-before-completion`, `dispatching-parallel-agents`, `engineering:code-review`, `scientific-critical-thinking`, `citation-check` (for numbers that go into the paper), `systematic-debugging` |

---

## Spec

### Problem

Seven workstreams were written by separate sessions that never saw each other's reasoning. Each passed its own tests. That does not show that the pieces agree on conventions, that the results can be regenerated from a clean clone, or that every number about to enter the paper traces to a file. This workstream checks those three things and prepares the demo.

### Goals

1. From a fresh clone, one command regenerates every result that does not need the robot, and the regenerated files equal the committed ones.
2. Every number that the paper will quote from this code is listed with the file, row and commit it comes from.
3. Each module has been reviewed by an agent that did not write it, with attention to the conventions that cross workstreams.
4. A one-page checklist for running the demo in the room on 30 Nov, with the fallback for each failure.

### Non-goals

- No new features and no refactoring.
- No rewriting of the paper. The output is a table of numbers and a list of statements the data support.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| Q1 | P0 | `scripts/reproduce_all.py`: clone the repository into a temporary folder, create the environment, run the tests, run `run_sim_dense.py` and `run_sim_puzzle.py` with the seeds recorded in the committed CSVs, run `make_figures.py`, run `decode_physical.py` on the stored frames if they are present | Exit code 0 |
| Q2 | P0 | Regenerated CSVs are identical to the committed ones except for the `commit` column | A diff table in the report; any difference is investigated before it is explained |
| Q3 | P0 | Number trace: a table with every count, rate and interval in `sim_summary.md` and `physical_summary.md`, its source file and row, and a recomputation from the CSV by independent code | All recomputations match exactly |
| Q4 | P0 | Convention audit across workstreams: turn direction, mirroring, zero-based and one-based indexing, image channel order, window offset used by the single-window decoder, the treatment of 45-degree angles | One paragraph per convention stating where it is defined, every place it is used, and whether all uses agree, with file and line |
| Q5 | P0 | End-to-end consistency test with no robot: for every piece and turn, render the back page from the S5 PDF, read it with S1, phrase it with S4, and check that the front tile at the announced position, after applying the announced turn, shows the right part of the picture the right way up | A new test file listed in the report as a recommended addition, with its result |
| Q6 | P0 | Review of each module by a fresh agent using `engineering:code-review` | Findings listed by severity; every critical finding has an owner and a status |
| Q7 | P0 | Contract check: every signature in `CONTRACTS.md` matches the code; every approved contract change is reflected in the document | Table of matches |
| Q8 | P0 | `UNVERIFIED` sweep: every remaining mark in the code and handoff notes is listed with what would verify it | List in the report |
| Q9 | P0 | Claims check for the paper: which of predictions 1 to 4 the data support, with the exact numbers, and the limits that must be stated (one robot, one room, how pieces were held, analysis unit, any runs discarded) | Section in the report; written with `scientific-critical-thinking` |
| Q10 | P0 | `DEMO_CHECKLIST.md` | See below |
| Q11 | P1 | Timing: frames per second of the full loop on the laptop with the robot, and time from presenting a piece to speech, from the S6 dry run logs | Stated in the report |

### The demo checklist must cover

- The evening before: charge the robot; confirm laptop and robot join the room's network or bring a travel router; update nothing.
- Thirty minutes before: start order (robot on, wait for Wi-Fi, stop the conversation app, `run_demo.py --source robot --viewer`, open the viewer on the projector), lighting check with one piece, volume check.
- During: the five pieces to show and their order, including one deliberately shown with a thumb over a cell to demonstrate a rejection.
- Fallbacks, each with the exact command: Wi-Fi fails (`--source replay` on the saved frames from the physical test, with the viewer); robot audio fails (laptop speakers through `scripts/say.py` path); robot will not connect (the recorded clip from S6 Task 7); viewer fails (terminal output only).
- After: stop the app, let the robot return to neutral, power off.

---

## Plan

### Task 1: Inventory

- [ ] Create the worktree. Read every `HANDOFF_*.md` and every `CONTRACT_CHANGE_*.md`. Write the list of what was built, what was cut, and what is still `UNVERIFIED` as the first section of the report.

### Task 2: Reproduction (Q1, Q2)

- [ ] Write `scripts/reproduce_all.py` as a plain sequence of subprocess calls with the seeds read from the committed CSVs. Run it. This takes as long as the original runs; start it first and continue with the other tasks while it runs.
- [ ] Diff the outputs. Any difference: `systematic-debugging` before anything else.

### Task 3: Parallel review (Q3 to Q8)

- [ ] Dispatch the subagents listed below in one batch. Each returns findings only.
- [ ] Merge their findings into the report. For every critical finding, open an issue naming the owning workstream and the smallest fix. Do not fix source files in this branch.

### Task 4: Claims and limits (Q9)

- [ ] Write the section from the two summary files and the trace table. One sentence per prediction: supported, not supported, or not tested, with numbers and intervals. Then the limits.
- [ ] Dispatch the sceptic subagent below and answer each of its points in the report.

### Task 5: Demo checklist (Q10, Q11). HUMAN for the rehearsal

- [ ] Write `DEMO_CHECKLIST.md`. Test every fallback command on the laptop.
- [ ] With the author: one full rehearsal following the checklist from a powered-off robot, timed. Record what went wrong and update the checklist.

### Task 6: Report and close

- [ ] Finish `VERIFICATION_REPORT.md`. Give the author a summary of at most fifteen lines: what is safe to put in the paper, what needs a fix first, and what remains unverified.

### Subagent use

With Ultracode on, Claude will orchestrate these itself. They are all read-only and independent, which is what makes this workstream suited to it.

1. Number tracer: "Using only pandas or the csv module, and without reading `jigsaw/experiment/stats.py` or `figures.py`, recompute every count, proportion and Wilson 95 percent interval that appears in `results/sim_summary.md` and `results/physical_summary.md` from the CSV files. Return a table: statement, value in the summary, your value, source file and row filter, match or mismatch."
2. Convention auditor: "For each of these conventions, find where it is defined and every place it is used across `jigsaw/`, `scripts/`, `viewer-ui/src/` and `tests/`: (a) direction of a quarter turn, (b) back-to-front column mirroring, (c) zero-based versus one-based row and column numbers, (d) BGR versus RGB, (e) which window the single-window decoder reads, (f) how nominal angles of 45, 135, 225, 315 degrees are labelled. Report each use with file and line and say whether it agrees with `docs/jigsaw/CLAUDE.md`. Do not edit files."
3. Contract checker: "Compare every signature, dataclass field, event field and CSV column in `docs/jigsaw/CONTRACTS.md` with the code and with the header rows of the CSV files in `results/`. Return a table of matches and mismatches."
4. One code reviewer per package (`decode` and `vision`, `experiment`, `robot`, `voice`, `app` and `protocol`, `viewer`), each with `engineering:code-review` and this instruction: "You did not write this code. Review it for correctness first, then for anything that could make a result in the paper wrong. List findings as critical, major or minor with file and line. Do not edit files."
5. End-to-end tester: "Write `tests/test_end_to_end_print_read_speak.py` implementing requirement Q5 of `docs/jigsaw/S8_verification.md`. Use only public functions. Run it and return the output. This is the one file you may create."
6. `UNVERIFIED` sweeper: "Search the repository for `UNVERIFIED` and for the same word in `docs/jigsaw/handoff/`. For each, say what probe or test would verify it and whether `results/probes/` already contains that evidence."
7. Sceptic (after Task 4): "Read the claims section of `docs/jigsaw/VERIFICATION_REPORT.md` and the two summary files. You are a reviewer for a theory conference who doubts the application section. Write the five strongest objections to the experimental claims, each tied to a specific number or procedure."

### What could go wrong

| If | Then |
|---|---|
| Regenerated CSVs differ | Most likely an unseeded random call or dependence on process scheduling in the parallel runner. Find it; the fix belongs to S2. The paper uses only numbers that reproduce |
| The convention audit finds a disagreement | Decide which side matches `CLAUDE.md`, write a failing test that shows the disagreement, and hand the test to the owning workstream |
| The end-to-end test fails for a subset of pieces | Almost certainly mirroring or turn wording. This is the reason the test exists; fix before the talk |
| A critical review finding touches a result already in the paper draft | Tell the author immediately, with the affected numbers |
| The rehearsal shows the room network blocks device-to-device traffic | Use a travel router or a phone hotspot that both devices join; test it in the rehearsal, not on the day |

### Definition of done

Reproduction passes or every difference is explained and assigned; trace table complete with all matches; convention audit clean or issues assigned; checklist rehearsed once; report delivered.
