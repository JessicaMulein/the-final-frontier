# Narration Engine — Design

## What already exists

Verified in `audiobook-studio/tools/kokoro-local/.venv` (the venv the current pipeline
uses), `mlx_audio/tts/models/` contains `fish_qwen3_omni`, `indextts`, `higgs_audio`,
`higgs_audio_v3`, `qwen3_tts`, `chatterbox`, `longcat_audiodit`, `voxcpm` and others.
Apple Silicon support for the candidate engines is therefore already installed, not
hypothetical.

Two findings shape this design.

**Fish S2 Pro is ready now.** Its `Model.generate` signature is:

```python
generate(text, voice=None, ref_audio=None, ref_text=None, instruct=None,
         max_tokens=1024, temperature=0.7, top_p=0.7, top_k=30,
         speed=1.0, chunk_length=300, ...)
```

It offers what the QVoice path lacks: a natural-language `instruct`, inline
performance tags, and `batch_generate(texts, ref_audios, ref_texts, instructs, ...)`
for true parallel candidates. Critically, `generate` accumulates a `Conversation`,
appending each rendered segment back as an assistant `VQPart` before the next
segment. Long-form continuity is native. Our warm-up-generate-then-trim-by-ASR
machinery exists only to approximate that, and it is the source of two of this
session's bugs.

**IndexTTS in mlx-audio is v1, not v2.** `indextts.py` exposes a single `ref_audio`
and a BigVGAN vocoder, with no emotion or style conditioning:

```python
generate(text, ref_audio, ref_mel=None, max_tokens=5000, sampler=None, ...)
```

IndexTTS2's separable timbre and emotion prompts — the capability that would let us
keep the current narrator's identity while borrowing a performance — are absent.
That is the porting contribution, and it is real work: a different architecture
(semantic tokens to mel to vocoder) plus an emotion conditioning module.

## Consequence for sequencing

Audition Fish S2 Pro first, because it costs configuration rather than a port and
already has instruct, tags, batching and native continuity. Treat the IndexTTS2 port
as a parallel track whose value is independent of the audition outcome. Do not port
first and audition later.

## Architecture

```
manuscript ──▶ planner ──▶ engine adapter ──▶ candidates ──▶ judges ──▶ selector
                                  ▲                                        │
                                  └────────── retry with new budget ◀──────┘
                                                                           │
                                            assembler ◀──────────── accepted unit
                                                 │
                                    chapter verify ──▶ book packager ──▶ listen list
```

### Planner

Splits the manuscript into units using the engine's own preferred granularity rather
than a fixed character count. For an engine with native continuity the unit is a
paragraph group inside one `generate` call; the engine handles internal chunking. For
an engine without it, units stay bounded by generated seconds, since delivery decay
tracks generation length. Planning is pure and deterministic: the same manuscript and
settings yield the same units, which is what makes resume and reproduction possible.

### Engine adapter

One narrow interface so judges, selector and assembler never know which engine ran:

```python
class Engine(Protocol):
    name: str
    def plan(self, text: str) -> list[Unit]: ...
    def render(self, units: list[Unit], *, style: Style, seeds: list[int]) -> list[Take]: ...
    capabilities: Capabilities   # batching, continuity, instruct, tags, duration control
```

`Capabilities` is consulted rather than assumed, so the adaptive policy can use
`batch_generate` where it exists and fall back to sequential rendering where it does
not. Adapters wrap Fish S2 Pro, QVoice (the existing pure-C runtime, kept working as
the control), and later IndexTTS2.

### Judges

Independent, each answering one question, each able to veto. The lesson from this
session is that no single metric survives contact with a real defect: pace scoring
preferred the take with the stuttered "four" because its overall rhythm was ideal,
and a first-third-versus-last-third drift gate flagged one of three bad units while
rating the best-sounding unit worst.

**Structural (hard reject).** Text present, exactly once, in order. First and last
words survive trimming, checked against the expected token sequence. No added or
omitted spans. Boundary alignment maps through replacement opcodes, so `two point
one` matching ASR's `2 1` cannot silently resolve to a later exact word.

**Acoustic (hard reject).** Self-similarity scan for a repeated span of 80–500 ms
within or across words — the "four-four" class, invisible to ASR by construction.
Onset burst, level step, clipping, codec loop, dropout, unnatural silence. Seam
residue. Within-unit level slope and articulation decay.

**Delivery (ranking).** Speaker similarity to the reference. Pitch span and dynamic
range, because flatness is the complaint and WER cannot see it. Articulation rate and
pause distribution against the chapter's own norm. Naturalness estimate.

**Consensus (ranking, and the most promising new signal).** Align sibling candidates
for the same text and score each word against the distribution of its siblings. When
seven candidates pronounce a word normally and one carries an extra acoustic segment,
the outlier is identifiable without any absolute threshold. This is what would have
caught the defect that two rerolls and every existing gate missed.

Judges emit scores and confidence, never a bare boolean, so the selector can tell
"clearly fine" from "nothing objected."

### Selector and adaptive budget

Render one candidate. If every hard gate passes and delivery scores sit inside the
chapter's norm with margin, accept. Otherwise widen: render a small batch, rank, and
accept the best that passes. If none passes, widen once more. If the budget is
exhausted, mark unresolved, record evidence, continue.

This keeps cost near one generation for clean units and concentrates compute where
something is actually wrong. It is the only way a single Mac can afford
generate-many, and it is why `batch_generate` matters more than raw model speed.

### Assembler

Level matching across units, within-unit slope removal, click-free joins, spectrally
shaped inter-unit tone rather than digital silence. This logic already exists and is
proven in `render_chapter_qvoice.py`; it moves into a shared module rather than being
rewritten.

### Evidence and resume

Per chapter, a manifest recording text, references, settings, seeds, every candidate
with its scores, gate outcomes, selection reason, and unit boundaries. Per book, a
single listen list naming only unresolved passages with timestamps and reasons.
Completed verified units are never regenerated on resume. Given identical inputs and
seeds the output is reproducible, so a defect reported by ear can be reproduced
exactly rather than approximately.

## Repository layout

```
audiobook-studio/tools/vendor/mlx-audio/        submodule, pinned upstream revision
audiobook-studio/tools/narration/               this subproject
    engines/         fish_s2.py, qvoice.py, indextts2.py
    judges/          structural.py, acoustic.py, delivery.py, consensus.py
    plan.py  select.py  assemble.py  book.py
    audition/        blind bake-off harness
    fixtures/        regression fixtures, one per confirmed defect class
    parity/          IndexTTS2 port parity harness
```

The existing `kokoro-local` tree is left alone. `drift.py`, `pace.py`,
`validate_stt.py` and `detect_loops.py` are imported, not duplicated; the QVoice path
keeps working as the control throughout.

## Submodule

`Blaizzy/mlx-audio` is already a dependency of this project, so it is the natural
upstream target and the natural submodule. Pinning it as a submodule replaces the
pip wheel with an editable checkout, which is what makes the IndexTTS2 work
contributable rather than a private patch. A push remote is added only when a pull
request is ready; the submodule itself tracks upstream read-only.

## Risks

**The Mac may be fast enough only with adaptive budgeting.** 64 GB unified memory is
ample for a 4B model quantized to 8-bit; throughput is the open question, not
capacity. Benchmark one minute of audio before estimating the book. If a candidate
costs more than roughly real time, the adaptive policy is not an optimization but a
precondition.

**Fish S2 Pro's licence is a research licence.** The author has accepted that
constraint for now, but it is recorded here because it bears on release, and because
reference-audio provenance carries the same distinction already documented for EMNS:
a copyright licence is not a speaker's consent to cloning.

**Inline tags can overact.** This novel needs restrained implication. Tags are a
lever to use sparingly, and the audition should include a no-tags condition so the
comparison is not confounded.

**Consensus scoring is unproven here.** It is the most promising new judge and the
least validated. It gets calibrated against the defects already confirmed by ear in
chapters one through three before it is trusted to gate anything.
