"""Write the 35 jigsaw piece outlines (front view, mm) to viewer-ui/src/outlines.json for the board panel.

Usage: uv run python scripts/export_outlines.py [out.json]

The picture on the fronts covers the puzzle plus a bleed on every side (jigsaw/printing.py page_front),
so the board panel places it at (-bleed, -bleed) with size (width + 2 bleed, height + 2 bleed).
"""
import json
import sys
from pathlib import Path

from jigsaw import geometry as geo
from jigsaw import types as T

OUT = Path(__file__).resolve().parents[1] / "viewer-ui" / "src" / "outlines.json"
BLEED_MM = 4.0      # jigsaw/printing.py BLEED (not imported: printing needs reportlab)


def export(out: Path = OUT) -> None:
    pieces = [{"row": r, "col": c, "points": [[round(float(x), 2), round(float(y), 2)] for x, y in geo.outline(r, c)]}
              for r in range(T.PUZZLE_ROWS) for c in range(T.PUZZLE_COLS)]
    data = {"units": "mm", "rows": T.PUZZLE_ROWS, "cols": T.PUZZLE_COLS, "width": geo.W, "height": geo.H,
            "bleed": BLEED_MM, "pieces": pieces}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    export(path)
    print(f"wrote {path}")
