# Narration Engine — Requirements

## Problem

The current QVoice pipeline produces individually good chapters but cannot produce a
*book*. Three chapters took an entire working session, and every chapter needed a
human to listen end-to-end and report defects by timestamp, after which a unit was
re-rendered and the chapter reassembled. At roughly 130 chapters that process does
not finish.

Two separate deficiencies drive this:

1. **Expressiveness ceiling.** The locked recipe records its own verdict:
   "Excellent overall; slightly less emotive than ideal, but do not change the
   recipe." A 4.8-second neutral dialect reference is being asked to supply both
   speaker identity *and* an audiobook performance. The listener describes the
   result as "a weird flat affect while still having emotion."

2. **Defects that survive every automated gate.** Confirmed this session:
   - An intra-word codec stutter on "six fifty-four" that ASR normalizes to a
     single correct token, so WER, coverage, loop, drift and pace checks all pass.
     Two reroll attempts were accepted by machine and rejected by ear.
   - A boundary-alignment bug that deleted "Two point one" and "Ravi" from chapter
     one while chapter WER stayed at 0.023.
   - A cold-start burst on the first words of a chapter, scored zero clicks.
   - A warm-up residue that read as a stutter at a seam, with residue below every
     threshold in place at the time.

   Whisper is a language model; it reconstructs damaged speech into correct text.
   Text-based QA is therefore structurally blind to the defect class that actually
   reaches a listener.

## Goal

One command produces a finished, verified audiobook. Human attention is spent on a
short voice audition up front, plus a bounded listen list the system cannot clear
on its own — not on reviewing 130 chapters.

## Non-goals

- Paid per-character APIs. Ruled out on cost.
- Rented GPU. Ruled out; the only hardware is one 64 GB Apple Silicon Mac.
- Zero human listening. Not credible for any engine available to us. The target is
  reducing listening from hours to minutes, with the residue explicitly located.

## Requirements

### 1. Engine selection is evidence-based

**User story:** As the author, I want the narration engine chosen by a blind
comparison on my own prose, so that the decision rests on how it sounds rather
than on benchmark claims.

#### Acceptance criteria

1. WHEN an audition is run THE SYSTEM SHALL render an identical passage set through
   every configured engine and reference combination.
2. THE SYSTEM SHALL include the current QVoice recipe as an unlabeled control.
3. THE SYSTEM SHALL reject structurally failing candidates before presentation, so
   the listener compares each engine's best passing take rather than its accidents.
4. THE SYSTEM SHALL present audio under opaque labels, holding the mapping in a file
   that is not read during scoring.
5. THE SYSTEM SHALL cover, at minimum: technical exposition, quiet unease, grief
   without theatre, dialogue with attribution, procedural detail containing clock
   times and numerals, and a chapter ending.
6. WHEN scoring is complete THE SYSTEM SHALL reveal the mapping and record the
   result as the engine of record, with its references and settings.

### 2. Expressiveness is a measured, separable property

**User story:** As the author, I want the narrator's identity and her performance
controlled independently, so that fixing flat affect does not change who is reading.

#### Acceptance criteria

1. WHERE an engine accepts a style or instruction input separately from its speaker
   reference THE SYSTEM SHALL expose both as independent configuration.
2. THE SYSTEM SHALL record prosodic range per unit — pitch span, dynamic range,
   articulation rate, pause distribution — so that flatness is visible as a number
   and comparable across engines.
3. THE SYSTEM SHALL NOT treat lexical-fidelity metrics as evidence of delivery
   quality. A flat, evenly paced read scores well on WER by construction.
4. WHEN an engine supports inline performance tags THE SYSTEM SHALL keep them out of
   the manuscript, applying them only in the spoken transform.

### 3. Acoustic defects are detected without relying on transcripts

**User story:** As the author, I want the machine to catch the stutters and glitches
I currently find by ear, so that a passing chapter means something.

#### Acceptance criteria

1. THE SYSTEM SHALL detect a repeated acoustic span within a word or across adjacent
   words, in the 80–500 ms range, independently of the transcript.
2. THE SYSTEM SHALL compare each candidate against its sibling candidates for the
   same text and flag any word whose duration, level, or spectral trajectory is an
   outlier from the consensus of passing siblings.
3. THE SYSTEM SHALL verify that the first and last words of every unit survive
   trimming, by comparing against the expected token sequence rather than against
   the next available exact match.
4. THE SYSTEM SHALL detect onset bursts, level steps, clipping, codec loops,
   dropouts, and unnatural silence, and record each with a timestamp.
5. THE SYSTEM SHALL measure within-unit decay of level and articulation and reject a
   unit that degrades beyond a configured bound.
6. WHEN a defect class is confirmed by ear and missed by the gates THE SYSTEM SHALL
   gain a regression fixture reproducing it, retained in the repository.
7. THE SYSTEM SHALL NOT report a chapter as verified on the strength of text metrics
   alone.

### 4. Candidate generation replaces manual rerolling

**User story:** As the author, I want the system to try again by itself, so that a
bad take never reaches my ears.

#### Acceptance criteria

1. WHEN a unit is rendered THE SYSTEM SHALL be able to produce multiple independent
   candidates for it.
2. WHERE the engine supports batched generation THE SYSTEM SHALL use it rather than
   looping, to keep candidate cost near-linear in wall time.
3. THE SYSTEM SHALL spend candidates adaptively: accept a unit that passes every gate
   with margin on its first candidate, and escalate only where confidence is low.
4. WHEN no candidate passes within the budget THE SYSTEM SHALL record the unit as
   unresolved with its evidence, and continue rather than abort the book.
5. THE SYSTEM SHALL select among passing candidates on delivery quality, not on
   first-pass order.
6. THE SYSTEM SHALL cache candidates and their scores, so that a later decision can
   be revisited without regenerating audio.

### 5. Long-form consistency is structural

**User story:** As the author, I want chapter twelve to sound like chapter one.

#### Acceptance criteria

1. WHERE an engine carries generated audio forward as context THE SYSTEM SHALL use
   that mechanism in preference to re-conditioning each unit from cold.
2. THE SYSTEM SHALL bound the generated length of a unit, having measured that
   delivery decays with generation length.
3. THE SYSTEM SHALL keep speaker identity within a configured similarity band across
   the whole book, measured against the reference, and flag drift.
4. THE SYSTEM SHALL match levels across units and remove within-unit level slope.
5. THE SYSTEM SHALL join units without clicks, residue, or silence that reads as a
   dropout.

### 6. One command produces the book

**User story:** As the author, I want to start a render and come back to a finished
audiobook.

#### Acceptance criteria

1. THE SYSTEM SHALL accept the manuscript root and produce per-chapter audio and a
   chaptered M4B in a single invocation.
2. THE SYSTEM SHALL run unattended for hours, on one machine, without supervision.
3. WHEN interrupted THE SYSTEM SHALL resume from durable state without regenerating
   completed, verified units.
4. THE SYSTEM SHALL write a manifest per chapter recording text, references,
   settings, seeds, candidate scores, gate results, and boundaries.
5. WHEN the run completes THE SYSTEM SHALL emit one listen list naming only the
   passages it could not clear, with timestamps and the reason for each.
6. THE SYSTEM SHALL be deterministic given identical inputs, settings, and seeds, so
   that a reported defect can be reproduced exactly.
7. THE SYSTEM SHALL keep the existing QVoice path working and unmodified while this
   engine is being proven.

### 7. Upstream contribution is a first-class output

**User story:** As the author, I want the model work we do to live upstream rather
than as a private patch we maintain forever.

#### Acceptance criteria

1. THE SYSTEM SHALL depend on a pinned upstream revision, recorded by commit.
2. WHERE a capability is missing upstream THE SYSTEM SHALL implement it as a clean
   model-level change, separable from audiobook-specific code.
3. THE SYSTEM SHALL provide a parity harness comparing a ported implementation
   against the reference implementation under greedy decoding.
4. THE SYSTEM SHALL keep audiobook production code out of any upstream patch.
5. THE SYSTEM SHALL record model licences and reference-audio provenance, including
   the distinction between a copyright licence and a speaker's consent to cloning.
