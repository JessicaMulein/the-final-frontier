# Rebuilding the legacy audition environment

This pipeline is **frozen**. It drove the Kokoro/Chatterbox/QVoice auditions and the
first EMNS audiobook, and it is kept so those results stay reproducible and any part
of it can be restored. New work happens in `../narration` against Fish S2 Pro.

The virtualenv is disposable and is not committed. `frozen.txt` is the exact pinned
set it contained, captured before it was deleted to reclaim disk space.

```bash
cd audiobook-studio/tools/kokoro-local
uv venv --python 3.12.11 .venv
uv pip install --python .venv/bin/python -r requirements/frozen.txt
```

## Engines and weights

No weights are vendored here. The engines this pipeline drove pull their own models
into the shared Hugging Face cache on first use. The vendored C engine at
`../vendor/qwen3-tts-c` fetches its own weights with its own
`download_model.sh` / `download_voices.sh`; those downloads were removed from this
repository because the engine was superseded, and the scripts will fetch them again
if it is ever revived.
