import { useEffect, useRef } from "react";
import * as THREE from "three";
import { headToScene, type Mat4, MM, poseToScene } from "./scene";
import type { FrameEvent } from "./state";

const FOV_H_DEG = 70; // UNVERIFIED: default until K from HANDOFF_S3.md gives the camera's field of view
const FRUSTUM_MM = 400; // drawn depth of the field of view
const PIECE_MM = 36;

const IDENTITY: Mat4 = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const setRowMajor = (o: THREE.Object3D, m: Mat4) => {
  o.matrix.set(...(m as [number, number, number, number, number, number, number, number, number, number, number, number, number, number, number, number]));
  o.matrixWorldNeedsUpdate = true;
};

// Back of a piece as the camera sees it: white paper with a 10 x 10 cell grid.
function gridTexture(): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d")!;
  g.fillStyle = "#f4f4f0";
  g.fillRect(0, 0, 256, 256);
  g.strokeStyle = "#555";
  g.lineWidth = 3;
  for (let i = 0; i <= 10; i++) {
    const p = 1.5 + i * 25.3;
    g.beginPath();
    g.moveTo(p, 0);
    g.lineTo(p, 256);
    g.moveTo(0, p);
    g.lineTo(256, p);
    g.stroke();
  }
  return new THREE.CanvasTexture(c);
}

function frustumLines(aspect: number): THREE.LineSegments {
  const x = Math.tan((FOV_H_DEG * Math.PI) / 360) * FRUSTUM_MM * MM;
  const y = x / aspect;
  const z = -FRUSTUM_MM * MM;
  const c = [[-x, y, z], [x, y, z], [x, -y, z], [-x, -y, z]];
  const pts: number[] = [];
  c.forEach((p, i) => pts.push(0, 0, 0, ...p, ...p, ...c[(i + 1) % 4]));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  return new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0x7fb8ff }));
}

// Square of the piece's size in the object frame of jigsaw/pose.py (0..36 mm in x and y, z = 0).
function pieceMesh(): THREE.Mesh {
  const s = PIECE_MM;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute([0, 0, 0, s, 0, 0, s, s, 0, 0, s, 0], 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute([0, 1, 1, 1, 1, 0, 0, 0], 2));
  geo.setIndex([0, 2, 1, 0, 3, 2]);
  const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: gridTexture(), side: THREE.DoubleSide }));
  mesh.matrixAutoUpdate = false;
  return mesh;
}

function headMesh(): THREE.Group {
  const head = new THREE.Group();
  const shell = new THREE.Mesh(
    new THREE.SphereGeometry(55 * MM, 32, 16),
    new THREE.MeshStandardMaterial({ color: 0xdfe3e8, roughness: 0.6 }),
  );
  shell.scale.set(1.25, 0.8, 1);
  head.add(shell);
  for (const x of [-25, 25]) {
    const eye = new THREE.Mesh(new THREE.CircleGeometry(12 * MM, 24), new THREE.MeshBasicMaterial({ color: 0x111111 }));
    eye.position.set(x * MM, 8 * MM, -55.5 * MM);
    eye.rotation.y = Math.PI;
    head.add(eye);
  }
  return head;
}

// Head at the origin oriented by the head pose (identity until a head event), its field of view, and the
// read piece at rvec, tvec. Hidden piece when the pose is null.
export function ScenePanel({ frame, headPose }: { frame: FrameEvent | null; headPose: number[] | null }) {
  const host = useRef<HTMLDivElement>(null);
  const objs = useRef<{ rig: THREE.Group; piece: THREE.Mesh } | null>(null);

  useEffect(() => {
    const el = host.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0e12);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 2.5));
    const grid = new THREE.GridHelper(10, 20, 0x3a4350, 0x222a34);
    grid.position.y = -2.5;
    scene.add(grid);

    const rig = new THREE.Group(); // head frame; the camera looks down -z
    rig.matrixAutoUpdate = false;
    rig.add(headMesh(), frustumLines(1));
    const piece = pieceMesh();
    piece.visible = false;
    rig.add(piece);
    scene.add(rig);
    objs.current = { rig, piece };

    const view = new THREE.PerspectiveCamera(45, 1, 0.05, 100);
    view.position.set(5.2, 2.6, 3.4);
    view.lookAt(0, -0.2, -1.7);

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = el;
      renderer.setSize(w, h, false);
      view.aspect = w / Math.max(h, 1);
      view.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(el);
    resize();
    renderer.setAnimationLoop(() => renderer.render(scene, view));

    return () => {
      renderer.setAnimationLoop(null);
      observer.disconnect();
      renderer.dispose();
      el.removeChild(renderer.domElement);
      objs.current = null;
    };
  }, []);

  useEffect(() => {
    if (objs.current) setRowMajor(objs.current.rig, headPose ? headToScene(headPose) : IDENTITY);
  }, [headPose]);

  const rvec = frame?.rvec ?? null;
  const tvec = frame?.tvec ?? null;
  useEffect(() => {
    const o = objs.current;
    if (!o) return;
    o.piece.visible = !!(rvec && tvec);
    if (rvec && tvec) setRowMajor(o.piece, poseToScene(rvec, tvec));
  }, [rvec?.join(), tvec?.join()]);

  return (
    <section className="panel scene" aria-label="3D view">
      <div className="scene-host" ref={host} data-testid="scene" data-piece-visible={!!(rvec && tvec)} />
      <p className="caption">{rvec && tvec ? `Piece ${Math.round(Math.hypot(...tvec))} mm from the camera` : "No piece pose"}</p>
    </section>
  );
}
