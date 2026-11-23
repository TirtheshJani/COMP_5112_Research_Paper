"""Flask server for the projector view.

GET  /            the built UI (jigsaw/viewer/static, committed, so the demo needs no Node)
GET  /events      server-sent events, one JSON event per message (CONTRACTS section 5)
GET  /frame.jpg   latest camera JPEG, never cached (204 before the first frame)
GET  /picture.png the picture printed on the fronts, sliced by the board panel
POST /reset       clears the board on every page (publishes an empty board event)

serve(bus) runs this in a daemon thread. If the port is taken it logs a warning and returns None, so
the app loop carries on without a viewer.
"""
import json
import logging
import threading
from pathlib import Path

from flask import Flask, Response, abort, send_file
from werkzeug.serving import BaseWSGIServer, make_server

from jigsaw.viewer.events import EventBus

log = logging.getLogger(__name__)

STATIC = Path(__file__).parent / "static"
PICTURE = Path(__file__).resolve().parents[2] / "print" / "picture_portrait.png"
HEARTBEAT_S = 15.0


def create_app(bus: EventBus, static_dir: Path = STATIC, picture: Path | None = PICTURE) -> Flask:
    static_dir = Path(static_dir)
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="")

    @app.get("/")
    def index():
        page = static_dir / "index.html"
        if not page.is_file():
            return "Viewer UI is not built. Run: cd viewer-ui && npm run build", 503
        return send_file(page)

    @app.get("/events")
    def events():
        def stream():
            sub = bus.subscribe(heartbeat=HEARTBEAT_S)
            try:
                yield "retry: 1000\n\n"
                for event in sub:
                    yield ": ping\n\n" if event is None else f"data: {json.dumps(event)}\n\n"
            finally:
                sub.close()

        return Response(stream(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    @app.get("/frame.jpg")
    def frame():
        jpeg = bus.latest_frame()
        if jpeg is None:
            return "", 204
        return Response(jpeg, mimetype="image/jpeg", headers={"Cache-Control": "no-store, max-age=0"})

    @app.get("/picture.png")
    def picture_png():
        if picture is None or not Path(picture).is_file():
            abort(404)
        return send_file(picture)

    @app.post("/reset")
    def reset():
        bus.publish({"type": "board", "placed": []})
        return "", 204

    return app


def serve(bus: EventBus, port: int = 8765, host: str = "127.0.0.1", picture: Path | None = PICTURE) -> BaseWSGIServer | None:
    """Start the viewer in a daemon thread and return its server (call .shutdown() to stop), or None."""
    try:
        server = make_server(host, port, create_app(bus, picture=picture), threaded=True)
    except (OSError, SystemExit) as e:           # werkzeug prints the bind error and calls sys.exit(1)
        log.warning("viewer not started: port %d unavailable (%r)", port, e)
        return None
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="viewer", daemon=True).start()
    log.info("viewer at http://%s:%d/", host, port)
    return server
