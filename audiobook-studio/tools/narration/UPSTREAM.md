# Upstream findings for `Blaizzy/mlx-audio`

Found while building an audiobook pipeline on Fish S2 Pro (`fish_qwen3_omni`).
Submodule pinned at `6dc2103`. Nothing here is filed yet — these are drafts.

Environment: Apple M4 Max, 64 GB, MLX 0.32.2, `mlx-community/fish-audio-s2-pro`.

---

## 1. `chunk_length` is silently ignored for plain prose (functional bug)

**Severity:** high for any long-form / audiobook use. Silent truncation, not an error.

`Model._split_generation_text`:

```python
def _split_generation_text(self, text: str, chunk_length: int) -> list[str]:
    turns = split_text_by_speaker(text)
    return (
        group_turns_into_batches(turns, max_speakers=5, max_bytes=chunk_length)
        if turns
        else [text]
    )
```

`split_text_by_speaker` splits on `r"(<\|speaker:\d+\|>)"` and returns only the
matched turns. Text containing no speaker tag therefore yields `turns == []`, the
`else` branch returns `[text]` unchanged, and the entire input becomes a single
batch. `chunk_length` has no effect, and generation stops at `max_tokens`.

### Reproduction

A 1186-word chapter (single speaker, no tags), `chunk_length=300`,
`max_tokens=1024`:

| | result |
|---|---|
| segments yielded | 1 |
| audio produced | 47.55 s |
| expected | ~7 min |
| coverage against source text | 0.131 |
| WER | 0.872 |

The call returns normally. Nothing warns that 87% of the text was dropped.

### Why it is easy to miss

The docstring for `generate` and the model README both describe long-form support:

> Long text is batched internally with `chunk_length` while preserving the running
> conversation context

That is true — but only when the text happens to contain speaker tags. The common
case for TTS, a single narrator, is the case that silently fails.

### Workaround in use

Tag each paragraph as one turn:

```python
tagged = "\n".join(f"<|speaker:0|>{p}" for p in paragraphs)
```

This engages the existing batcher and, importantly, keeps the running
`Conversation` across batches. Same chapter, same settings:

| | result |
|---|---|
| segments yielded | 23 |
| audio produced | 6 min 11 s |
| coverage | 0.998 |
| WER | 0.019 |

### Suggested fix

When no speaker turns are found, fall back to splitting on paragraph or sentence
boundaries up to `max_bytes`, rather than returning the whole text. Something like:

```python
turns = split_text_by_speaker(text)
if not turns:
    turns = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()] or [text]
return group_turns_into_batches(turns, max_speakers=5, max_bytes=chunk_length)
```

A warning when a single batch exceeds the token budget would also have turned this
from a silent 13%-coverage result into an obvious error.

---

## 2. README documents `ref_audio` as a path; the code requires an `mx.array`

**Severity:** low, but it is the first thing a new user hits.

`mlx_audio/tts/models/fish_qwen3_omni/README.md` shows:

```python
results = list(
    model.generate(
        text="Hello from Fish Speech.",
        ref_audio="sample_audio.wav",
        ref_text="This is what my voice sounds like.",
    )
)
```

`_prepare_reference_prompt` does:

```python
audio = ref_audio
...
if audio.ndim == 1:
```

so a `str` raises `AttributeError: 'str' object has no attribute 'ndim'`.

Either accept a path and load it (the `indextts` model does exactly this via
`load_audio`), or correct the README. Accepting a path would also let the model own
the resample: it runs at 44.1 kHz, and callers with 24 kHz references currently
have to resample themselves, where a naive `numpy.interp` would alias the one clip
that carries the speaker's identity.

---

## 3. `group_turns_into_batches` regroups sentence-level turns

**Severity:** documentation / expectation mismatch.

Tagging each *sentence* as its own turn does not yield one segment per sentence,
because turns are regrouped up to `max_speakers=5` and `max_bytes=chunk_length`:

- 13 sentences tagged individually → 4 yielded segments

That is reasonable behaviour for dialogue, but it means callers cannot use turn
tagging to control gap placement at sentence granularity. Worth a note in the
README, since the obvious reading is that one turn maps to one segment.

`max_speakers` is also a misleading parameter name here: it bounds the number of
*turns* per batch, not the number of distinct speakers.

---

## 4. Minor: deprecated call in our own code path

`mx.metal.device_info()` warns it is deprecated in favour of `mx.device_info()`.
Noted only because it appears in diagnostics we wrote, not in mlx-audio itself.

---

## Contribution plan

1. File issue 1 with the reproduction table above; offer the fallback-split patch.
2. File issue 2 as a docs-or-code choice, with a one-line preference for accepting
   a path.
3. Fold issue 3 into issue 1 as a README note.

Nothing in this file depends on the audiobook pipeline, so any patch can be kept
free of project-specific code, per the spec's requirement that upstream work stay
separable.
