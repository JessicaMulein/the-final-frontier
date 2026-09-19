# Assets

Inputs and provenance for the narration pipeline. Nothing here is a deliverable.

The repo's top-level `audiobook/` directory is reserved for final output only — the
chapter WAVs, the MP3s derived from them, and the M4B. Anything that is an input, a
measurement, or a superseded render lives under `.audiobook/`.

## voice-refs/

Reference recordings a cloner conditions on. Small, and kept because the reference
is the ceiling on delivery quality for every engine.

| Path | What |
|---|---|
| `common-voice-refs/*.wav` | Four UK southern female clips from [OpenSLR SLR83](https://openslr.org/83), the crowdsourced UK/Ireland dialect corpus. CC BY-SA 4.0. |
| `emns-refs/*.wav` | EMNS candidates, [OpenSLR SLR136](https://openslr.org/136). Apache 2.0. |
| `emns-refs/emns-refs.json` | Provenance and the attribution the EMNS licence requires. Keep this wherever a derived voice ships. |

Measured properties, from `provenance/qvoice-legacy/qvoice/dialect-reference-analysis.json`:

| Reference | Pitch span | Dynamic range | Verdict |
|---|---|---|---|
| `uk-southern-female-03-tight` | 8.84 st | 22.6 dB | clean, but the narrowest range of any candidate |
| `emns-neutral-l0-599` | 19.24 st | 27.3 dB | widest range, rejected by ear as "hiss and something else" |

That pair is the whole reason the reference search happened: neither axis alone was
enough, and optimising one at a time produced a voice that was either flat or noisy.
The production reference now comes from Hi-Fi TTS instead, built by
`tools/narration/hifitts_refs.py` into `tools/narration/out/hifitts-refs/`.

The licence distinction matters and is easy to lose: a permissive copyright licence
on a recording is **not** the speaker's consent to have their voice cloned. The
Hi-Fi TTS authors sought written consent from speakers before using a voice for
synthesis and encourage others to do the same.

## provenance/qvoice-legacy/

The Qwen3 CustomVoice ("QVoice") work, superseded as an engine but retained for the
measurements that are still cited in the spec and in code comments.

Worth keeping:

- `qvoice/dialect-reference-analysis.json` — source of the pitch-span figures above
- `qvoice/production-recipe.json` — the locked QVoice recipe, including the human
  approval note "Excellent overall; slightly less emotive than ideal", which is the
  observation that started the engine search
- `qvoice/frontier-british-female-reference.json` — EMNS clip selection and transcripts
- `qvoice/*.qvoice` — the built voice profiles

A latent bug is recorded in those logs and worth remembering: the QVoice pipeline
conditioned the uk-s03 audio with EMNS's transcript as its ICL text. A reference and
its transcript must match; the current pipeline pairs every reference with its own.

## Superseded output

`.audiobook/superseded/` holds the previous complete audiobook — the Chatterbox EMNS
M4B and the 128 MP3s derived from it. Parked rather than deleted so there is a
listenable product until the new render replaces it. Safe to remove once the new M4B
is built and accepted.
