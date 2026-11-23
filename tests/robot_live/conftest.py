"""Live tests on the Reachy Mini. Skipped unless JIGSAW_LIVE=1; JIGSAW_HOST sets the robot address.

    JIGSAW_LIVE=1 JIGSAW_HOST=10.0.0.100 uv run pytest tests/robot_live -o addopts="" -s
"""
import os

import pytest

if os.environ.get("JIGSAW_LIVE") != "1":
    collect_ignore_glob = ["test_*.py"]


@pytest.fixture(scope="session")
def robot():
    from jigsaw.robot.reachy import connect
    r = connect(os.environ.get("JIGSAW_HOST") or None)
    yield r
    r.close()
