"""Copy everything a probe prints, stdout and stderr (tracebacks, SDK warnings), into results/probes/<name>.txt."""
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "results" / "probes"


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()

    def flush(self):
        for st in self.streams:
            st.flush()


def tee(name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.txt"
    log = open(path, "w", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, log)
    sys.stderr = _Tee(sys.__stderr__, log)
    return path
