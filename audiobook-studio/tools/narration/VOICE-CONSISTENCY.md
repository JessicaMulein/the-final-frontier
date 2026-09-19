# Chapter-to-chapter voice consistency: what was tried, measured, and concluded

A record of the investigation into why the narrator's voice changes between chapters,
written so nobody repeats it. Most of what follows is negative results. They cost
real time and they are the reason the current production settings are what they are.

**Outcome: accepted as a limitation.** The defect is real, measurable, deterministic,
and inaudible inside a chapter. Three separate approaches failed to remove it. The
voice ships as it is.

---

## 1. The complaint

The listener, reviewing rendered chapters in sequence:

> the voice variability between files might be something of a problem. the voice is
> "the same" but yet "not".

> it goes deeper and then higher and back as we go along.

And later, on blind chapter-boundary clips, consistently:

> the timber or something changes at 16 seconds — it gets lighter, clearer.

Sixteen seconds was exactly the chapter boundary in those clips. The listener heard it
in **four out of four** boundary clips, across two different boundaries and two
different render conditions, "repeatably, identically."

## 2. The engine and settings under test

Fish S2 Pro (`mlx-community/fish-audio-s2-pro`) via a pinned `mlx-audio` submodule, on
Apple Silicon. Voice reference `hifitts-clean-92` (Hi-Fi TTS SLR109 `clean` subset,
SNR ≥ 40 dB), chosen by blind audition. Paragraph-level speaker turns with inline
`[short pause]` between sentences and 650 ms shaped gaps between paragraphs — pacing
variant "C", chosen by ear over four alternatives.

Every chapter is **one** `generate()` call. Fish appends each rendered segment into a
running `Conversation` before generating the next, so prosody context carries forward
natively.

## 3. The central finding: it is brightness, not pitch

This is the single most useful result, and it took far too long to reach.

The investigation began on the assumption that "deeper and then higher" meant
**fundamental frequency**. It does not. Measured across 17 rendered chapters:

| measure | head → tail | chapters affected |
|---|---|---|
| spectral centroid | **−84.8 Hz** mean (≈16%) | **17 / 17** |
| spectral tilt | **−3.02 dB/octave** | **17 / 17** |
| energy above 2 kHz | 0.0132 → 0.0076, roughly halved | 16 / 17 |

Meanwhile F0 moved the *wrong way* on half the test set: two boundaries the listener
heard as getting "lighter" stepped **downward** in pitch (−0.81 and −1.17 semitones).

Spectral centroid is the only measure that tracked the listener's judgements. It
ordered them correctly 7 times out of 7 across two independent blind tests.

### Metrics that did not track the listener's ear

Recorded because each one cost time and each one was, at the time, plausible:

1. Pitch span in semitones — anti-correlated with the voice chosen by ear
2. Dynamic range (p95−p10 frame RMS)
3. Median F0 — wrong *direction* on 2 of 4 boundary clips
4. F0 percentile floor (p20)
5. Timbre fingerprint distance (MFCC-based) — the largest distance of nine clips was rated "very good"
6. Articulation rate / pace profile
7. WER and coverage — flat across defective and clean takes alike
8. Repeated-span detection — a clean sibling had *more* repeated spans than the defect
9. Active-RMS level — brightness falls while level slightly *rises*, so loudness explains almost none of it (R² 0.049)

The lesson is not that measurement is useless. It is that **the listener's ear is the
acceptance gate**, and a metric earns trust only after it has predicted their
judgement more than once.

## 4. Interventions, in order

### 4.1 Deterministic anchoring — KEPT

Generate one identical discarded lead-in turn before each chapter so every chapter
starts from the same voice state, retaining its tokens in the running `Conversation`
but never shipping its audio.

Unlike the earlier QVoice warm-up, the anchor is an entire yielded segment, discarded
whole. There is no ASR boundary search and no cut inside a waveform, so it cannot
delete a chapter's first word — a defect class that did occur in the QVoice pipeline.

Verified invariant: the discarded anchor waveform is **byte-identical across
chapters** (SHA256 `3afcf960506252b0` at full chapter length). If that hash ever
varies, the experiment is invalid because the model did not start from one state.

Results, on the worst-measured run in the book:

| | production | anchored |
|---|---|---|
| boundary 10 → 11 | +0.84 st | **+0.38 st** |
| boundary 11 → 12 | −1.17 st | **−0.81 st** |
| F0 spread over the run | 12.32 Hz | **8.22 Hz** |

The listener picked both anchored clips as the closer join, blind, 2 out of 2.

**Kept** — it is generation-side, so it introduces no processing artifacts, and it
genuinely stabilises F0. It costs about 12–15% render time (RTF 1.54 against 1.32–1.37)
plus 23.7 s of generated-then-discarded audio per chapter.

It does **not** fix the audible defect, because the audible defect is brightness.

### 4.2 Time-varying spectral tilt correction — FAILED

Fit spectral tilt against time across a chapter, then apply the inverse as a smooth
bounded ramp, the same way `flatten_slope` corrects a level slope.

| condition | centroid spread across 4 chapters | worst boundary |
|---|---|---|
| uncorrected | **146 Hz** | 110 Hz |
| per-chapter target | 403 Hz | 114 Hz |
| absolute book-wide target, 250 Hz pivot | 371 Hz | 118 Hz |
| absolute, boost-only | 325 Hz | 119 Hz |

Every variant made brightness **less** uniform than doing nothing. One chapter's tail
was pushed to 901 Hz against a natural range of 482–568 Hz.

Root cause: spectral tilt is a regression slope over the log spectrum; centroid is an
energy-weighted mean frequency. **Holding one constant does not hold the other.** They
diverge badly across chapters. Tilt was chosen because it was easy to fit, not because
it had ever predicted the listener's ear.

### 4.3 Spoken chapter announcements — FAILED at the acoustic goal, KEPT for accessibility

Hypothesis: the ear was directly comparing a dull ending against a bright opening
across a 1.2 s gap, so interposing a spoken announcement would break the comparison.

Result: **all four clips still stepped**, with and without announcements. Three
seconds of speech plus two seconds of silence did not help.

The measurement explains why. Announcements are themselves short fresh generations,
and fresh generations are bright:

| generation (identical anchor, seed, reference, instruct) | centroid |
|---|---|
| ch10 announcement, 2.90 s | **593.2 Hz** |
| ch11 announcement, 2.46 s | **412.3 Hz** |
| ch12 announcement, 3.28 s | **558.2 Hz** |

A 181 Hz spread on identical settings, differing only in the words spoken. Chapter
heads span only 61 Hz by comparison. So an announcement does not buffer the
transition; it front-loads the brightness, or adds a second step.

The listener rated the 11→12 announced clip best. Its announcement (558 Hz) is
*brighter* than the chapter it introduces (485 Hz), so brightness arrives as an
overshoot that then settles, rather than as a rise.

**Announcements are kept** — for the honest reason that blind listeners need spoken
chapter titles to navigate. They were never going to mask the boundary.

### 4.4 Static per-chapter spectral matching — FAILED

The operation real audiobook mastering performs: one fixed, gentle, bounded EQ curve
per chapter, targeting the book's own median long-term spectrum. Median target so no
single chapter drags it; third-octave smoothing so it corrects broad character rather
than chasing formants; ±3 dB bound; loudness preserved exactly. A static curve cannot
pump, which was the failure mode of 4.2.

| | before | after |
|---|---|---|
| boundary 10 → 11 | +65.2 Hz | +68.1 Hz |
| boundary 11 → 12 | +78.8 Hz | +63.4 Hz |
| whole-chapter centroid spread | 24.7 Hz | 15.7 Hz |

One boundary improved 20%, the other got slightly worse.

The arithmetic that should have been done **before** building it:

- **between-chapter** average spread: **24.7 Hz**
- **within-chapter** head-to-tail decay: **126.0 Hz** (ch10), 52.5 (ch11), 18.8 (ch12)

Chapter 10's own head-to-tail fall is nearly twice the entire boundary step. A static
per-chapter curve can only correct the between-chapter term, so it was never capable
of closing a 65–79 Hz step. It corrected the small term.

`match_spectra.py` is retained as a working, documented implementation in case
per-chapter colour matching is ever wanted for a different reason. It is **not** in
the production path.

## 5. Mechanism: what the decay actually is

Two hypotheses were tested against the 17 rendered chapters.

| test | result | implication |
|---|---|---|
| brightness vs elapsed generated time | R² 0.180 | accumulation |
| brightness vs fraction through chapter | R² **0.206** | position |
| do longer chapters end darker? | **+7.74** Hz/min | longer chapters end *brighter* |
| is brightness following loudness? | R² 0.049 | no |

At the time this was read as refuting accumulating context. **That reading was
overstated**, and the error is recorded deliberately: the test assumed a *linear*
decay. A process that accumulates and then saturates fails that test while still being
accumulation. The correct conclusion is only that the decay is not linear in time.

What is solid: brightness is high at the start of a `generate()` call and falls as the
call proceeds, by roughly a constant *proportion* regardless of chapter length. Both
R² values are low (0.18–0.21), meaning the trend sits under normal sentence-to-sentence
variation — which is exactly why it is inaudible within a chapter and obvious when an
ending meets a beginning.

### The one idea never tested

Splitting a chapter into several `generate()` calls so brightness resets periodically,
trading one 126 Hz slide for several smaller ones. Generation-side, so no EQ artifacts.

Not attempted because the 181 Hz spread across the three announcements shows each
fresh call's brightness is substantially text-dependent and unpredictable. Chunking
could replace one step at a seam, where a listener expects change, with several steps
*inside* a chapter, where they do not. Cost to find out: about ten minutes of GPU on
chapter 10, the worst case.

## 6. What ships

| decision | status |
|---|---|
| Fish S2 Pro, `hifitts-clean-92`, interior instruct | in production |
| paragraph turns, `[short pause]`, 650 ms shaped gaps (variant C) | in production, approved by ear |
| deterministic anchor + fixed seed 70 | in production |
| V6 spectral gap repair, FFT 2048 | in production |
| spoken chapter announcements with canonical titles | in production, for navigation |
| any spectral EQ of the narration | **not in production** |

## 7. Do not retry

1. **Do not correct spectral tilt.** Tried three ways. Tilt and centroid are not
   interchangeable, and every variant made cross-chapter brightness worse.
2. **Do not expect announcements to mask the boundary.** They are fresh bright
   generations. Measured: 412–593 Hz on identical settings.
3. **Do not expect anchoring or seeding to control timbre.** They control F0. Brightness
   is driven by the text.
4. **Do not use static per-chapter matching to fix boundaries.** It addresses a 24.7 Hz
   term when the problem is a 126 Hz one.
5. **Do not trust F0 as the register variable.** It had the direction wrong on half the
   blind set.
6. **Do not switch to `--sentence-turns` to obtain read-along timings.** It would give
   exact sentence boundaries for free but changes the prosody that was approved by ear.
   Use forced alignment inside known paragraph windows instead.
7. **Do not re-roll for a better take.** With a fixed seed the output is deterministic;
   the same text produces the same brightness.

## 8. Process notes

Recorded because they cost more than the technical mistakes.

- **A metric was trusted before it had predicted anything.** Tilt was corrected because
  it was easy to fit. Centroid, the measure that had actually tracked the listener,
  was not the target until after two failures.
- **Arithmetic was skipped before building.** The static-matching implementation was
  written before comparing the 24.7 Hz between-chapter term against the 126 Hz
  within-chapter term. That one subtraction would have cancelled the work.
- **A refutation was claimed from a test of the wrong shape.** See §5.
- **Pipeline code was edited during a live render**, which broke chapters 7–14 with a
  `NameError` after an import was removed before its call site. Never edit the renderer
  while it is running; version it instead.
- **Evidence was deleted before being extracted.** A per-clip dropout measurement JSON
  documenting the Chatterbox glitch clips was removed during cleanup without first
  pulling its numbers out, while comparable QVoice fixtures were preserved.
- **Iteration continued past the point where input was wanted.** Repeatedly.

## 9. Reproducing the measurements

All tooling is in this directory and reads rendered WAVs; none of it needs a GPU.

| script | what it reports |
|---|---|
| `diagnose_brightness.py` | centroid, >2 kHz ratio, spectral tilt; head/tail and slope per chapter |
| `diagnose_accumulation.py` | elapsed-time vs fractional-position explanations; length-vs-final-brightness |
| `diagnose_voice.py` | F0 and level fingerprints, pairwise timbre distance |
| `chapter_trajectory.py` | per-chapter F0 trajectory, within-chapter slope, adjacent-chapter steps |
| `anchor_experiment.py` | the three-condition anchor test, including the byte-identity invariant |
| `boundary_clips.py` | blind chapter-boundary clips, optionally with announcements |
| `match_spectra.py` | static per-chapter spectral matching (retained, not in production) |
| `correct_tilt.py` | tilt correction (retained as a documented negative result) |
