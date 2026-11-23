"""Pose of the piece relative to the camera, from the grid homography (for the 3D viewer)."""
import cv2
import numpy as np

from jigsaw import types as T


def piece_pose(H: np.ndarray, K: np.ndarray | None, D: np.ndarray | None,
               shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray] | None:
    """rvec, tvec (mm) of the read grid's cell (0, 0) corner. shape is GridRead.cells.shape."""
    if K is None:
        return None
    h, w = shape
    xs, ys = np.meshgrid(np.arange(w + 1, dtype=np.float32), np.arange(h + 1, dtype=np.float32))
    cells = np.dstack([xs, ys]).reshape(-1, 1, 2)
    img = cv2.perspectiveTransform(cells, H).reshape(-1, 2)
    obj = np.hstack([cells.reshape(-1, 2) * T.CELL_MM, np.zeros((len(img), 1), np.float32)])
    ok, rvec, tvec = cv2.solvePnP(obj, img, K, D if D is not None else np.zeros(5), flags=cv2.SOLVEPNP_ITERATIVE)
    return (rvec.ravel(), tvec.ravel()) if ok else None
