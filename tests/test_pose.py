import cv2
import numpy as np

from jigsaw import types as T
from jigsaw.pose import piece_pose


def test_recovers_a_known_pose():
    K = np.array([[900, 0, 640], [0, 900, 360], [0, 0, 1]], float)
    rvec = np.array([0.2, -0.15, 0.4])
    tvec = np.array([-20.0, 10.0, 180.0])
    w = h = 12
    xs, ys = np.meshgrid(np.arange(w + 1, dtype=np.float32), np.arange(h + 1, dtype=np.float32))
    cells = np.dstack([xs, ys]).reshape(-1, 2)
    obj = np.hstack([cells * T.CELL_MM, np.zeros((len(cells), 1))])
    img, _ = cv2.projectPoints(obj, rvec, tvec, K, None)
    H, _ = cv2.findHomography(cells, img.reshape(-1, 2))
    r, t = piece_pose(H, K, None, (h, w))
    assert np.allclose(t, tvec, rtol=0.02, atol=1.0)
    assert np.degrees(np.linalg.norm(r - rvec)) < 2


def test_no_intrinsics_no_pose():
    assert piece_pose(np.eye(3), None, None, (5, 5)) is None


def test_distortion_argument_changes_the_pose_only_when_given():
    K = np.array([[900, 0, 640], [0, 900, 360], [0, 0, 1]], float)
    w = h = 12
    xs, ys = np.meshgrid(np.arange(w + 1, dtype=np.float32), np.arange(h + 1, dtype=np.float32))
    cells = np.dstack([xs, ys]).reshape(-1, 2)
    obj = np.hstack([cells * T.CELL_MM, np.zeros((len(cells), 1))])
    img, _ = cv2.projectPoints(obj, np.array([0.2, -0.15, 0.4]), np.array([-20.0, 10.0, 180.0]), K, None)
    H, _ = cv2.findHomography(cells, img.reshape(-1, 2))
    none = piece_pose(H, K, None, (h, w))
    zeros = piece_pose(H, K, np.zeros(5), (h, w))
    assert np.allclose(none[0], zeros[0]) and np.allclose(none[1], zeros[1])
    D = np.array([-0.3, 0.1, 0, 0, 0.0])
    assert not np.allclose(none[1], piece_pose(H, K, D, (h, w))[1])
