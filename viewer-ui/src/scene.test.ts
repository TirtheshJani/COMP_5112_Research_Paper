import { describe, expect, it } from "vitest";
import { apply, headToScene, MM, poseToScene, rodrigues } from "./scene";

const close = (a: number[], b: number[]) => a.forEach((v, i) => expect(v).toBeCloseTo(b[i], 9));

describe("rodrigues", () => {
  it("is the identity for a zero vector and a quarter turn about z", () => {
    close(rodrigues([0, 0, 0]), [1, 0, 0, 0, 1, 0, 0, 0, 1]);
    close(rodrigues([0, 0, Math.PI / 2]), [0, -1, 0, 1, 0, 0, 0, 0, 1]);
  });
});

describe("poseToScene: OpenCV camera (x right, y down, z forward) to three.js (x right, y up, z to viewer)", () => {
  it("puts a piece straight ahead in front of the camera, which looks down -z", () => {
    const m = poseToScene([0, 0, 0], [0, 0, 300]);
    close(apply(m, [0, 0, 0]), [0, 0, -300 * MM]);
  });

  it("keeps x, flips y and z, and scales millimetres once", () => {
    const m = poseToScene([0, 0, 0], [10, 20, 300]);
    close(apply(m, [0, 0, 0]), [10 * MM, -20 * MM, -300 * MM]);
    close(apply(m, [36, 0, 0]), [46 * MM, -20 * MM, -300 * MM]); // object x stays to the right
    close(apply(m, [0, 36, 0]), [10 * MM, -56 * MM, -300 * MM]); // object y (down the grid) goes down
  });

  it("applies the rotation before the axis flip", () => {
    // a quarter turn about the optical axis: object x points down the image (OpenCV +y), so up is -y in three
    const m = poseToScene([0, 0, Math.PI / 2], [0, 0, 300]);
    close(apply(m, [36, 0, 0]), [0, -36 * MM, -300 * MM]);
  });

  it("is row-major with a proper rotation (determinant +1 before scaling)", () => {
    const m = poseToScene([0.3, -0.2, 1.1], [5, 6, 300]);
    const [a, b, c, , d, e, f, , g, h, i] = m;
    expect(a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)).toBeCloseTo(MM ** 3, 12);
    close(m.slice(12), [0, 0, 0, 1]);
  });
});

describe("headToScene", () => {
  it("is the identity for the identity pose", () => {
    close(headToScene([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]), [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
  });

  it("maps a head pitched down (robot frame: x forward, y left, z up) to the camera looking down", () => {
    const a = Math.PI / 6; // positive rotation about robot y tips the forward axis down
    const pose = [Math.cos(a), 0, Math.sin(a), 0, 0, 1, 0, 0, -Math.sin(a), 0, Math.cos(a), 0, 0, 0, 0, 1];
    const forward = apply(headToScene(pose), [0, 0, -1]); // the camera looks down -z in the head group
    close(forward, [0, -Math.sin(a), -Math.cos(a)]);
  });

  it("maps a head turned to its left (positive yaw about robot z) to the camera looking toward -x", () => {
    const a = Math.PI / 4;
    const pose = [Math.cos(a), -Math.sin(a), 0, 0, Math.sin(a), Math.cos(a), 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
    close(apply(headToScene(pose), [0, 0, -1]), [-Math.sin(a), 0, -Math.cos(a)]);
  });

  it("maps a roll about robot x (forward) to a rotation about three.js z, leaving forward unchanged", () => {
    const a = Math.PI / 5; // positive roll: the robot's left side (y) goes up
    const pose = [1, 0, 0, 0, 0, Math.cos(a), -Math.sin(a), 0, 0, Math.sin(a), Math.cos(a), 0, 0, 0, 0, 1];
    const m = headToScene(pose);
    close(apply(m, [0, 0, -1]), [0, 0, -1]);
    close(apply(m, [-1, 0, 0]), [0, Math.sin(a), 0].map((v, i) => (i === 0 ? -Math.cos(a) : v)));
  });

  it("ignores the translation of the head pose", () => {
    close(apply(headToScene([1, 0, 0, 0.1, 0, 1, 0, 0.2, 0, 0, 1, 0.3, 0, 0, 0, 1]), [0, 0, 0]), [0, 0, 0]);
  });
});
