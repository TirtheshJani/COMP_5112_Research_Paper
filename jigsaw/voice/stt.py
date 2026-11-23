"""Command recognition from 16 kHz microphone chunks. faster_whisper is imported inside functions only.

Voice activity detection is an energy threshold, not Silero, to keep this module free of onnx models.
Time is counted in audio samples, so VAD behaviour is deterministic with FakeAudioIn. Transcription runs
on one worker thread, so poll() never blocks for longer than one chunk read; a result is returned by a later poll().
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

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
    """Build a transcriber on faster-whisper, restricted by an initial prompt (V8).

    tiny.en is a deliberate choice for speed on the laptop; the spec suggests small.en. V8 (nine of ten) is not yet measured.
    """
    from faster_whisper import WhisperModel  # UNVERIFIED: faster-whisper README (WhisperModel(size, device, compute_type)), not run here

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def run(pcm: np.ndarray) -> str:
        # UNVERIFIED: transcribe(audio ndarray, language, initial_prompt, beam_size, temperature) from the faster-whisper README
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
        self.threshold = threshold  # RMS of a float32 chunk in [-1, 1]; untuned
        self._pool = ThreadPoolExecutor(max_workers=1)
        self._pending: list[Future] = []
        self._buf: list[np.ndarray] = []
        self._n = 0  # samples in the buffer
        self._speech = 0  # samples of speech in the buffer
        self._silence = 0  # trailing silent samples
        self._holdoff = 0  # samples still to ignore

    def warm(self) -> None:
        """Load the speech model now, so the first command does not pay for it."""
        if self._transcribe is None:
            self._transcribe = whisper_transcriber()

    def _reset(self) -> None:
        self._buf, self._n, self._speech, self._silence = [], 0, 0, 0

    def _run(self, pcm: np.ndarray) -> Command | None:
        self.warm()
        text = self._transcribe(pcm)
        cmd = match_command(text)
        log.info("heard %r -> %s", text, cmd)
        return cmd

    def _finish(self) -> None:
        pcm = np.concatenate(self._buf).astype(np.float32)
        speech_s = self._speech / RATE
        self._reset()
        if speech_s < MIN_UTTERANCE_S:
            log.info("utterance too short (%.2f s), ignored", speech_s)
            return
        self._pending.append(self._pool.submit(self._run, pcm))

    def _collect(self) -> Command | None:
        if self._pending and self._pending[0].done():
            return self._pending.pop(0).result()
        return None

    def poll(self) -> Command | None:
        """Read one chunk. Returns a command when a finished utterance has been recognised, else None."""
        if self.is_muted():
            self._reset()
            self._holdoff = int(HOLDOFF_S * RATE)
            self.audio_in.read()  # keep the microphone queue drained
            return None
        chunk = self.audio_in.read()
        done = self._collect()
        if chunk is None:
            return done
        chunk = np.asarray(chunk, dtype=np.float32).reshape(-1)
        if self._holdoff > 0:
            self._holdoff -= len(chunk)
            return done
        loud = len(chunk) > 0 and float(np.sqrt(np.mean(chunk**2))) >= self.threshold
        if loud:
            self._buf.append(chunk)
            self._n += len(chunk)
            self._speech += len(chunk)
            self._silence = 0
            if self._n >= MAX_UTTERANCE_S * RATE:
                self._finish()
        elif self._buf:
            self._buf.append(chunk)
            self._n += len(chunk)
            self._silence += len(chunk)
            if self._silence >= END_SILENCE_S * RATE:
                self._finish()
        return done

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
