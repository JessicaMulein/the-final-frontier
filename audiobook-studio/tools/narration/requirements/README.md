# Rebuilding the narration environment

The virtualenv is disposable and is not committed. `frozen.txt` is the exact
pinned set it contained, captured before it was deleted to reclaim disk space.

```bash
cd audiobook-studio/tools/narration
uv venv --python 3.12.11 .venv
uv pip install --python .venv/bin/python -r requirements/frozen.txt
```

## mlx-audio is not installed from PyPI

`mlx-audio` is deliberately absent from `frozen.txt`. It comes from the pinned
submodule at `audiobook-studio/tools/vendor/mlx-audio`, and every command must run with
it on the path:

```bash
export PYTHONPATH=<repo>/audiobook-studio/tools/vendor/mlx-audio
```

An editable install was tried and abandoned: the generated
`__editable__.mlx_audio-0.5.4.pth` is silently skipped by `site.py` in this
environment, so the finder never loads at interpreter startup even though a probe
`.pth` in the same directory does execute. `PYTHONPATH` is the reliable mechanism.
If the submodule is missing, `git submodule update --init --recursive` first.

## Model weights

Fish S2 Pro (`mlx-community/fish-audio-s2-pro`) downloads to the shared Hugging
Face cache on first use, outside this repository. Nothing here vendors weights.

## Voice reference

The chosen narrator reference lives in `out/hifitts-refs/` and is load-bearing
input, not test output: `render_chapter_fish.py` reads `hifitts-clean-92.wav` and
its verified transcript from there. Regenerate with `hifitts_refs.py` if lost.
