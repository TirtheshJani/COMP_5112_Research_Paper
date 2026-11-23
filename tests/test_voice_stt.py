import numpy as np

from jigsaw.fakes import FakeAudioIn
from jigsaw.voice.stt import CommandListener

CH = 1600  # 0.1 s


def tone(n):
    t = np.arange(CH) / 16000
    return [(0.3 * np.sin(2 * np.pi * 300 * t)).astype(np.float32) for _ in range(n)]


def quiet(n):
    return [np.zeros(CH, np.float32) for _ in range(n)]


def run(chunks, said="where does this go", muted=lambda: False):
    heard = []

    def fake(pcm):
        heard.append(len(pcm))
        return said

    lst = CommandListener(FakeAudioIn(chunks), muted, transcribe=fake)
    out = [lst.poll() for _ in range(len(chunks) + 1)]
    return [o for o in out if o], heard


def test_command_recognised_after_silence():
    out, heard = run(quiet(2) + tone(8) + quiet(5))
    assert out == ["ask"]
    assert len(heard) == 1


def test_pure_silence_gives_none():
    out, heard = run(quiet(30))
    assert out == [] and heard == []


def test_short_blip_ignored():
    out, heard = run(tone(2) + quiet(6))
    assert out == [] and heard == []


def test_unknown_text_gives_none():
    out, heard = run(tone(8) + quiet(5), said="banana")
    assert out == [] and len(heard) == 1


def test_muted_input_ignored_and_holdoff():
    muted = {"v": True}
    chunks = tone(8) + quiet(1) + tone(8) + quiet(5)
    heard = []
    lst = CommandListener(FakeAudioIn(chunks), lambda: muted["v"], transcribe=lambda p: heard.append(1) or "stop")
    for _ in range(8):
        assert lst.poll() is None
    muted["v"] = False
    out = [lst.poll() for _ in range(len(chunks) - 8)]
    # 0.5 s hold-off drops quiet(1) and the first 4 tone chunks; the last 4 tone chunks (0.4 s) are heard
    assert [o for o in out if o] == ["stop"]
    assert len(heard) == 1


def test_long_speech_is_cut_at_max():
    # 4.5 s of speech: first 4.0 s are cut and transcribed, the remaining 0.5 s is a second utterance
    out, heard = run(tone(45) + quiet(5))
    assert out == ["ask", "ask"]
    assert heard[0] <= 4.0 * 16000 + CH
