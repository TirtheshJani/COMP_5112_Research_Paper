import { useEffect, useState } from "react";
import { describeDecision, type FrameEvent } from "./state";

// Latest camera frame with the read grid drawn over it. The frame is fetched per frame event and
// swapped in only once loaded, so the picture never flashes blank.
export function CameraPanel({ frame }: { frame: FrameEvent | null }) {
  const [shown, setShown] = useState<{ src: string; w: number; h: number } | null>(null);

  useEffect(() => {
    if (!frame) return;
    const src = `/frame.jpg?t=${frame.t}`;
    const img = new Image();
    img.onload = () => setShown({ src, w: img.naturalWidth, h: img.naturalHeight });
    img.src = src;
    return () => {
      img.onload = null;
    };
  }, [frame?.t]);

  const kind = frame?.decision.kind;
  const w = shown?.w ?? 720;
  const h = shown?.h ?? 720;
  return (
    <section className="panel camera" aria-label="Camera">
      <div className="frame" style={{ aspectRatio: `${w} / ${h}` }}>
        {shown ? <img src={shown.src} alt="Robot camera" /> : <div className="empty">Waiting for the camera</div>}
        <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
          {frame?.grid && (
            <polygon
              data-testid="grid-overlay"
              data-kind={kind}
              className={kind}
              points={frame.grid.map(([x, y]) => `${x},${y}`).join(" ")}
            />
          )}
        </svg>
      </div>
      <p className={`decision ${kind ?? ""}`} data-testid="decision">
        {frame ? (
          <>
            <span className="tag">{kind === "read" ? "READ" : "REJECT"}</span>
            {describeDecision(frame.decision)}
          </>
        ) : (
          "No frame yet"
        )}
      </p>
    </section>
  );
}
