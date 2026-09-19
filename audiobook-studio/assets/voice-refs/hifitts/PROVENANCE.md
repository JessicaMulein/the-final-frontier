# Narrator voice reference — provenance and integrity

`hifitts-clean-92.wav` is the voice of this audiobook. Every rendered chapter is a
zero-shot clone of this file, and the chapters approved by ear were approved against
**this exact audio**. It is committed rather than regenerated because re-deriving it
depends on a third-party dataset mirror and on a local cache path, and because losing
it would mean the book's narrator could never be reproduced or the remaining chapters
rendered to match the approved ones.

## Integrity

```
hifitts-clean-92.wav  sha256 2718268846e7b02b15b130c499711ae4730f8041307f49d39e1e08678a8ec762
hifitts-clean-92.txt  sha256 9fb56fcb1bd465b15398174da692c8b18fc468bcac9764a09b21580f6245d4aa
```

44,100 Hz, mono, PCM_16, 32.44 s. The rate matters: it is Fish S2 Pro's native rate,
so the identity source is never resampled.

The transcript is the dataset's own verified, zero-WER text for these clips, and it is
what gets passed as `ref_text`. A mismatched reference transcript was a real defect in
the earlier QVoice pipeline, so the pairing is kept together and hashed together.

**Do not regenerate this file to "refresh" it.** A different selection is a different
narrator, and every approval recorded against the current voice would silently become
meaningless.

## Where it came from

| | |
|---|---|
| dataset | Hi-Fi Multi-Speaker English TTS (Hi-Fi TTS), OpenSLR SLR109 |
| paper | Bakhturina, Lavrukhin, Ginsburg, Zhang — *Hi-Fi Multi-Speaker English TTS Dataset*, arXiv:2104.01497 |
| mirror used | Hugging Face `MikhailT/hifi-tts`, `dev.clean` parquet shards |
| speaker | 92 |
| subset | `clean` (the dataset's higher-quality tier, SNR >= 40 dB) |
| built by | `audiobook-studio/tools/narration/hifitts_refs.py --seconds 25` |
| selection | clips ordered by closeness to 8 s duration, concatenated until >= 25 s, peak-normalised to 0.95 |

The underlying material is public domain: the dataset is built from LibriVox
audiobooks and Project Gutenberg texts. The `clean` subset was chosen deliberately —
its label predicted the listener's blind preference where prosody metrics did not.

## Speaker consent — unresolved, and the author's call

The dataset's authors state that they obtained **written consent from the speakers**
before using their voices for synthesis, and they encourage others doing the same to
seek consent as well.

Speaker 92 is a real LibriVox volunteer. This novel is distributed under
"All rights reserved". Whether narrating a commercial work with this voice needs that
speaker's consent is an ethical question the dataset's own authors raise, and it is the
author's decision, not a technical one. It is recorded here so the question is not lost
simply because the file is convenient.

If the answer turns out to be no, the voice must change, and every chapter has to be
re-rendered. That is the cost of deferring it.

## Why this file is not subject to blob-size purging

At 2.7 MB it exceeds the 2 MB threshold used when the repository's history was rewritten
to remove old renders. It must be excluded from any future size-based purge. A rewrite
that strips it would remove the book's narrator from the repository while leaving every
tool that reads it intact — a failure that would not surface until the next render.
