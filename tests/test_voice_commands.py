import pytest

from jigsaw.voice.commands import match_command


@pytest.mark.parametrize(
    "text,cmd",
    [
        ("where does this go", "ask"),
        ("Where does it go?", "ask"),
        ("where", "ask"),
        ("again", "again"),
        ("Repeat.", "again"),
        ("say that again", "again"),
        ("next", "next"),
        ("Next piece!", "next"),
        ("stop", "stop"),
        ("that's enough", "stop"),
        ("Thats enough", "stop"),
        ("  STOP,  ", "stop"),
        ("stop saying that again", "stop"),
    ],
)
def test_match(text, cmd):
    assert match_command(text) == cmd


@pytest.mark.parametrize("text", ["", "hello robot", "banana", "   ", "..."])
def test_no_match(text):
    assert match_command(text) is None


def test_voice_modules_import_without_extras():
    import subprocess
    import sys

    code = (
        "import sys, jigsaw.voice.phrases, jigsaw.voice.commands, jigsaw.voice.tts, jigsaw.voice.stt; "
        "assert not {'piper', 'faster_whisper', 'onnxruntime', 'sounddevice'} & set(sys.modules)"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
