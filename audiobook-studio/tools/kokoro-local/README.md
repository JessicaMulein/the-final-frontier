# Local Chatterbox / Kokoro audition tooling

Mac (Apple Silicon) draft/audition pipeline for *The Final Frontier*.  
**This is not the Nova production workflow.** Paid production remains
`frontier-audiobook production …` under [`audiobook-studio/README.md`](../../README.md).

These scripts never call AWS/Nova and never write under `audiobook-studio/dist/`.

## Layout

| Script | Role |
|--------|------|
| `render_chapter_chatterbox.py` | One chapter → WAV (Chatterbox via mlx-audio) |
| `batch_render_chatterbox.py` | Range of chapters; optional STT-recheck + retry |
| `validate_stt.py` | mlx-whisper vs manuscript; WER / insert / suspicious-replace gate |
| `prepare_ref.py` | Tight-crop + fade a voice reference WAV |
| `emns_select_refs.py` | Survey / profile the EMNS corpus; build reference WAVs |
| `audition_refs.py` | A/B refs × knob presets over one passage; WER + prosody table |
| `prosody.py` | Pitch-span / dynamic-range metrics (numpy only, no TTS import) |
| `detect_loops.py` | Loop / babble / dropped-content gate — catches what WER misses |
| `soften_joins.py` | Post-pass join click cleanup on existing WAVs |
| `build_m4b.py` | Chaptered M4B from ordered `*-{voice-tag}.wav`; listen gate + text version |
| `spoken_text.py` | The one definition of narrated text, and its digest |
| `audio_state.py` | Per-chapter state, listen queue, approval ledger |
| `render_chapter.py` | Kokoro one-shot (earlier audition; not the locked path) |

Use the **local** venv (not `audiobook-studio/.venv`):

```bash
cd audiobook-studio/tools/kokoro-local
# .venv must already exist with mlx-audio, mlx-whisper, soundfile, …
PY=.venv/bin/python   # do not Path.resolve() this; keep the venv shim
```

Outputs go under `audiobook/` (delivery-shaped filenames) and logs/reports under
`audiobook/kokoro-audition/chatterbox-v2/`.

## Locked voice (current)

- **Model:** `mlx-community/chatterbox-fp16`
- **Ref:** `audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav`  
  (from `ylacombe/english_dialects` southern_female clip 03, tight-cropped)
- **Voice tag:** `chatterbox-uk-s03`
- **Delivery names:** `NNN-chapter-XXX-chatterbox-uk-s03.wav`  
  (sequence = `4 + chapter`, matching Nova-ish ordering; dedication = `002-…`)

## Candidate replacement seed (EMNS)

Measured alternative to the `uk-southern-female-03` seed. **Not yet locked —
awaiting a listen pass.**

- **Ref:** `audiobook/kokoro-audition/emns-refs/emns-neutral-l0-599.wav`
- **Corpus:** [EMNS, OpenSLR SLR136](https://openslr.org/136/) — single female
  British English speaker, emotive narrative storytelling, **Apache 2.0**
- **Attribution:** Kari Noriy, Xiaosong Yang, Jian Zhang, *EMNS /Imz/ Corpus*
  (2023). Required by the licence; carried in `emns-refs.json`.
- **Source:** utterance id 599, class `Neutral`, level 0, single continuous take
- **Pairs with `0.5 / 0.5`.** See the warning below.

Measured on 30 sentences / 390 tokens of chapter 1:

| Ref | knobs | WER | susp | pitch span | dyn dB |
|-----|-------|-----|------|-----------|--------|
| `emns-neutral-l0-599` | **0.5/0.5** | **0.0256** | **3** | **17.58** | 25.4 |
| `emns-neutral-l0-599` | 0.7/0.3 | 0.2179 | 5 | 17.54 | 25.4 |
| `uk-southern-female-03-tight` | 0.5/0.5 | 0.0538 | 7 | 15.76 | 24.7 |
| `uk-southern-female-03-tight` | 0.7/0.3 | 0.0692 | 8 | 16.05 | 26.1 |

Against the current locked recipe (bottom row): **2.7x lower WER, ~60% fewer
suspicious replaces, ~10% wider pitch span.** This is README lever #1
("expressive seed, mid knobs") holding up under measurement.

### Full chapter 1 result

The 30-sentence audition **understates full-chapter WER by ~3.7x** (0.0256 on the
excerpt vs 0.094 over the whole chapter). Audition numbers rank candidates; they
do not predict chapter quality. Measured on the full chapter:

| | EMNS n599 `0.5/0.5` | s03 `0.7/0.3` |
|---|---|---|
| STT gate | PASS | **FAIL** |
| loop gate | PASS | PASS |
| WER | 0.094 | 0.114 |
| replace ops | **20** | 57 |
| suspicious | **14** | 34 |
| runtime | 8.5 min | 6.3 min |

Two caveats: `Anand` still garbles on both seeds (`-> and nun` / `-> and anne`),
so that one is a hard word, not a seed problem. And the **first** render attempt
of this exact recipe hit a 30 s babble collapse — it took one re-render to get a
clean pass, so always run `detect_loops.py` before accepting a chapter. The
broken attempt is kept at
`audiobook/kokoro-audition/ref-audition-long/attempt1-broken/` as a gate fixture.

> **Do not swap the ref without also dropping the knobs.** `emns-neutral-l0-599`
> at `0.7/0.3` degrades to WER `0.2179` — roughly 3x *worse* than the seed it
> replaces. The gain is the seed-and-knobs pair, not the seed alone.

### Traps found while selecting this

1. **Emotion labels are a bad proxy for expressiveness.** EMNS `level` is bound
   to emotion class, not an independent intensity dial. Low-arousal classes
   *flatten* prosody: `Sad` has the corpus's **lowest** mean pitch span (6.54)
   and sits below the incumbent (8.84), while `Neutral` level 0 contains some of
   the widest-range clips in the corpus. Select on measured prosody
   (`--profile`), never on the label.
2. **The WebM containers over-report duration.** These are browser-recorded, so
   `ffprobe -show_entries format=duration` is inflated — id 241 advertises
   15.28 s and decodes to 8.87 s. Corpus is 1.91 h, not the 2.3 h implied.
   `emns_select_refs.py` measures decoded sample counts instead.
3. **Splicing underperformed single takes.** Spliced pairs reached 12+ s of
   speech but scored *worse* on both WER and pitch span than the 8 s single
   clip, and behaved erratically across presets. Prefer one continuous take.
4. **Short audition passages mislead.** A 2-sentence probe put the incumbent's
   pitch span at 4.25; 8 sentences put it at 14.80. Use >= 30 sentences before
   drawing any conclusion.

### Rebuilding the refs

The corpus is cached outside the repo (repo `.gitignore` is empty, so anything
in-tree gets committed). Only the short ref WAVs are versioned.

```bash
mkdir -p ~/.cache/emns-slr136 && cd ~/.cache/emns-slr136
curl -sSLO https://openslr.org/resources/136/metadata.csv
curl -sSLO https://openslr.org/resources/136/cleaned_webm.tar.xz
tar -xJf cleaned_webm.tar.xz
```

```bash
# survey, then rank empirically against the incumbent
$PY emns_select_refs.py --report --profile \
  --corpus ~/.cache/emns-slr136 \
  --baseline "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav" \
  --min-speech 6.0 --top 25

# rebuild the current candidate
$PY emns_select_refs.py --build \
  --corpus ~/.cache/emns-slr136 --id 599 \
  --out-dir "../../../audiobook/kokoro-audition/emns-refs"
```

`--splice-group 599,524` joins clips into one ref if you want to test length
again; `--keep-internal-silence` disables dead-air compaction.

## Ref audition harness

Renders one passage per (ref × knob preset), then scores fidelity **and**
prosody. The prosody columns exist because WER cannot see the defect being
chased: a flat, evenly-paced read scores *well* on WER.

```bash
$PY audition_refs.py \
  --ref-dir "../../../audiobook/kokoro-audition/emns-refs" \
  --ref "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav" \
  --chapter-file "../../../The Final Frontier Novel/chapters/discovery-part/discovery-part-001-noise-floor.md" \
  --max-sentences 30 \
  --preset 0.7:0.3 --preset 0.5:0.5 \
  --out-dir "../../../audiobook/kokoro-audition/ref-audition-long"
```

Read the two halves together: prefer the candidate that holds WER at or below
the incumbent **while** raising pitch span. Neither number is an acceptance
decision — editorial voice acceptance is human.

## Current render recipe

Defaults used for the ongoing book pass:

| Knob | Value | Notes |
|------|-------|--------|
| `exaggeration` | `0.7` | Affect up — also raises word-garble risk |
| `cfg_weight` | `0.3` | Lower = freer delivery |
| `chunk-mode` | `sentences` | Variable pauses; **cold-start every sentence** |
| breath gate | on | Trim trailing fwip/breath before joins |

```bash
$PY batch_render_chatterbox.py \
  --start 1 --end 30 \
  --manuscript-root "../../../The Final Frontier Novel/chapters" \
  --ref-audio "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav" \
  --output-dir "../../../audiobook" \
  --exaggeration 0.7 \
  --cfg-weight 0.3 \
  --chunk-mode sentences \
  --gate-breaths \
  --voice-tag chatterbox-uk-s03 \
  --skip-existing
```

Single chapter:

```bash
$PY render_chapter_chatterbox.py \
  --chapter-file "../../../The Final Frontier Novel/chapters/…/discovery-part-002-….md" \
  --output "../../../audiobook/006-chapter-002-chatterbox-uk-s03.wav" \
  --ref-audio "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav" \
  --exaggeration 0.7 --cfg-weight 0.3 --chunk-mode sentences --gate-breaths
```

### Emotion vs fidelity (known tradeoff)

Dry dialect seed + hot knobs + sentence cold-starts → clearer *affect*, more
near-rhyme garble (`shower`→`dowered`, `Anand`→`and anne`). Blind whole-chapter
re-render at the same recipe usually regenerates the same class of errors.

Promising levers that **keep emotion** without only “turning knobs down”:

1. **Expressive seed, mid knobs** — performative British female ref; generate ~`0.5 / 0.5`.
2. **Hot knobs + paragraph (or multi-sentence) chunks** — fewer cold starts on short openers.
3. **Surgical retry** — re-synth only STT-flagged sentences (cooler or with pronunciation hints).

Do not treat STT FAIL as “delete chapter and hope” without changing one of the above.

## Loop / babble gate (`detect_loops.py`)

**The STT gate alone will pass a chapter with 30 seconds of garbage in it.**
Run this alongside it.

When Chatterbox collapses into degenerate repetition, whisper transcribes the
run as many tiny or empty segments. No single insert span gets long, WER barely
moves, and `validate_stt.py` returns PASS. Observed on the first chapter 1
render at `0.5/0.5`: a 30 s stretch that collapsed to the two words "No fit.",
plus a stretch of garbled numerals that drifted into Korean characters — and the
STT gate scored it `wer=0.066 PASS`, *better* than the clean re-render's
`wer=0.094`. WER is close to useless for this failure mode.

```bash
$PY detect_loops.py \
  "../../../audiobook/005-chapter-001-chatterbox-emns-n599.wav" \
  --manuscript-root "../../../The Final Frontier Novel" \
  --report "../../../audiobook/kokoro-audition/ref-audition-long/loop-report-ch01.json"
```

Exits non-zero on any finding. Signals:

| Finding | Meaning |
|---------|---------|
| `stall` | A span >= 4 s running below 30% of this render's own median pace |
| `repeat` | The same short segment text recurring >= 4 times back to back |
| `missing` | Word coverage below 0.97 — content simply not delivered |

Two calibration notes learned the hard way:

- **Pace is relative, not absolute.** Stalls are judged against the render's own
  median words/sec. The EMNS seed narrates at ~2.45 wps where
  `uk-southern-female-03` runs ~3.3 wps; an absolute threshold flags a slow
  voice as a broken one. That tempo difference is also why the same chapter is
  8.5 min on the new seed and 6.3 min on the old one.
- **Whisper hallucinates past end-of-file.** It emitted 17 phantom segments past
  EOF on the s03 chapter, and a fake "24x 'to me'" loop on a clean render.
  Segments starting beyond the audio length are dropped before judging.

Whisper is also non-deterministic run to run (the same file counted 1153 then
1221 words). Treat any single STT number as noisy; the stall/repeat findings are
far more stable than WER.

## STT glitch gate

`validate_stt.py` transcribes with `mlx-community/whisper-large-v3-turbo` and
compares tokens to spoken manuscript text.

Fails when any of:

- WER ≥ `--wer-fail` (default `0.12`)
- insert ops ≥ `--insert-fail` (default `12`) — loop / babble signal
- suspicious content-word replaces ≥ `--suspicious-fail` (default `15`)

Benign filters cover numbers/ordinals, UK/US spelling, weak function-word flips.
Whisper noise still remains; use examples as a **listen list**, not gospel.

```bash
$PY validate_stt.py \
  --audio-dir "../../../audiobook" \
  --manuscript-root "../../../The Final Frontier Novel" \
  --voice-tag chatterbox-uk-s03 \
  --chapter 1 --chapter 2 \
  --report "../../../audiobook/kokoro-audition/chatterbox-v2/stt-glitch-report.json"
```

### Batch with STT-recheck

After each chapter: STT → on FAIL, one full re-render (`--stt-retries`, default 1)
→ if still FAIL, **keep last render** and continue (logged).

```bash
$PY batch_render_chatterbox.py \
  --start 8 --end 30 \
  …same render flags… \
  --stt-recheck \
  --stt-retries 1 \
  --stt-suspicious-fail 15 \
  --stt-report "../../../audiobook/kokoro-audition/chatterbox-v2/stt-batch-008-030.jsonl"
```

Requires Metal (run outside sandbox / normal Terminal). Do not
`Path.resolve()` the `.venv/bin/python` shim — that strips the venv and breaks imports.

## Reference prep

```bash
$PY prepare_ref.py \
  --input "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03.wav" \
  --output "../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav"
```

## Listen queue and text versioning

Three artifacts have to agree about which draft they came from: the render, the
human listen approval, and the packaged M4B. `spoken_text.py` defines the one
identity they all derive from — the SHA-256 of `normalize(extract_body(chapter))`,
the exact string handed to the model. `render_chapter_chatterbox` and
`render_chapter_qvoice` import `extract_body` from it, so a digest can never
drift from the text that was actually narrated.

The digest covers **spoken text only**. Editing a `hook:` line, fixing a `words:`
count, or promoting a `status:` leaves the audio valid. Changing a sentence does
not.

### States

| State | Meaning |
|-------|---------|
| `missing` | no render on disk |
| `stale` | a render exists, but of superseded prose |
| `failed` | rendered, automated gates did not pass |
| `unlistened` | rendered, gates passed, **awaiting a human listen** |
| `rejected` | a human listened to this exact text and rejected it |
| `accepted` | a human listened to this exact text and accepted it |

Only `accepted` chapters may be packaged. Approval is bound to the digest, not to
the chapter number, so **nothing ever has to remember to un-approve**: edit the
prose and the old approval stops matching, and the chapter reappears in the
queue. Revert the edit and the approval applies again.

`audio_state.py` runs on plain `python3` — no mlx, no Metal, no venv — so it
works from a hook, from CI, or while a render owns the GPU.

```bash
ROOTS=(--chapters-root "../../../The Final Frontier Novel/chapters"
       --output-dir "../../../audiobook"
       --work-root "../../../audiobook/qvoice-work")

python3 audio_state.py "${ROOTS[@]}" --report    # table, worst first
python3 audio_state.py "${ROOTS[@]}" --stale     # needs re-rendering
python3 audio_state.py "${ROOTS[@]}" --queue     # needs listening
python3 audio_state.py "${ROOTS[@]}" --json      # everything, machine-readable

python3 audio_state.py "${ROOTS[@]}" --accept 7 --note "clean read"
python3 audio_state.py "${ROOTS[@]}" --reject 7 --note "garble at 4:12 on Anand"
```

`--reject` requires a note. The ledger at `audiobook/listen-ledger.json` is
append-only: a later verdict supersedes an earlier one and both stay in the
record.

### Reading the fallback count

`--report` totals `fallback chunks` — chunks whose accepted seed was not the
primary. Each one means the first candidate failed its gate and a retry saved it.
A clean pass rate with many fallbacks is a healthy retry budget, not a dependable
first attempt, and `--attempts 6` is a hard ceiling: exhaust it and the chapter
fails outright. Watch this number rather than the pass rate.

Remember what the gates cannot see. WER and coverage measure whether the right
words are present; they are blind to delivery, which is why the renderer records
`residue_peak` and why acceptance is human.

## M4B (when chapters are ready)

Packaging verifies the listen gate for exactly the chapters in the audio set, so
a 30-chapter preview is judged on its 30 and a full book on all 128. It refuses
unless every one is `accepted`, and it stamps the build with the text version.

```bash
$PY build_m4b.py \
  --audio-dir "../../../audiobook" \
  --voice-tag qvoice-uks03 \
  --chapters-root "../../../The Final Frontier Novel/chapters" \
  --work-root "../../../audiobook/qvoice-work" \
  --release-version v0.9.0 \
  --output "../../../audiobook/the-final-frontier-qvoice-uks03.m4b"
```

On refusal it prints the blocking chapters grouped by state and the commands that
clear them. `--no-verify-text` skips the gate for a private proof copy; the output
then records no text version and cannot say which draft it contains.

Two things carry the version. A sidecar `<output>.json` holds the release label,
`text_version_sha256`, and per chapter the spoken digest, WER, coverage, fallback
chunks, listen timestamp and note. And the M4B's own `comment` tag carries the
release and digest, so a stray copy separated from its sidecar still identifies
itself:

```bash
ffprobe -v quiet -show_entries format_tags=comment -of default=nw=1:nk=1 book.m4b
# v0.9.0 · text_version 0dbfa53f… · voice qvoice-uks03
```

To check whether a built audiobook is behind the manuscript, compare its
`text_version_sha256` against the current text:

```bash
python3 spoken_text.py --chapters-root "../../../The Final Frontier Novel/chapters"
```

A mismatch means it is behind; `audio_state.py --stale` says exactly which
chapters moved.

## Artifact index

| Path | What |
|------|------|
| `audiobook/*-chatterbox-uk-s03.wav` | Current local delivery WAVs |
| `audiobook/*-tiffany.wav` | Nova production WAVs (untouched by this tooling) |
| `audiobook/kokoro-audition/chatterbox-v2/*.log` | Batch / STT run logs |
| `audiobook/kokoro-audition/chatterbox-v2/stt-*.json*` | STT reports |
| `audiobook/kokoro-audition/common-voice-refs/*.wav` | Incumbent dialect-corpus seeds |
| `audiobook/kokoro-audition/emns-refs/*.wav` | EMNS candidate seeds |
| `audiobook/kokoro-audition/emns-refs/emns-refs.json` | Ref provenance + EMNS attribution |
| `audiobook/kokoro-audition/ref-audition*/` | Ref A/B renders, `passage.txt`, score JSON |
| `~/.cache/emns-slr136/` | EMNS corpus download (**outside** the repo, not committed) |

## Boundary rules

- Do **not** add mlx-audio / mlx-whisper to the Nova `uv` lock without a separate pin review.
- Do **not** overwrite `*-tiffany.wav` or write into `audiobook-studio/dist/`.
- Editorial voice acceptance is human; STT and prosody metrics are objective assists only.
- Keep the EMNS corpus download outside the repo. Only ship the short ref WAVs.
- EMNS is Apache 2.0: retain the attribution in `emns-refs.json` wherever a
  derived voice ships. The licence covers copyright only — it is not the
  speaker's consent to voice cloning, which is why this seed is fine for an
  open-source book and would need review for a commercial release.
