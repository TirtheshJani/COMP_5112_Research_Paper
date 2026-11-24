"""Probe 4: one small nod and one small shake. MOVES THE ROBOT.

    python scripts/probes/p4_nod.py --host reachy-mini.local --move

Pitch and yaw of 10 degrees, 0.6 s each way, then back to neutral. Nothing moves without --move.
Uses goto_target(head=create_head_pose(...), duration=...) from reachy-mini 1.15.0.
UNVERIFIED: goto_target (reachy_mini.py:674, waits for the move at :724) and create_head_pose
(utils/__init__.py:14) on the real robot; p4 has run only on the mockup simulator and results/probes/p4.txt
is empty.
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="reachy-mini.local")
    ap.add_argument("--move", action="store_true")
    a = ap.parse_args()
    if not a.move:
        print("Dry run. Add --move to let the head move (10 degrees, slowly).")
        return
    from _tee import tee
    tee("p4")  # only a real run replaces results/probes/p4.txt; a dry run leaves the evidence alone
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose

    with ReachyMini(connection_mode="network", host=a.host) as mini:
        for kw in ({"pitch": 10}, {"pitch": -5}, {}, {"yaw": 10}, {"yaw": -10}, {}):
            mini.goto_target(head=create_head_pose(**kw, degrees=True), duration=0.6)
    print("done: nod and shake")


if __name__ == "__main__":
    main()
