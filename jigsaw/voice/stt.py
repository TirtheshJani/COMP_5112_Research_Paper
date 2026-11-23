"""Command recognition from 16 kHz microphone chunks. faster_whisper is imported inside functions only.

Voice activity detection is an energy threshold, not Silero, to keep this module free of onnx models.
Time is counted in audio samples, so behaviour is deterministic and testable with FakeAudioIn.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np

from jigsaw.types import AudioIn
from jigsaw.voice.commands import Command, match_command

log = logging.getLogger(__name__)

RATE = 16000
MIN_UTTERANCE_S = 0.3
MAX_UTTERANCE_S = 4.0
END_SILENCE_S = 0.4
HOLDOFF_S = 0.5  # ignore input this long after the robot stops speaking
PROMPT = "where does this go, again, repeat, next piece, stop, that's enough"

Transcriber = Callable[[np.ndarray], str]


def whisper_transcriber(model_size: str = "tiny.en") -> Transcriber:
    """Build a transcriber on faster-whisper, restricted by an initial prompt (V8)."""
    from faster_whisper import WhisperModel  # UNVERIFIED: API from faster-whisper docs, not run here

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def run(pcm: np.ndarray) -> str:
        segments, _ = model.transcribe(pcm, language="en", initial_prompt=PROMPT, beam_size=1, temperature=0.0)
        return " ".join(s.text for s in segments).strip()

    return run


class CommandListener:
    def __init__(
        self,
        audio_in: AudioIn,
        is_muted: Callable[[], bool],
        transcribe: Transcriber | None = None,
        threshold: float = 0.02,
    ):
        self.audio_in = audio_in
        self.is_muted = is_muted
        self._transcribe = transcribe
        self.threshold = threshold  # RMS of a float32 chunk in [-1, 1]
        self._buf: list[np.ndarray] = []
        self._speech = 0  # samples of speech in the buffer
        self._silence = 0  # trailing silent samples
        self._holdoff = 0  # samples still to ignore

    def _reset(self) -> None:
        self._buf, self._speech, self._silence = [], 0, 0

    def _finish(self) -> Command | None:
        pcm = np.concatenate(self._buf).astype(np.float32)
        speech_s = self._speech / RATE
        self._reset()
        if speech_s < MIN_UTTERANCE_S:
            log.info("utterance too short (%.2f s), ignored", speech_s)
            return None
        if self._transcribe is None:
            self._transcribe = whisper_transcriber()
        text = self._transcribe(pcm)
        cmd = match_command(text)
        log.info("heard %r -> %s", text, cmd)
        return cmd

    def poll(self) -> Command | None:
        """Read one chunk. Returns a command when an utterance ends, else None."""
        chunk = self.audio_in.read()
        if chunk is None:
            return None
        chunk = np.asarray(chunk, dtype=np.float32).reshape(-1)
        if self.is_muted():
            self._reset()
            self._holdoff = int(HOLDOFF_S * RATE)
            return None
        if self._holdoff > 0:
            self._holdoff -= len(chunk)
            return None
        loud = float(np.sqrt(np.mean(chunk**2))) >= self.threshold if len(chunk) else False
        if loud:
            self._buf.append(chunk)
            self._speech += len(chunk)
            self._silence = 0
            if len(self._buf) and sum(len(b) for b in self._buf) >= MAX_UTTERANCE_S * RATE:
                return self._finish()
            return None
        if not self._buf:
            return None
        self._buf.append(chunk)
        self._silence += len(chunk)
        if self._silence >= END_SILENCE_S * RATE:
            return self._finish()
        return None
