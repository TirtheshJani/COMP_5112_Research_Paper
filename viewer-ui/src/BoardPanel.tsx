import { useEffect, useState } from "react";
import outlines from "./outlines.json";
import { cellKey, HIGHLIGHT_MS } from "./state";

type Outline = { row: number; col: number; points: number[][] };
const { width: W, height: H, bleed: B } = outlines;
const PAD = 6; // mm around the puzzle, room for the highlight stroke
const AXIS = 14; // mm on the top and left for the one-based row and column numbers
const pieces = outlines.pieces as Outline[];
const pathOf = (p: Outline) => "M" + p.points.map(([x, y]) => `${x},${y}`).join("L") + "Z";

// The 7 x 5 board in front coordinates, drawn with the real cut lines. A placed piece shows its
// part of the printed picture; if the picture is missing it is a solid colour with its label.
export function BoardPanel({ placed, highlight }: { placed: string[]; highlight: { key: string; at: number } | null }) {
  const [picture, setPicture] = useState(true);
  const [lit, setLit] = useState<string | null>(null);

  useEffect(() => {
    if (!highlight) {
      setLit(null);
      return;
    }
    setLit(highlight.key);
    const t = window.setTimeout(() => setLit(null), HIGHLIGHT_MS);
    return () => window.clearTimeout(t);
  }, [highlight?.key, highlight?.at]);

  return (
    <section className="panel board" aria-label="Board">
      <svg data-testid="board" viewBox={`${-AXIS} ${-AXIS} ${W + AXIS + PAD} ${H + AXIS + PAD}`}>
        <defs>
          {pieces.map((p) => (
            <clipPath key={p.row * 10 + p.col} id={`clip-${p.row}-${p.col}`}>
              <path d={pathOf(p)} />
            </clipPath>
          ))}
        </defs>
        {Array.from({ length: outlines.cols }, (_, c) => (
          <text key={`c${c}`} className="axis" x={(c + 0.5) * (W / outlines.cols)} y={-AXIS / 2}>
            {c + 1}
          </text>
        ))}
        {Array.from({ length: outlines.rows }, (_, r) => (
          <text key={`r${r}`} className="axis" x={-AXIS / 2} y={(r + 0.5) * (H / outlines.rows)}>
            {r + 1}
          </text>
        ))}
        {pieces.map((p) => {
          const key = cellKey(p.row, p.col);
          const filled = placed.includes(key);
          const d = pathOf(p);
          return (
            <g
              key={key}
              data-testid={`piece-${p.row}-${p.col}`}
              data-filled={filled}
              data-highlight={lit === key}
              className={`piece${filled ? " filled" : ""}${lit === key ? " lit" : ""}`}
            >
              <path className="slot" d={d} />
              {filled && picture && (
                <image
                  href="/picture.png"
                  x={-B}
                  y={-B}
                  width={W + 2 * B}
                  height={H + 2 * B}
                  preserveAspectRatio="none"
                  clipPath={`url(#clip-${p.row}-${p.col})`}
                  onError={() => setPicture(false)}
                />
              )}
              {filled && !picture && (
                <text className="label" x={(p.col + 0.5) * (W / outlines.cols)} y={(p.row + 0.5) * (H / outlines.rows)}>
                  {p.row + 1},{p.col + 1}
                </text>
              )}
              <path className="edge" d={d} />
            </g>
          );
        })}
      </svg>
      <p className="caption">
        {placed.length} of {pieces.length} placed
      </p>
    </section>
  );
}
