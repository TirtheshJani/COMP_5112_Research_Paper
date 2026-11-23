# S7 Viewer: what the robot sees, in 3D, and the board filling in

> **v2 update (23 Nov).** The board is 7 rows x 5 columns of jigsaw pieces; draw the piece outlines from `jigsaw.geometry.outline(r, c)` (export them once to JSON for the UI). Frame events carry `grid` (four image corners of the read grid) instead of `quad` (CONTRACTS v2 section 5).

| | |
|---|---|
| Terminal | Sonnet 5.5, effort high, Ultracode off |
| Branch and worktree | `feat/s7-viewer` in `.worktrees/s7-viewer` |
| Depends on | S0 merged. Does not wait for S1, S3 or S6: it is built against a recorded event file |
| Blocks | nothing (the demo runs without it; a recorded clip is the fallback) |
| Owns | `jigsaw/viewer/` (`__init__.py`, `events.py`, `server.py`, `static/`), `viewer-ui/` (React 19, TypeScript, Vite, three), `scripts/replay_events.py`, `tests/test_viewer_*.py`, `tests/data/events_sample.jsonl` |
| Must not edit | everything else |
| Skills | `karpathy-guidelines`, `test-driven-development`, `frontend-design`, `verification-before-completion`, `playwright-skill`, `engineering:code-review` |

---

## Spec

### Problem

In the talk the audience cannot see what the robot's camera sees or why it answers as it does. A view on the projector should show the camera image with the detected piece outlined, a 3D scene with the robot's head, its field of view and the piece at its estimated position, and a 5 x 8 board on which each identified piece appears in its place.

### Goals

1. One page, served by the laptop, readable from the back of a room.
2. It updates within 200 ms of an event at 10 events per second.
3. It can be developed and tested with no robot and no other workstream, by replaying a file of events.
4. A failure in the viewer never affects the app loop.

### Non-goals

- No controls that drive the robot. The page is display only, plus one "reset board" button.
- No accounts, no database, no deployment beyond `localhost`.
- No model of the robot's body beyond a simple head shape. No loading of the SDK's MuJoCo meshes.
- No mobile layout. It is shown on a projector at 1920 x 1080.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| W1 | P0 | `EventBus` with `publish(event)`, `subscribe()` (a generator per client, bounded queue of 100, drops oldest when a client is slow), `set_frame(jpeg)`, `latest_frame()` | Unit tests: two subscribers both receive; a subscriber that never reads does not block `publish`; `publish` takes under 1 ms |
| W2 | P0 | Flask app: `GET /` serves the built UI, `GET /events` is a server-sent event stream, `GET /frame.jpg` returns the latest JPEG with no-cache headers, `POST /reset` clears the board state | Flask test client receives the events that were published, in order |
| W3 | P0 | `serve(bus, port=8765)` starts the server in a daemon thread and returns | Called from `run_demo.py --viewer`; the app loop continues if the port is taken (a warning is logged) |
| W4 | P0 | `scripts/replay_events.py tests/data/events_sample.jsonl --rate 10` publishes a recorded sequence in a loop, with JPEG frames from the renderer | The UI can be developed against it |
| W5 | P0 | Camera panel: the latest frame, with the quad drawn over it (green when the decision is a read, amber when rejected), and the decision text | Playwright test against the replay server: the overlay polygon has the quad's coordinates |
| W6 | P0 | Board panel: 5 x 8 grid in front coordinates; on `announce` the cell at `(front_row, front_col)` fills with that part of the picture (or a solid colour and label if no picture is configured) and is highlighted for 2 seconds | Playwright: after the sample sequence, exactly the announced cells are filled |
| W7 | P0 | Status line: the last spoken sentence in large type, and the give-up sentence when it occurs | Playwright |
| W8 | P1 | 3D panel with three.js: a head shape at the origin oriented by the `head` event (identity until one arrives), a view frustum from the camera's field of view, and a textured square of the piece's size at `rvec`, `tvec`; hidden when they are null | The scene renders at 30 frames per second on the laptop; a unit test checks the conversion from OpenCV camera coordinates (x right, y down, z forward) to the three.js scene |
| W9 | P0 | Reconnect: if the event stream drops, the page retries every second and shows "disconnected" | Playwright: stop and restart the replay server |
| W10 | P0 | Build output is committed to `jigsaw/viewer/static/` so that running the demo does not require Node | `run_demo.py --viewer` works after a fresh clone with Python only |

### Design notes

- Layout for a projector: camera panel left, 3D panel right, board along the bottom, status line across the top. Dark background, high contrast, minimum text size 28 px. Use the `frontend-design` skill for the visual treatment, but keep it plain; this accompanies a research talk.
- Server-sent events, not WebSockets: one direction, automatic reconnect in the browser, no extra dependency.
- The frame is fetched as an image on each `frame` event (`/frame.jpg?t=<t>`), not pushed through the event stream.
- The picture for the board is the same image file S5 uses for the fronts, if configured through `--picture`; the UI slices it with CSS background positions.
- Coordinate conversion for W8: OpenCV's camera frame has y down and z forward; three.js has y up and z toward the viewer. Convert with a fixed matrix `diag(1, -1, -1)` applied to both the rotation and the translation, and scale millimetres to scene units once. Put this in one function with a test.

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Camera field of view for the frustum | From `K` in `HANDOFF_S3.md`; default 70 degrees horizontal until then | No |
| Whether head pose events will be published | S6 publishes `head` only if S3 exposes the current head pose cheaply. The viewer works without them | No |

---

## Plan

### Task 1: Worktree, sample events

- [ ] Create the worktree. `uv sync --extra dev --extra viewer`.
- [ ] Write `tests/data/events_sample.jsonl` by hand from `CONTRACTS.md` section 5: about 60 events covering a piece appearing, three reads, an announce, the piece leaving, a rejected piece with a give-up, a second announce, and a board event.

### Task 2: Event bus and server (W1 to W4)

- [ ] `tests/test_viewer_events.py`:

```python
import time
from jigsaw.viewer.events import EventBus

def test_two_subscribers_receive_in_order():
    bus = EventBus(); a, b = bus.subscribe(), bus.subscribe()
    bus.publish({"type": "x", "n": 1}); bus.publish({"type": "x", "n": 2})
    assert [next(a)["n"], next(a)["n"]] == [1, 2] and next(b)["n"] == 1

def test_slow_subscriber_does_not_block_publish():
    bus = EventBus(); bus.subscribe()               # never read
    t = time.perf_counter()
    for n in range(1000): bus.publish({"n": n})
    assert time.perf_counter() - t < 0.5

def test_frame_storage():
    bus = EventBus(); assert bus.latest_frame() is None
    bus.set_frame(b"\xff\xd8\xff\xd9"); assert bus.latest_frame() == b"\xff\xd8\xff\xd9"
```

- [ ] Run (fail), implement `events.py` with `queue.Queue` per subscriber and a lock, run (pass).
- [ ] `tests/test_viewer_server.py` with Flask's test client: `/frame.jpg` returns 404 before a frame and the bytes after; `/events` yields `data: {...}\n\n` lines for published events (read a few with `stream=True`); `/reset` returns 204.
- [ ] Implement `server.py` and `scripts/replay_events.py`. Run the replay server and `curl -N localhost:8765/events` to see events arrive. Commit.

### Task 3: UI scaffold and panels (W5, W6, W7, W9)

- [ ] `npm create vite@latest viewer-ui -- --template react-ts`, add `three`. Configure the Vite dev server to proxy `/events`, `/frame.jpg` and `/reset` to `localhost:8765`, and the build to write to `../jigsaw/viewer/static/`.
- [ ] A `useEvents` hook wrapping `EventSource` with reconnect state. A reducer holding the latest frame event, the last announcement and the set of placed cells. Unit tests for the reducer with Vitest: feeding the sample events gives the expected placed cells.
- [ ] Components: `CameraPanel` (image plus SVG overlay scaled to the image), `Board`, `StatusLine`. Keep each under about 80 lines.
- [ ] Playwright tests (use the `playwright-skill`) against the replay server for W5, W6, W7, W9. Take a screenshot at 1920 x 1080 and look at it. Commit.

### Task 4: 3D panel (W8)

- [ ] Unit test for `cvToThree(rvec, tvec)` with two hand-computed poses (piece straight ahead at 200 mm; piece rotated 90 degrees about the optical axis).
- [ ] `Scene3D` component: a box and two cylinders for the head, a frustum of line segments, a plane with a canvas texture drawn from the 6 x 6 cells if the announce event is known, otherwise plain. Orbit controls disabled; a fixed three-quarter camera.
- [ ] Screenshot test that the plane is visible when pose is present and hidden when null. Commit.

### Task 5: Build, integrate, handoff

- [ ] `npm run build`; commit `jigsaw/viewer/static/`. From a fresh clone with Python only: `uv run python scripts/replay_events.py ...` and open the page.
- [ ] Review subagent. `HANDOFF_S7.md` with two screenshots. Pull request.

### Subagent use

- After Task 1, backend and frontend are independent because the event file is the contract between them. Dispatch two general-purpose subagents in parallel:
  - Backend: "In `.worktrees/s7-viewer`, implement W1 to W4 from `docs/jigsaw/S7_viewer.md` in `jigsaw/viewer/events.py`, `jigsaw/viewer/server.py`, `scripts/replay_events.py` and their tests only. Tests first. Follow `CLAUDE.md`. Return the test output and the exact command that starts the replay server."
  - Frontend: "In `.worktrees/s7-viewer/viewer-ui`, scaffold the Vite React TypeScript app and implement the reducer, `useEvents`, `CameraPanel`, `Board` and `StatusLine` for W5, W6, W7, W9. Use `tests/data/events_sample.jsonl` as fixture data for Vitest reducer tests. Do not write Python. Return the list of files and the Vitest output."
  The main session then runs both together, writes the Playwright tests, and does Task 4.
- Review subagent: "Review `feat/s7-viewer`. Check that a slow or disconnected browser cannot block `EventBus.publish`; that `serve` cannot raise into the caller; that the board uses front coordinates; and the sign conventions in `cvToThree`. Do not edit files."

### What could go wrong

| If | Then |
|---|---|
| Pose looks mirrored or upside down in 3D | The fixed conversion matrix is wrong; the unit test with hand-computed poses is the reference. Fix there only |
| The projector washes out the overlay colours | Use line thickness and labels as well as colour |
| S6 publishes an event field the UI does not expect | The reducer ignores unknown types and fields; add a test for that |
| Time runs short | Cut W8. The camera panel, board and status line are the P0 set |

### Definition of done

Python and Vitest tests pass; Playwright tests pass against the replay server; static build committed; screenshots in the handoff note; pull request open.
