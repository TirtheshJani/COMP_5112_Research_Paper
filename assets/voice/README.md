# Piper voice files

Not committed (see `.gitignore` here). Put these two files in this folder:

- `en_US-lessac-medium.onnx`
- `en_US-lessac-medium.onnx.json`

Source: the Piper voices on Hugging Face (`rhasspy/piper-voices`, `en/en_US/lessac/medium`). The same files already exist
in the `rocky_mini` repo root and can be copied. Sample rate is 22,050 Hz. To use another location set `JIGSAW_PIPER_VOICE`.

Install the engine with `uv sync --extra voice`. Without the voice file the Piper tests skip.
