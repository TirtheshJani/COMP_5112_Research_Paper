"""Speak a sentence through the laptop speakers (audio fallback). Usage: python scripts/say.py "text" """
from __future__ import annotations

import argparse
import logging

from jigsaw.voice.tts import synthesize


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("text")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    import sounddevice as sd

    pcm, rate = synthesize(args.text)
    # UNVERIFIED: sounddevice docs (sd.play(array, samplerate), sd.wait()); not run here
    sd.play(pcm, rate)
    sd.wait()


if __name__ == "__main__":
    main()
