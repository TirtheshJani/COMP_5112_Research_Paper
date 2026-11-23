"""Build the print file: python scripts/make_print.py [picture.png] [out.pdf]"""
import sys
from pathlib import Path

from jigsaw.printing import build

root = Path(__file__).resolve().parent.parent
picture = sys.argv[1] if len(sys.argv) > 1 else root / "print" / "picture_portrait.png"
out = sys.argv[2] if len(sys.argv) > 2 else root / "print" / "reachy_debruijn_jigsaw.pdf"
build(str(picture), str(out))
