"""Probe 1: is the robot's daemon reachable? No SDK needed.

    python scripts/probes/p1_status.py [--host reachy-mini.local]

Prints the daemon status and the camera specs as JSON. Exit code 0 when both answer.
Endpoints read from the SDK source (reachy-mini 1.15.0: /api/daemon/status, /api/camera/specs);
both answered on the robot (results/probes/p1.txt, 23 Nov 2026).
"""
import argparse
import json
import sys
import urllib.request


def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())


def main():
    from _tee import tee
    tee("p1")
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="reachy-mini.local")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    base = f"http://{a.host}:{a.port}/api"
    ok = True
    for path in ("/daemon/status", "/camera/specs"):
        try:
            print(path, json.dumps(get(base + path), indent=2)[:2000])
        except Exception as e:  # noqa: BLE001 (a probe reports every failure)
            ok = False
            print(path, "FAILED:", repr(e))
    if not ok:
        print("\nIf this failed: is the robot on and on the same Wi-Fi? Try --host <robot IP> "
              "(the IP is shown in the Reachy Mini app or your router).")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
