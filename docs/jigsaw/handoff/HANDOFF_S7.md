# HANDOFF S7: viewer (23 Nov 2026)

Branch `feat/s7-viewer`, worktree `.worktrees/s7-viewer`, based on `de471c5`. Not pushed.

## What was built

| Req | Where | State |
|---|---|---|
| W1 | `jigsaw/viewer/events.py`: `EventBus.publish / subscribe(heartbeat=None) / set_frame / latest_frame / n_subscribers`. Each subscriber has its own queue of at most 100, and `publish` never waits on a client. When a slow client's queue is full its oldest *frame* event goes first, so board, announce, give_up and head events survive. The bus remembers the last board, the last sentence (cleared by an empty board) and the last head pose and replays them to each new subscriber, so a page opened or reconnected mid-demo shows the current board. `subscribe()` registers at once and returns a `Subscription` iterator; `close()` unregisters it, even before the first `next()`. | done |
| W2 | `jigsaw/viewer/server.py`: `create_app(bus, static_dir, picture, heartbeat=15.0)` with `GET /`, `GET /events` (SSE, `retry: 1000`, `: ping` every 15 s so a closed client is noticed), `GET /frame.jpg` (no-store, 204 before the first frame), `GET /picture.png`, `POST /reset` (JSON body only, which blocks cross-site form posts; publishes `{"type": "board", "placed": []}`). | done |
| W3 | `serve(bus, port=8765, host="127.0.0.1", picture=PICTURE)` returns the werkzeug server (call `.shutdown()`), or `None` with a warning if the port is taken. The port is probed with a plain `bind()` first, because werkzeug sets `SO_REUSEADDR` and on Windows a second viewer would otherwise bind the same port. Werkzeug calls `sys.exit(1)` on a bind error; `serve` catches it. The board picture path is logged. | done |
| W4 | `scripts/replay_events.py events.jsonl --rate 10 [--port 8765] [--loops 0]` and `tests/data/events_sample.jsonl` (39 events). Frames are rendered once from `jigsaw.render` (seeded by the event index) and their `grid` is the piece's 10 x 10 cell square mapped through the render transform, so the overlay sits on the piece. | done |
| W5 | Camera panel: frame swapped in only once loaded; SVG polygon with the `grid` points, green for a read, dashed amber for a reject that found a grid; decision text with a READ or REJECT tag (not colour alone). | done |
| W6 | Board panel: 7 x 5 SVG of the real outlines (`viewer-ui/src/outlines.json`, from `scripts/export_outlines.py`); a placed piece is clipped from `/picture.png` placed with the print bleed (`jigsaw/printing.py page_front`, 4 mm); highlight for 2 s; one-based row and column numbers. Without a picture a placed piece is a solid colour with its label. | done |
| W7 | Status line at 64 px: the last announce text, or the give-up sentence in amber. | done |
| W8 (P1) | 3D panel (three.js): head at the origin turned by the `head` pose, 70 degree field of view, the read piece as a 36 mm square at `rvec, tvec` (hidden when null). Conversion in `viewer-ui/src/scene.ts` with unit tests. | done |
| W9 | `useViewer` closes the `EventSource` on any error and reopens it after 1 s; footer shows "disconnected, retrying". | done |
| W10 | Build committed to `jigsaw/viewer/static/`; `tests/test_viewer_server.py::test_committed_build_is_served_with_its_assets` checks that it is served with Python only. | done |

Board semantics: `announce` adds its cell and highlights it; `board` replaces the set of filled cells; an empty `board` also clears the status line. A page that joins late receives the remembered announce, so that cell is highlighted for 2 s when the page loads.

## Commands and output

```
$ uv run pytest tests/test_viewer_events.py tests/test_viewer_server.py tests/test_viewer_outlines.py tests/test_viewer_replay.py
28 passed in 10.93s

$ uv run pytest
66 passed, 1 skipped in 129.58s (0:02:09)

$ uv run ruff check jigsaw/viewer scripts/replay_events.py scripts/export_outlines.py tests/test_viewer_*.py
All checks passed!

$ cd viewer-ui && npx vitest run
Tests  14 passed (14)

$ cd viewer-ui && npm run e2e        # rebuilds into jigsaw/viewer/static, then Playwright against replay_events.py
ok 1 W5: overlay polygon has the grid coordinates, green on a read and amber on a reject
ok 2 W5: the camera image is the server's latest frame
ok 3 W6: after the sample sequence exactly the announced cells are filled
ok 4 W6: an announced piece is highlighted for 2 s
ok 5 W6: reset clears the board
ok 6 W7: the status line shows the last spoken sentence and the give-up sentence
ok 7 W9: shows disconnected when the server stops and recovers when it restarts
ok 8 W8: the 3D panel shows the piece only while it has a pose, at 30 frames per second or more
ok 9 W6: a page opened mid-demo shows the current board at once
9 passed (1.9m)          # twice in a row
```

The W8 test counts three.js renders (`window.__sceneRenders`), not just animation frames. Headless Chromium on this machine reached 60 frames per second for the full page at 1920 x 1080. That was not measured on the demo laptop.

Rebuilding the UI produces the same asset hashes as the committed build (the reviewer checked this).

## How to run

```
uv sync --extra dev --extra viewer
uv run python scripts/replay_events.py tests/data/events_sample.jsonl --rate 10   # then open http://127.0.0.1:8765/
cd viewer-ui && npm install && npm run dev      # UI development, proxied to the replay server
cd viewer-ui && npx playwright install chromium && npm run e2e
uv run python scripts/export_outlines.py        # only if jigsaw/geometry.py changes
```

S6 wiring: `bus = EventBus(); serve(bus)`; for each frame call `bus.set_frame(jpeg)` and then `bus.publish(frame_event)`.

## UNVERIFIED

- `viewer-ui/src/scene.ts headToScene`: the `head` pose is assumed to be a 4 x 4 in the robot frame (x forward, y left, z up), from the Reachy Mini SDK docs. Only its rotation is used. No probe has checked it.
- `viewer-ui/src/ScenePanel.tsx FOV_H_DEG = 70`: default until `K` is in `HANDOFF_S3.md`. The frustum is drawn with aspect 1.
- The piece square is 36 mm from the grid's cell (0, 0) corner (object frame of `jigsaw/pose.py`). If S1's read grid includes margin cells or is smaller than the piece, the square is drawn offset. It is a square, not the piece outline. The camera-to-head offset is ignored: the camera is at the head's centre.

## Noticed outside my files

- `uv sync` failed with `invalid peer certificate: UnknownIssuer` because `SSL_CERT_FILE` points to a missing miniconda file; `SSL_CERT_FILE= UV_NATIVE_TLS=1 uv sync ...` works.
- `jigsaw/viewer/static` is not package data in `pyproject.toml`; it works from the repo (editable install), not from a built wheel. S0 owns `pyproject.toml`.
- The Spec text of `S7_viewer.md` still says "5 x 8" and "quad"; the v2 box and CONTRACTS v2 say 7 x 5 and `grid`. I followed v2.
- `scripts/export_outlines.py` copies `BLEED_MM = 4.0` from `jigsaw/printing.py`, which cannot be imported without reportlab. `test_bleed_matches_printing` reads the value from the source, so drift fails the test.
- The 1 remaining skip in the full suite belongs to another workstream.

## Open questions

- Should `POST /reset` also reach the app's board state (S6)? Now it only clears the viewers.
- Frame and JPEG are not matched by index. The page fetches the latest JPEG for each frame event, so at 30 fps the image can be a frame or two newer than the polygon. If that is visible on the projector, S6 could add a frame counter to the event and to `set_frame`.
- Events are shared between subscribers and serialised later. S6 must not change an event dict after publishing it (this is noted in the `events.py` docstring).

## Review

The `reviewer` subagent read `git diff de471c5..HEAD`. It ran the viewer pytest files (21 passed, 1 skipped), vitest (11 passed) and tsc (clean). It found no blockers. Its findings and what was done:

| # | Severity | Finding | Done |
|---|---|---|---|
| 1 | major | `serve()` on Windows: werkzeug's `SO_REUSEADDR` let a second viewer bind a port that was already serving, so `serve` returned a server instead of None | Probe with a plain `bind()` first; `test_serve_twice_on_one_port_starts_only_one` |
| 2 | major | A page opened or reconnected mid-demo had an empty board; a slow client could drop `announce` or `board` events for good | The bus replays board, status and head; full queues drop frames first; three bus tests and the e2e "page opened mid-demo" test |
| 3 | minor | The bleed check skipped without reportlab | The test reads `BLEED` from the `printing.py` source |
| 4 | minor | Piece square placement depends on S1's grid origin and margin | Documented under UNVERIFIED |
| 5 | minor | The head test checked one sign only | Exact pitch, yaw and roll cases, and translation ignored |
| 6 | minor | Dead SSE client and heartbeat untested | `n_subscribers() == 0` after the client closes; `heartbeat` argument and ping test |
| 7 | minor | The fps test measured requestAnimationFrame, not renders | It counts three.js renders |
| 8 | minor | The board picture is fixed to `print/picture_portrait.png` | `serve(picture=...)` already existed; the path is now logged at start |
| 9 | minor | `/reset` clears only the pages; cross-site POST possible | JSON body required (415 otherwise); S6 board listed as an open question |
| 10 | nit | Shared event dicts | Documented in the `events.py` docstring |
| 11 | nit | Tautological assert; tight timing bound | Assert replaced; bound loosened to 1 s |
| 12 | nit | `server_close()` missing in a test | Added |
| 13 | nit | JPEG can be newer than the polygon | Open question |
| 14 | nit | `performance.now()` inside the reducer | Time is stamped in the dispatch call |

While fixing finding 2, I also rewrote the e2e reset test. It used to restart the server, and the new server's empty board could hide a broken reset. It now clicks just after the first announce, waits for the 204, and checks that the board empties within 1 s, well before the loop would empty it.
