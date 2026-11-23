"""Live tests on the Reachy Mini. Skipped, with the reason shown, unless JIGSAW_LIVE=1; JIGSAW_HOST sets the
robot address.

    JIGSAW_LIVE=1 JIGSAW_HOST=10.0.0.100 uv run pytest tests/robot_live -o addopts="" -s
"""
import os

import pytest


@pytest.fixture(scope="session")
def robot():
    if os.environ.get("JIGSAW_LIVE") != "1":
        pytest.skip("live robot test: not run; set JIGSAW_LIVE=1 (and JIGSAW_HOST) with the robot on")
    from jigsaw.robot.reachy import connect
    r = connect(os.environ.get("JIGSAW_HOST") or None)
    yield r
    r.close()
