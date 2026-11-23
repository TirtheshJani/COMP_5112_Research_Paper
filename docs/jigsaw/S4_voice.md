# S4 Voice: fixed sentences out, four commands in

> **v2 update (23 Nov).** `Read` is already in front coordinates: `phrase_read(read)` takes no `cols` argument; say row and column plus one ("Row 4, column 2"). Add `phrase_reject(reason)` with short reason-specific lines: `no_grid` "Show me the grid side, over the green card"; `no_window` "Move your fingers to the edge"; anything else "Show me again". The turn sentence depends on how the person flips the piece; settle it with S6 on the real pieces (see S6 v2 box) before recording phrases.

| | |
|---|---|
| Terminal | Sonnet 5.5, effort high, Ultracode off |
| Branch and worktree | `feat/s4-voice` in `.worktrees/s4-voice` |
| Depends on | S0 merged |
| Blocks | S6 (app) |
| Owns | `jigsaw/voice/` (`__init__.py`, `phrases.py`, `tts.py`, `commands.py`, `stt.py`), `scripts/say.py`, `scripts/listen.py`, `tests/test_voice_*.py`, `assets/voice/` (ignored by git except a README) |
| Must not edit | core modules, `types.py`, `fakes.py`, `jigsaw/robot/` |
| Human needed | A listening test of ten commands (Task 5) |
| Skills | `karpathy-guidelines`, `test-driven-development`, `verification-before-completion`, `engineering:code-review` |

---

## Spec

### Problem

The robot must tell a person where a piece goes and how to turn it, and it should respond to a few spoken commands. The vocabulary is closed: forty positions, four turns, one rejection sentence, four commands. An earlier conversational app on this robot had trouble with turn-taking, and none of that machinery is needed here.

### Goals

1. A pure function that turns a `Read` into the sentence to speak, correct about the mirrored column and the direction of the turn.
2. Local speech synthesis of that sentence to PCM, with no network.
3. Recognition of four commands from 16 kHz microphone audio, with no language model.
4. Everything testable with `FakeAudioIn` and `FakeAudioOut`, and the demo able to run with voice input switched off.

### Non-goals

- No conversation, no wake word, no personality.
- No barge-in. The microphone is ignored while the robot speaks.
- No cloud speech services.
- No audio playback code. Playing PCM is `AudioOut.play`, owned by S3. This workstream produces arrays.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| V1 | P0 | `phrase_read(read, cols)` | `Read(0, 0, 2)` with 8 columns gives "Row 1, column 8. Turn it upside down." Table of all four turn sentences tested |
| V2 | P0 | `phrase_reject()` | Returns "I cannot read that one. Show me again." |
| V3 | P0 | Turn wording matches what the person must do to the piece as they look at the picture side | See design notes; one test per turn, and one physical confirmation in S6 |
| V4 | P0 | `synthesize(text)` returns mono float32 in [-1, 1] and the sample rate, using Piper with a voice file under `assets/voice/` | Duration between 1 and 6 seconds for the longest sentence; no clipping; runs offline. Skipped in CI when the voice file is absent |
| V5 | P0 | All 161 sentences (40 positions x 4 turns, plus the rejection) are synthesized once and cached in memory at start | `warm_cache()` finishes in under 60 seconds on the laptop; later calls return in under 5 ms |
| V6 | P0 | `match_command(text)` | "where does this go", "where does it go", "where" give `ask`; "again", "repeat", "say that again" give `again`; "next", "next piece" give `next`; "stop", "that's enough" give `stop`; anything else gives `None`. Case and punctuation ignored |
| V7 | P1 | `CommandListener.poll()`: voice activity detection on 16 kHz chunks, transcribe each utterance of 0.3 to 4 seconds with faster-whisper, pass the text to `match_command`; ignores input while `is_muted()` is true and for 0.5 seconds after | With `FakeAudioIn` fed recorded WAV files of the four commands, each is recognised; silence gives `None` |
| V8 | P1 | Recognition restricted to the command vocabulary | Use an `initial_prompt` listing the commands and reject transcripts with no keyword; ten spoken commands in a quiet room, at least nine correct |
| V9 | P0 | No import of `piper`, `faster_whisper` or `onnxruntime` at module import time | `python -c "import jigsaw.voice.phrases, jigsaw.voice.commands"` works with the `voice` extra not installed |

### Design notes

- The turn sentence. `read.turn = k` means the camera sees the back rotated by `k` quarter turns counter-clockwise. To make the back upright the person rotates it `k` quarter turns clockwise as seen from the back. Seen from the front, the same physical rotation is counter-clockwise. The person assembling the puzzle looks at the front. So the sentences, phrased for the picture side, are: 0 "It is the right way up.", 1 "Turn it a quarter turn counter-clockwise.", 2 "Turn it upside down.", 3 "Turn it a quarter turn clockwise." Write the derivation as a comment above the table, and keep the table in one place. S6 confirms it with one real piece before the talk. If S0 or S1 recorded a different convention in their handoff notes, follow the notes and say so.
- Libraries. `rocky_mini` already runs Piper (`en_US-lessac-medium.onnx`, 22,050 Hz) and faster-whisper on this laptop, and vendors the Silero VAD ONNX model to avoid a PyTorch dependency. Reuse those choices and read that code first. Do not copy its architecture; this needs two functions and one small class.
- Sample rates. `synthesize` returns Piper's native rate. `AudioOut.play` (S3) resamples.
- The fallback. If the Piper install fails on this machine, pre-render the 161 sentences to WAV files once on any machine and load them. The interface does not change.

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Which Piper voice | Default: the one already in `rocky_mini` | No |
| Is voice input wanted in the talk at all | Author. Default: built, off by default | No |

---

## Plan

### Task 1: Worktree and reading

- [ ] Create the worktree. Dispatch the Explore subagent below. Read `HANDOFF_S0.md` for the turn convention.

### Task 2: Phrases and commands (V1, V2, V3, V6, V9). No dependencies needed

- [ ] `tests/test_voice_phrases.py`:

```python
import pytest
from jigsaw.types import Read
from jigsaw.voice.phrases import phrase_read, phrase_reject, match_command

@pytest.mark.parametrize("turn,tail", [
    (0, "It is the right way up."),
    (1, "Turn it a quarter turn counter-clockwise."),
    (2, "Turn it upside down."),
    (3, "Turn it a quarter turn clockwise."),
])
def test_turn_sentences(turn, tail):
    assert phrase_read(Read(2, 3, turn), cols=8) == f"Row 3, column 5. {tail}"

def test_column_is_mirrored():
    assert phrase_read(Read(0, 0, 0), cols=8).startswith("Row 1, column 8.")
    assert phrase_read(Read(4, 7, 0), cols=8).startswith("Row 5, column 1.")

def test_reject_sentence():
    assert phrase_reject() == "I cannot read that one. Show me again."

@pytest.mark.parametrize("text,cmd", [
    ("Where does this go?", "ask"), ("where does it go", "ask"), ("WHERE", "ask"),
    ("again", "again"), ("Say that again.", "again"), ("repeat", "again"),
    ("next", "next"), ("Next piece!", "next"),
    ("stop", "stop"), ("that's enough", "stop"),
    ("", None), ("hello robot", None), ("the weather is nice", None),
])
def test_match_command(text, cmd):
    assert match_command(text) == cmd
```

- [ ] Run (fail). Implement `phrases.py` using `decode.front_slot`. `match_command` lowercases, strips punctuation and checks keyword sets in the order stop, again, next, ask (so "stop, where" stops). Run (pass). Commit.

### Task 3: Synthesis (V4, V5)

- [ ] Add `piper-tts` to the `voice` optional group with the version `rocky_mini` uses. Put the voice file in `assets/voice/` (copy from `rocky_mini`; it is ignored by git) and document in `assets/voice/README.md` where it comes from.
- [ ] Tests, marked to skip when the voice file is missing: output dtype and range, duration bounds, `warm_cache` timing, second call under 5 ms.
- [ ] Implement `tts.py`: lazy model load, `synthesize`, `warm_cache(cols)`. About 40 lines.
- [ ] `scripts/say.py "Row 1, column 8. Turn it upside down."` plays through the laptop speakers with `sounddevice` (added to the `voice` group) so the author can hear it without the robot. Run it once and listen. Commit.

### Task 4: Listening (V7, V8)

- [ ] Record four short WAV files of the commands at 16 kHz with `scripts/listen.py --record` (the author speaks, or use `synthesize` output resampled to 16 kHz as test input; note which). Store them under `tests/data/voice/`.
- [ ] Tests with `FakeAudioIn` fed those files in 20 ms chunks: each returns its command; silence returns `None`; while muted nothing is returned.
- [ ] Implement `stt.py`: `CommandListener` keeps a small buffer, uses the vendored Silero VAD through `onnxruntime` to find utterance boundaries, and calls faster-whisper (`small.en`, on the GPU if present) with an `initial_prompt` of the command phrases. `poll()` never blocks longer than one chunk; transcription runs in a worker thread and its result is picked up by a later `poll()`.
- [ ] Commit.

### Task 5: Listening test. HUMAN

- [ ] `scripts/listen.py` prints each recognised command live from the laptop microphone. The author says each command at least twice plus two unrelated sentences. Record hits and false triggers in the handoff note.

### Task 6: Review and handoff

- [ ] Review subagent; `HANDOFF_S4.md`; pull request.

### Subagent use

- Explore subagent, at the start: "In `C:\Users\TJ\Documents\GitHub\rocky_mini`, find how Piper is loaded and called, how faster-whisper is configured, and how the Silero VAD ONNX model is run with onnxruntime (file `audio/vad.py` or similar, and `server/`). Return the exact package versions from its lock or pyproject file, the model file names, and the 10 to 30 lines of code for each call. Do not edit anything."
- Tasks 3 and 4 touch different files and can run as two parallel general-purpose subagents after Task 2 is committed. Prompt for each: the requirement numbers, the files it may create, the instruction to write tests first, to keep imports lazy, and to return the test output.
- Review subagent: "Review `feat/s4-voice`. Check the turn-sentence derivation in the comment against `docs/jigsaw/CLAUDE.md` conventions; check for any import of piper, faster_whisper or onnxruntime at module top level; check that `CommandListener.poll` cannot block. Do not edit files."

### What could go wrong

| If | Then |
|---|---|
| Piper will not install on Python 3.12 on Windows | Pre-render the 161 WAV files (see design notes) |
| Whisper mishears single words | Prefer the longer phrasings in the demo ("where does this go"), and keep the keyword match on the transcript loose |
| The robot's own speech triggers a command | The mute flag and the 0.5 second tail handle it; S6 passes `AudioOut.is_playing` as `is_muted` |
| The turn wording is backwards on the real robot | It is one table. S6 Task 6 checks it with a real piece and fixes the table here through a one-line pull request |

### Definition of done

Phrase and command tests pass with no optional dependencies; synthesis heard once by the author; listening test recorded; handoff written; pull request open.
