# HANDOFF S4: voice

Branch `feat/s4-voice` (worktree `.worktrees/s4-voice`). Not pushed.

## Built
- `jigsaw/voice/phrases.py`: `phrase_read(read)`, `phrase_reject(reason)`, `TURN_SENTENCE`. Left/right wording as in the S4 prompt.
- `jigsaw/voice/commands.py`: `match_command(text)`. Order: stop, again, next, ask.
- `jigsaw/voice/tts.py`: `synthesize`, `warm_cache`, `all_sentences` (35 x 4 + 3 reject sentences = 143), in-memory cache.
- `jigsaw/voice/stt.py`: `CommandListener(audio_in, is_muted, transcribe=None).poll()`, plus `warm()` and `close()`.
  Energy VAD; transcription on one worker thread, so a result arrives on a later `poll()`.
- `scripts/say.py`, `scripts/listen.py`, `assets/voice/README.md` and `.gitignore`, `voice` extra in `pyproject.toml`.

## Commands run
- `..\..\.venv\Scripts\python.exe -m pytest tests/test_voice_*.py` gives `44 passed, 3 skipped`.
- Full suite before the review fixes: `81 passed, 3 skipped in 73.27s`. Not re-run after the fixes (only voice files changed).
- `ruff check .` gives `All checks passed!`. Real-character dash check on all changed files: none.
- `uv run` could not create a venv in the worktree (certificate error, `UnknownIssuer`), so the main checkout's `.venv` python was used.

## UNVERIFIED (marked in code)
- Piper: nothing ran. `piper-tts` is not installed (same certificate problem). `tts._load` and `_render` follow piper-tts >= 1.3
  (`AudioChunk.audio_float_array`, `sample_rate`). `../rocky_mini/server/app.py` uses the older `synthesize_wav`.
- The 3 skipped tests need the voice file (`en_US-lessac-medium.onnx` exists at `../rocky_mini/`, not copied here).
  So V4 (1 to 6 s, no clipping) and V5 (warm under 60 s, cached call under 5 ms) are untested.
- faster-whisper and sounddevice calls are unverified. V7 with real WAV files and V8 (nine of ten spoken commands) are unmeasured:
  no WAV fixtures exist and Task 5 (human listening test) has not been done. The VAD threshold 0.02 is untuned.
- `uv.lock` is not updated for the new `voice` extra (no network).

## Decisions and deviations
- Turn 1 and 3 say "to the left / to the right" (prompt) while the spec notes say counter-clockwise / clockwise. S6 must confirm on a real piece.
- 143 sentences, not 161: the spec count is from the old 40-position layout.
- `tiny.en` instead of the spec's `small.en`, for speed; revisit when V8 is measured.
- Energy VAD instead of Silero, to avoid an onnx model dependency.

## Review (reviewer subagent): 12 findings, none critical, all addressed in `6e7d018` except as noted
Fixed: blocking transcription in `poll()` (now threaded, test added); `stop` priority; mute edge when `read()` returns None;
V9 subprocess test now covers `tts`, `stt`, `sounddevice`; missing-voice test no longer needs piper; clipping warning in `tts._render`;
turn derivation comment; running sample count; UNVERIFIED marks on sounddevice and whisper calls.
Not fixed: WAV fixtures for V7 (needs recordings), `small.en` (see above). The clipping assertion on real output is still untested.

## Outside my files
Nothing changed. `uv.lock` will need regenerating on a machine with network.

## Open questions
- Copy the voice file into `assets/voice/` and run the 3 skipped tests?
- Keep left/right wording, or switch to the spec's counter-clockwise wording after S6 checks a piece?
