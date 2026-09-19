# Narration engine subproject

Spec: `.kiro/specs/narration-engine/`

Goal: one command produces a verified audiobook, with human listening spent on a
short voice audition and a bounded listen list rather than on reviewing 130 chapters
by ear.

## Why this exists separately

The QVoice pipeline in `../kokoro-local/` produces good chapters but needs a human to
find defects by timestamp and a maintainer to reroll units by hand. Chapters 1-3 cost
a full session that way. It also carries an expressiveness ceiling its own recipe
records: "slightly less emotive than ideal, but do not change the recipe."

That path stays working and untouched. It is the control in the audition, not the
thing being replaced on faith.

## Environment

Isolated on purpose. `mlx-audio` is pinned as a git submodule and installed editable
here, so model-level work is contributable upstream; the QVoice venv keeps its own
pinned wheel and is unaffected.

```bash
cd .audiobook/tools/narration
PY=.venv/bin/python           # do not Path.resolve() this; it strips the venv
$PY -c "import mlx_audio, os; print(os.path.dirname(mlx_audio.__file__))"
# -> .audiobook/tools/vendor/mlx-audio/mlx_audio
```

Rebuild:

```bash
uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install -e "../vendor/mlx-audio[tts]"
VIRTUAL_ENV=.venv uv pip install soundfile mlx-whisper
```

Submodule pinned at `6dc2103`. It tracks upstream read-only; a push remote gets added
only when a pull request is ready.

## Hardware

Apple M4 Max, 64 GB unified memory, 16 cores, MLX 0.32.2. Memory is ample for an
8-bit 4B model plus codec and caches. Throughput is the open question, which is why
the candidate budget is measured before anything is built on top of it.

## Engine findings

Verified by reading the installed source, not from model cards.

**Fish S2 Pro (`fish_qwen3_omni`) — audition first.** Already has what the QVoice
path lacks:

```python
generate(text, ref_audio=..., ref_text=..., instruct=..., speed=..., chunk_length=300)
batch_generate(texts, ref_audios, ref_texts, instructs, ...)
```

`generate` accumulates a `Conversation`, appending each rendered segment back as an
assistant `VQPart` before the next. Long-form continuity is native. Our
warm-up-generate-then-trim-by-ASR machinery exists only to approximate that, and it
produced two of this session's bugs: a residue stutter at a seam, and a boundary
misalignment that deleted "Two point one" and "Ravi" while chapter WER stayed at
0.023.

`batch_generate` matters more than raw speed here, because the whole approach depends
on affording several candidates per unit.

**IndexTTS in mlx-audio is v1, not v2.** Confirmed at submodule HEAD: a single
`ref_audio`, BigVGAN vocoder, no emotion or style conditioning. IndexTTS2's separable
timbre and emotion prompts — the cleanest answer to flat affect, since it would let
the narrator's identity and her performance come from different references — are
absent. That is the porting contribution, and it is a genuine one.

## What the gates must catch

Text-based QA is structurally blind to the defects that actually reach a listener,
because Whisper is a language model and reconstructs damaged speech into correct
text. Confirmed this session, each passing every gate in place at the time:

| Defect | Why it passed |
|---|---|
| Intra-word stutter on "six fifty-four" | ASR normalizes it to one correct token; two rerolls were accepted by machine and rejected by ear |
| Deleted "Two point one", "Ravi" | Boundary search took the next exact word; chapter WER 0.023 |
| Cold-start burst on the first words | Scored 0 clicks; it is not a click |
| Warm-up residue stutter at a seam | Residue sat below every threshold then in place |
| Within-unit level fade of 3-6.5 dB | Per-unit gain matching cannot see a slope inside a unit |

Each becomes a retained regression fixture before any new gate is trusted.

Two negative results worth keeping, so they are not rediscovered:

- A first-third-versus-last-third drift gate flagged 1 of 3 units the listener
  flagged, and rated the best-sounding unit worst of all. Thirds-medians average away
  the local degradation that is audible.
- Pace scoring preferred the take with the stuttered "four", because its overall
  rhythm was closest to the chapter norm. Selecting on aggregate rhythm cannot
  detect a defect lasting 200 ms.

The most promising untried signal is cross-candidate consensus: align siblings for the
same text and flag the word that is an outlier against its own siblings. It needs
calibration against the fixtures above before it gates anything.
