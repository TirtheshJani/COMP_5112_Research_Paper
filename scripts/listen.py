"""Print recognised commands from the laptop microphone. Usage: python scripts/listen.py"""
from __future__ import annotations

import argparse
import logging
import queue

from jigsaw.voice.stt import RATE, CommandListener


class _MicIn:
    rate = RATE

    def __init__(self):
        import sounddevice as sd

        self._q: queue.Queue = queue.Queue()
        # UNVERIFIED: sounddevice docs (InputStream callback signature, blocksize); not run here
        self._stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=1600, callback=self._cb)
        self._stream.start()

    def _cb(self, indata, frames, time_info, status):
        self._q.put(indata[:, 0].copy())

    def read(self):
        try:
            return self._q.get(timeout=0.5)
        except queue.Empty:
            return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    listener = CommandListener(_MicIn(), is_muted=lambda: False)
    listener.warm()
    print("listening; Ctrl-C to quit")
    while True:
        cmd = listener.poll()
        if cmd:
            print(cmd)


if __name__ == "__main__":
    main()
