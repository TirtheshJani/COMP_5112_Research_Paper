// Coordinate conversions for the 3D panel (W8). Matrices are 4 x 4, row-major, as plain arrays.

export const MM = 0.01; // scene units per millimetre (1 unit = 100 mm)

export type Mat4 = number[];

// Rotation matrix (3 x 3, row-major) of an OpenCV Rodrigues vector.
export function rodrigues(r: number[]): number[] {
  const th = Math.hypot(r[0], r[1], r[2]);
  if (th < 1e-12) return [1, 0, 0, 0, 1, 0, 0, 0, 1];
  const [x, y, z] = r.map((v) => v / th);
  const c = Math.cos(th), s = Math.sin(th), C = 1 - c;
  return [
    c + x * x * C, x * y * C - z * s, x * z * C + y * s,
    y * x * C + z * s, c + y * y * C, y * z * C - x * s,
    z * x * C - y * s, z * y * C + x * s, c + z * z * C,
  ];
}

// Pose of the piece (object frame of jigsaw/pose.py: origin at the grid's cell (0, 0) corner, x along
// columns, y along rows, mm) in OpenCV camera coordinates, converted to the three.js frame of the camera:
// F = diag(1, -1, -1) applied to both rotation and translation, then millimetres scaled once.
export function poseToScene(rvec: number[], tvec: number[]): Mat4 {
  const R = rodrigues(rvec);
  const f = [1, -1, -1];
  const m: Mat4 = [];
  for (let i = 0; i < 3; i++) {
    m.push(f[i] * R[3 * i] * MM, f[i] * R[3 * i + 1] * MM, f[i] * R[3 * i + 2] * MM, f[i] * tvec[i] * MM);
  }
  return [...m, 0, 0, 0, 1];
}

// Robot frame (x forward, y left, z up) to three.js (x right, y up, z toward the viewer), so that the
// head's forward axis is -z, the direction the camera looks in the head group.
const C: Mat4 = [0, -1, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 1];
const Cinv: Mat4 = [0, 0, -1, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1];

// UNVERIFIED: frame of the `head` event pose (robot frame, x forward, z up, metres) is assumed from the
// Reachy Mini SDK docs (reachy_mini get_current_head_pose); no probe has checked it yet. Only the
// rotation is used: the head stays at the scene origin.
export function headToScene(pose: number[]): Mat4 {
  const rot = [...pose.slice(0, 3), 0, ...pose.slice(4, 7), 0, ...pose.slice(8, 11), 0, 0, 0, 0, 1];
  return mul(mul(C, rot), Cinv);
}

export function mul(a: Mat4, b: Mat4): Mat4 {
  const m: Mat4 = new Array(16).fill(0);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) m[4 * i + j] += a[4 * i + k] * b[4 * k + j];
  return m;
}

export function apply(m: Mat4, p: number[]): number[] {
  return [0, 1, 2].map((i) => m[4 * i] * p[0] + m[4 * i + 1] * p[1] + m[4 * i + 2] * p[2] + m[4 * i + 3]);
}
