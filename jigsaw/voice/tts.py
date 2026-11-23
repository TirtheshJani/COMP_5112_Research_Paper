"""Local speech synthesis with Piper. piper and onnxruntime are imported inside functions only."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np

from jigsaw.types import PUZZLE_COLS, PUZZLE_ROWS, Read
from jigsaw.voice.phrases import REJECT_DEFAULT, REJECT_SENTENCE, TURN_SENTENCE, phrase_read

log = logging.getLogger(__name__)

VOICE_NAME = "en_US-lessac-medium"  # same voice as ../rocky_mini (server/app.py:30), 22,050 Hz
VOICE_DIR = Path(__file__).resolve().parents[2] / "assets" / "voice"

_voice = None
_cache: dict[str, tuple[np.ndarray, int]] = {}


def voice_path() -> Path:
    """The .onnx file; JIGSAW_PIPER_VOICE overrides the default location."""
    return Path(os.environ.get("JIGSAW_PIPER_VOICE", VOICE_DIR / f"{VOICE_NAME}.onnx"))


def all_sentences() -> list[str]:
    """Every sentence the robot can say: 35 positions x 4 turns, plus the reject sentences."""
    reads = [phrase_read(Read(r, c, t)) for r in range(PUZZLE_ROWS) for c in range(PUZZLE_COLS) for t in TURN_SENTENCE]
    return reads + sorted({REJECT_DEFAULT, *REJECT_SENTENCE.values()})


def _load():
    global _voice
    if _voice is None:
        path = voice_path()
        if not path.exists():
            raise FileNotFoundError(f"Piper voice not found: {path}. See assets/voice/README.md")
        from piper import PiperVoice  # UNVERIFIED: API from piper-tts >= 1.3 and ../rocky_mini/server/app.py:170-176

        _voice = PiperVoice.load(str(path))
        log.info("loaded Piper voice %s", path)
    return _voice


def _render(text: str) -> tuple[np.ndarray, int]:
    voice = _load()
    # UNVERIFIED: piper-tts >= 1.3 yields AudioChunk objects from synthesize(text).
    chunks = [(c.audio_float_array, c.sample_rate) for c in voice.synthesize(text)]
    if not chunks:
        raise RuntimeError(f"Piper returned no audio for {text!r}")
    rate = chunks[0][1]
    pcm = np.concatenate([np.asarray(a, dtype=np.float32).reshape(-1) for a, _ in chunks])
    peak = float(np.abs(pcm).max())
    if peak > 1.0:
        log.warning("clipping %r: peak %.3f", text, peak)
    return np.clip(pcm, -1.0, 1.0).astype(np.float32), rate


def synthesize(text: str) -> tuple[np.ndarray, int]:
    """Mono float32 in [-1, 1] and the sample rate. Repeated calls are served from memory."""
    if text not in _cache:
        _cache[text] = _render(text)
    return _cache[text]


def warm_cache() -> int:
    """Synthesize every sentence once. Returns the number of sentences cached."""
    sentences = all_sentences()
    for s in sentences:
        synthesize(s)
    log.info("warm_cache: %d sentences", len(sentences))
    return len(sentences)
