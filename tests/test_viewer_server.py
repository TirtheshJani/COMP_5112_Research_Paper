import json
import logging
import socket
import urllib.request

import pytest

pytest.importorskip("flask")

from jigsaw.viewer.events import EventBus  # noqa: E402
from jigsaw.viewer.server import create_app, serve  # noqa: E402


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def client(bus, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>viewer</title>")
    pic = tmp_path / "pic.png"
    pic.write_bytes(b"\x89PNG fake")
    return create_app(bus, static_dir=tmp_path, picture=pic).test_client()


def _data(chunk: bytes) -> dict:
    line = chunk.decode().strip()
    assert line.startswith("data: ")
    return json.loads(line[len("data: "):])


def test_index_serves_built_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"<title>viewer</title>" in r.data


def test_index_without_build_says_so(bus, tmp_path):
    r = create_app(bus, static_dir=tmp_path / "missing").test_client().get("/")
    assert r.status_code == 503


def test_events_stream_delivers_published_events_in_order(bus, client):
    r = client.get("/events", buffered=False)
    assert r.mimetype == "text/event-stream"
    it = iter(r.response)
    assert next(it).startswith(b"retry: 1000")      # subscribed once the first chunk is out
    events = [{"type": "frame", "t": t, "grid": None, "rvec": None, "tvec": None,
               "decision": {"kind": "reject", "reason": "no_grid"}} for t in (1.0, 1.1, 1.2)]
    events.append({"type": "announce", "row": 3, "col": 1, "turn": 2, "text": "Row 4, column 2."})
    for e in events:
        bus.publish(e)
    assert [_data(next(it)) for _ in events] == events
    assert bus.n_subscribers() == 1
    r.close()                                       # the client went away: its subscription is dropped
    assert bus.n_subscribers() == 0


def test_events_stream_pings_when_idle(bus, tmp_path):
    c = create_app(bus, static_dir=tmp_path, heartbeat=0.05).test_client()
    r = c.get("/events", buffered=False)
    it = iter(r.response)
    next(it)
    assert next(it) == b": ping\n\n"
    r.close()


def test_frame_jpg_no_cache(bus, client):
    assert client.get("/frame.jpg").status_code == 204
    bus.set_frame(b"\xff\xd8jpeg")
    r = client.get("/frame.jpg?t=1.0")
    assert r.status_code == 200
    assert r.mimetype == "image/jpeg"
    assert r.data == b"\xff\xd8jpeg"
    assert "no-store" in r.headers["Cache-Control"]


def test_picture(client):
    r = client.get("/picture.png")
    assert r.status_code == 200
    assert r.data == b"\x89PNG fake"


def test_reset_publishes_empty_board(bus, client):
    sub = bus.subscribe()
    assert client.post("/reset", json={}).status_code == 204
    assert next(sub) == {"type": "board", "placed": []}


def test_reset_refuses_a_form_post(bus, client):
    # a cross-site page can send a form POST without a preflight, but not a JSON one
    assert client.post("/reset", data={"x": "1"}).status_code == 415
    assert bus.subscribe(heartbeat=0.01).__next__() is None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_serve_runs_in_background(bus):
    port = _free_port()
    srv = serve(bus, port=port)
    try:
        bus.set_frame(b"\xff\xd8x")
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/frame.jpg", timeout=5) as r:
            assert r.read() == b"\xff\xd8x"
    finally:
        srv.shutdown()
        srv.server_close()


def test_serve_twice_on_one_port_starts_only_one(bus, caplog):
    port = _free_port()
    first = serve(bus, port=port)
    try:
        with caplog.at_level(logging.WARNING):
            assert serve(bus, port=port) is None
        assert "viewer" in caplog.text.lower()
    finally:
        first.shutdown()
        first.server_close()


def test_serve_port_taken_warns_and_returns_none(bus, caplog):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        with caplog.at_level(logging.WARNING):
            assert serve(bus, port=port) is None
    assert "viewer" in caplog.text.lower()


def test_committed_build_is_served_with_its_assets(bus):
    """W10: the demo needs only Python; the committed build references only files that exist."""
    import re

    c = create_app(bus).test_client()
    page = c.get("/")
    assert page.status_code == 200
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', page.get_data(as_text=True))
    assert any(a.endswith(".js") for a in assets) and any(a.endswith(".css") for a in assets)
    for a in assets:
        assert c.get(a).status_code == 200, a
