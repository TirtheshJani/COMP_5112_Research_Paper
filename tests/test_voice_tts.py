import numpy as np
import pytest

from jigsaw.voice import tts

needs_voice = pytest.mark.skipif(not tts.voice_path().exists(), reason="Piper voice file absent (assets/voice/README.md)")


def test_all_sentences_count():
    s = tts.all_sentences()
    assert len(s) == 35 * 4 + 3
    assert len(set(s)) == len(s)


def test_missing_voice_is_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("JIGSAW_PIPER_VOICE", str(tmp_path / "none.onnx"))
    monkeypatch.setattr(tts, "_voice", None)
    with pytest.raises(FileNotFoundError):
        tts.synthesize("hello")


def test_synthesize_uses_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(tts, "_render", lambda t: (calls.append(t), (np.zeros(10, np.float32), 22050))[1])
    monkeypatch.setattr(tts, "_cache", {})
    tts.synthesize("a")
    tts.synthesize("a")
    assert calls == ["a"]


@needs_voice
def test_synthesize_real():
    pcm, rate = tts.synthesize("Row 7, column 5. Turn it a quarter turn to the right.")
    assert pcm.dtype == np.float32 and pcm.ndim == 1
    assert np.abs(pcm).max() <= 1.0
    assert 1.0 <= len(pcm) / rate <= 6.0


def test_warm_cache_renders_every_sentence_once(monkeypatch):
    calls = []
    monkeypatch.setattr(tts, "_render", lambda t: (calls.append(t), (np.zeros(10, np.float32), 22050))[1])
    monkeypatch.setattr(tts, "_cache", {})
    assert tts.warm_cache() == 143
    assert len(calls) == 143 and set(calls) == set(tts.all_sentences())
    assert tts.warm_cache() == 143
    assert len(calls) == 143                       # the second warm-up is served entirely from the cache


@needs_voice
def test_warm_cache_real_voice_serves_the_cached_object():
    assert tts.warm_cache() == 143
    first = tts.all_sentences()[0]
    assert tts.synthesize(first) is tts.synthesize(first)
