# Narration Engine — Tasks

Ordered so that the engine question is answered before any pipeline is built around
an engine, and so the existing QVoice path keeps working throughout.

## Phase 1 — Prove the hardware and the engine

- [ ] 1. Preflight the machine
  - Record chip, core counts, unified memory, macOS version, free disk.
  - Confirm headroom for an 8-bit 4B model plus codec and caches.
  - _Requirements: 6.2_

- [ ] 2. Add `Blaizzy/mlx-audio` as a pinned submodule
  - Place at `audiobook-studio/tools/vendor/mlx-audio`, record the commit.
  - Leave the existing `kokoro-local` venv and QVoice path untouched.
  - _Requirements: 7.1, 6.7_

- [ ] 3. Stand up an isolated narration environment
  - Separate venv; install the submodule editable.
  - Verify the QVoice pipeline still runs unchanged afterwards.
  - _Requirements: 6.7, 7.1_

- [ ] 4. Smoke-test Fish S2 Pro on one paragraph
  - Clone from `uk-southern-female-03-tight.wav` with its transcript as `ref_text`.
  - Time it. Record real-time factor and peak memory.
  - _Requirements: 1.1, 6.2_

- [ ] 4.1 Benchmark the candidate budget
  - Compare `generate` against `batch_generate` for 4 and 8 candidates.
  - Decide whether adaptive budgeting is an optimization or a precondition.
  - _Requirements: 4.2, 4.3_

## Phase 2 — Make the machine see what the ear hears

Built before the audition, because the audition must present each engine's best
*passing* take rather than its accidents.

- [ ] 5. Build the regression fixture set from confirmed defects
  - Extract, from chapters one to three, one fixture per class: intra-word stutter
    ("six fifty-four"), truncated opening ("Two point one", "Ravi"), cold-start
    burst, warm-up residue stutter, within-unit fade, articulation outlier.
  - Record for each what a listener heard and which gates passed it.
  - _Requirements: 3.6_

- [ ] 6. Repeated-span detector
  - Self-similarity scan for a repeated acoustic span of 80–500 ms.
  - Must flag the "six fifty-four" fixture and must not flag its clean siblings.
  - _Requirements: 3.1_

- [ ] 7. Structural boundary judge
  - Exact first and last word survival, checked against the expected token sequence.
  - Boundary mapping through replacement opcodes.
  - Must catch both truncation fixtures.
  - _Requirements: 3.3_

- [ ] 8. Acoustic judge
  - Onset burst, level step, clipping, codec loop, dropout, unnatural silence,
    seam residue, within-unit level and articulation decay.
  - Port the proven detectors rather than rewriting them.
  - _Requirements: 3.4, 3.5_

- [ ] 9. Delivery metrics
  - Speaker similarity, pitch span, dynamic range, articulation rate, pause
    distribution. Reuse `pace.py` and the prosody metrics.
  - _Requirements: 2.2, 2.3_

- [ ] 10. Consensus judge
  - Align sibling candidates; score each word against the sibling distribution.
  - Calibrate against the fixture set. Report agreement with the listener's calls
    honestly, and do not promote it to a hard gate unless it earns it.
  - _Requirements: 3.2_

- [ ] 11. Gate harness
  - Run all judges over a directory of audio and emit per-unit scores plus a
    timestamped listen list. No verified verdict from text metrics alone.
  - _Requirements: 3.7, 6.5_

## Phase 3 — Blind audition

- [ ] 12. Assemble the passage set
  - Technical exposition, quiet unease, grief without theatre, dialogue with
    attribution, procedural detail with clock times and numerals, chapter ending.
  - Draw from the existing audition excerpts plus chapters one to three.
  - _Requirements: 1.5_

- [ ] 13. Render the conditions
  - Fish S2 Pro: UK-s03 clone, restrained instruct, no tags.
  - Fish S2 Pro: UK-s03 clone, restrained instruct, sparse tags.
  - Fish S2 Pro: EMNS n599 clone.
  - QVoice current recipe, as the unlabeled control.
  - Four candidates per passage, hard gates applied, best passing take kept.
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.4_

- [ ] 14. Blind package and scoring
  - Opaque labels; mapping withheld during scoring.
  - Score for expressiveness and for identity separately, since the complaint is
    flat affect and the risk is losing the narrator.
  - _Requirements: 1.4_

- [ ] 15. Reveal and record the engine of record
  - Record references, settings, and the prosody numbers behind the choice.
  - _Requirements: 1.6, 2.2_

- [ ] 16. Ten-minute stamina render
  - One full chapter through the winner. Gate it. Listen once.
  - Decide go or no-go before any book-scale work.
  - _Requirements: 5.1, 5.2, 5.3_

## Phase 4 — The one command

- [ ] 17. Planner
  - Deterministic units, engine-aware granularity, bounded generated length.
  - _Requirements: 5.2, 6.6_

- [ ] 18. Engine adapters behind one interface
  - Fish S2 Pro and QVoice, with declared capabilities.
  - _Requirements: 5.1_

- [ ] 19. Adaptive candidate policy and selector
  - One candidate when confidence is high; escalate on doubt; cache candidates and
    scores; select on delivery, not order; record unresolved and continue.
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 20. Shared assembler
  - Extract level matching, slope removal, joins and inter-unit tone from
    `render_chapter_qvoice.py` into a shared module used by every engine.
  - _Requirements: 5.4, 5.5_

- [ ] 21. Chapter verification and manifest
  - Full-chapter gate pass; manifest with text, references, settings, seeds,
    candidates, scores, decisions, boundaries.
  - _Requirements: 6.4_

- [ ] 22. Book driver with durable resume
  - One invocation over the manuscript root; resume without regenerating verified
    units; unattended for hours.
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 23. M4B packaging and the single listen list
  - Chaptered M4B; one consolidated listen list with timestamps and reasons.
  - _Requirements: 6.1, 6.5_

- [ ] 24. Reproducibility check
  - Same inputs and seeds reproduce the same audio; a reported defect reproduces
    exactly.
  - _Requirements: 6.6_

## Phase 5 — IndexTTS2 port (parallel track, independent value)

Worth doing whatever the audition decides, because separable timbre and emotion is
the cleanest answer to flat affect, and because mlx-audio has only v1.

- [ ] 25. Parity harness
  - Same text, reference, settings, greedy decoding. Compare tokens, logits,
    speaker embeddings, and audio against the reference implementation.
  - _Requirements: 7.3_

- [ ] 26. Weight conversion
  - Checkpoint name and layout mapping; record revision and conversion hashes.
  - _Requirements: 7.1_

- [ ] 27. Model implementation
  - Semantic-token path, mel stage, vocoder, and the emotion conditioning module
    that v1 lacks. Separable timbre and style prompts. Duration control.
  - _Requirements: 2.1, 7.2_

- [ ] 28. Upstream-ready packaging
  - Clean model-level change, conversion script, small reproducible fixture,
    documented checkpoints and memory use. No audiobook code in the patch.
  - _Requirements: 7.2, 7.4_

- [ ] 29. Provenance and licences
  - Model licences; reference-audio provenance; the distinction between a copyright
    licence and a speaker's consent to cloning.
  - _Requirements: 7.5_
