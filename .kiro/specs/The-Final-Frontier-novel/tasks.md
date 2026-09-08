# Implementation Plan: The Final Frontier Novel

## Overview

The deliverable is a novel: a complete 128-entry chapter arc and written chapters, supported by
planning references, human editorial records, a site-build exclusion, and a lightweight objective
checker. Creative planning and prose remain the product. The checker protects continuity and
bookkeeping; it never judges voice, beauty, pacing, tenderness, or emotional truth.

Work follows the revised prose-first sequence:

1. record every author decision that blocks continuity, especially the Nia source/casualty decision;
2. scaffold the visible manuscript project and isolate it from the lyrics site;
3. write the complete planning references and 128-entry Provisional Arc;
4. implement and test only the minimal chapter/batch checker needed for safe exploratory prose;
5. draft the eight-chapter Calibration_Batch while the global checker and complete mandatory test
   suite are finished in parallel;
6. complete the single Baseline_Revision_Pass, then obtain author approval only after the full
   checker and suite are green;
7. draft the remaining chapters in approved 4–8 chapter batches by movement; and
8. run manuscript-global objective and editorial acceptance.

Task markers:

- **[AUTHOR]** — a decision only the author can make; the written decision is an explicit artifact.
- **[EDITORIAL]** — a human Editorial_Gate that records evidence and `pass` or `revision`; it is
  never automated.
- **[HARD GATE]** — all dependent work is blocked until the stated condition is satisfied.
- **[EXPLORATORY]** — prose may inform calibration but is not approved continuity until reconciled
  after baseline approval.

No task in this plan is optional. Every principal property test, focused test, integration test, and
site-isolation test is required. Implementation code uses **Python**, as fixed by the design.

## Tasks

- [ ] 1. Settle and record the blocking creative decisions
  - Store each dated decision in `Mindwars Novel/planning/decisions.md` with the selected option,
    rationale, binding or deferred state, and affected Canon_Bible/arc records. Creating this nested
    planning file may create the manuscript root before front matter; it is not reachable by the
    current direct-child song markdown glob.

  - [x] 1.1 Record the title decision **[AUTHOR]**
    - **Decided (`DEC-001`, 2026-09-08): the novel is titled *The Final Frontier*,** after the source
      song that led to it. *The Country Behind the Eyes* and *The Quiet Radius* are retired.
    - “The Mindwars” remains the in-world historical name for the undeclared war and is not the cover
      title.
    - The title deliberately duplicates a source-song title, so the task 2.2 acknowledgment must
      state that relationship explicitly. The manuscript working directory stays `Mindwars Novel/`
      unless a separate explicit decision renames it.
    - _Requirements: 6.5, 9.10_

  - [~] 1.2 Resolve the Nia source/casualty braid **[AUTHOR] [HARD GATE]**
    - Explicitly `approve` or `reject` the major provisional Novel_Extension identifying Nia Calder
      as both (a) the source of the continuous ordinary morning Mara receives with an eight-second
      reception/transport offset and (b) the first casualty of a separate, later intrusive thought
      that feels self-authored.
    - If approved, record that the two events remain separate and that chronology does not prove the
      handshake caused the later arrival. If rejected, choose which single role Nia retains and
      assign the other role to a distinct named human source witness or casualty.
    - The rejection fallback must preserve canon, the four-POV roster/load, the 128-chapter and
      140,000-word architecture, and Safiya’s separate subtraction function unless another explicit
      approved decision changes them. The additional human remains a supporting witness unless a
      separate fifth-POV change is approved.
    - Record the decision in `decisions.md`; task 4.2 must mirror it as an approved, rejected, or
      retired Novel_Extension before any continuity-dependent ArcEntry or Prose_Body is written.
    - _Requirements: 1.1, 4.1, 4.7, 6.1, 6.9, 6.14_

  - [~] 1.3 Confirm Safiya Mir’s maternal language and review dependency **[AUTHOR] [HARD GATE]**
    - Confirm or replace the provisional private Kashmiri register and choose how much specific
      non-English wording may appear.
    - Name the required cultural/linguistic review. No specific non-English wording, phonetic
      description, invented phrase, or culturally specific lexical rendering may be drafted before
      that review; the canonical maternal-language loss and Safiya’s agency may not be weakened to
      avoid it.
    - _Requirements: 4.3, 6.11, 6.12, 6.16_

  - [~] 1.4 Fix the first casualty’s operational consequence **[AUTHOR]**
    - Select the emergency-routing incident influenced by the later arriving thought, its outcome,
      the harm the casualty fears, and the evidence point that can separate fact from shame.
    - Assign the consequence to Nia if task 1.2 approves her casualty role; otherwise assign it to
      the distinct casualty selected by the rejection fallback. Use serious stakes without mass
      casualty as a shortcut.
    - _Requirements: 1.4, 4.6, 6.9_

  - [~] 1.5 Fix institutional/geographic names and post-null public visibility **[AUTHOR]**
    - Confirm or replace `Northline Array`, the Open Channel Consortium, and the Civic Record Trust.
    - Decide whether the country and counties stay unnamed or receive fictional names, and whether
      post-null knowledge is shaped by public inquiry, partial release, or a contested archive.
    - Preserve the canonical affected-area wording and armistice facts regardless of naming.
    - _Requirements: 4.5, 6.4, 6.16_

  - [~] 1.6 Choose record-frame visibility **[AUTHOR]**
    - Choose a concise Front_Matter note plus rare in-story references, or explicitly defer the
      exact visibility to calibration.
    - Preserve the chronology: the Civic Record Trust is formed only after Julian sees the April
      negotiation record altered; Discovery-era logs and voice memoranda predate the Trust and are
      later deposited with provenance intact; rolling Trust deposits begin only after formation.
    - _Requirements: 2.5, 6.14, 9.10_

  - [~] 1.7 Fix character belief strength about handshake causation **[AUTHOR]**
    - Decide how strongly specific characters believe Mara’s content-free invitation relates to the
      later intrusive arrival.
    - Keep causation unproved and every Foreign_Signal origin/sender account unconfirmed.
    - _Requirements: 3.13, 4.11, 6.6, 6.7_

- [ ] 2. Create the manuscript scaffolding and front matter
  - [~] 2.1 Create the visible manuscript directory layout
    - Create `Mindwars Novel/`, `planning/`, and `chapters/` with `discovery-part/`,
      `private-defense-part/`, `mindwars-part/`, and `aftermath-coda/`.
    - Record the fixed convention
      `<movement>-<three-digit-global-sequence>-<descriptive-slug>.md`; sequence never resets by
      movement, and directory, filename, header, and ArcEntry must agree.
    - _Requirements: 9.1, 9.4, 9.5, 9.8_

  - [~] 2.2 Write `Mindwars Novel/front-matter.md`
    - **No longer blocked on build-source edits.** Site_Build is external to this workspace, so no
      local song discovery can reach this file. Still write task 3.1's exclusion contract first so
      the manuscript root is declared before the root-level markdown exists.
    - Title reads ***The Final Frontier*** per `DEC-001`. The source acknowledgment must state that
      the novel takes its title from the song *The Final Frontier*, so a reader is not left guessing
      why a listed source song shares the book's name.
    - Include `A novel by Jessica Mulein`, and
      `Novel prose © 2026 Jessica Mulein. All rights reserved.`
    - State that the Civic Record Trust formed after alteration of the April negotiation record;
      later received pre-Trust Discovery logs/voice memoranda with their original provenance; and
      accepts rolling deposits only after formation. State that archive custody does not certify
      each account’s objective truth or every witness’s later status.
    - If included, acknowledge *The Synaptic Frontier*, *Faraday*, *The Final Frontier*, and
      *The Radius* as source songs without importing sound-recording (`℗`) or performance ownership
      language into the prose notice.
    - _Requirements: 9.10, 9.11, 9.12_

- [ ] 3. Isolate the manuscript from the lyrics site build
  - **Scope revised per `DEC-008`.** Site_Build lives in a separate lyrics repository and is not
    present in this workspace, so there is no local `build_site.py` to edit and no local song
    discovery that could collect the manuscript. Requirements 9.2, 9.3, 11.9, and 12.8 are met by a
    Manuscript_Exclusion_Contract this project owns and the lyrics repository can adopt. This
    re-scope awaits author confirmation; see design open choice 9 for the two alternatives.

  - [~] 3.1 Write the Manuscript_Exclusion_Contract
    - Create `Mindwars Novel/exclusion-contract.json` declaring `Mindwars Novel` as an excluded
      source root, using a workspace-relative path resolved as a direct workspace child.
    - State the matching rule the contract requires of any consumer: compare resolved direct
      workspace children and skip exclusions **before** any markdown glob or visibility-plan
      fallback; never use substring, slug, front-matter, or missing-visibility-row heuristics; fail
      closed if the declared root would enter song discovery.
    - State the contract's honest limit: it does not prove the external Site_Build has adopted it.
      Record lyrics-repository adoption as an external follow-up outside this project's acceptance.
    - _Requirements: 9.2_

  - [~] 3.2 Write and pass the exclusion fixture test
    - Implement the contract's reference collector in `.tools/check_novel.py --site-exclusion`: walk
      direct workspace children, skip declared exclusions first, then glob markdown.
    - Build a temporary workspace with manuscript root markdown, nested planning/chapter markdown,
      and one valid control song plus visibility row. Assert only the control becomes a `Song` and
      no manuscript-derived path appears in lyrics, search, or index artifacts.
    - Also assert the committed contract names the real manuscript root, so it cannot drift from the
      directory it protects. Fail closed on a missing, malformed, or stale contract.
    - This test is mandatory and remains a standing regression gate.
    - _Requirements: 9.2, 9.3, 11.9, 12.8_

- [ ] 4. Write the planning reference documents
  - [~] 4.1 Define machine-readable planning schemas in `planning/record-schemas.md`
    - Specify readable Markdown containing fenced structured JSON records for `ChapterHeader`,
      `ArcEntry`, `POVProfile`, `VoiceBrief`, `TimelineEntry`, `CrossCut`, `CanonFact`,
      `NovelExtension`, `Reveal`, `MotifEvent`, `LiteralPhraseConstraint`, `Baseline`, `ArcChange`,
      `EditorialFinding`, `GateResult`, and `CheckerDiagnostic`.
    - Fix the delimited Chapter_Header to exactly one each of `movement`, `chapter`, `pov_id`,
      `timeline_id`, `motif_events`, `hook`, `words`, `length_class`, and `status`.
    - The checker reads fenced records only and never infers values from commentary.
    - _Requirements: 9.6, 12.1, 12.4, 12.5, 12.6_

  - [~] 4.2 Write `planning/canon-bible.md`
    - Record every Binding_Canon_Fact with source/location, including December discovery; the
      stranger’s continuous ordinary morning received by Mara with an eight-second
      reception/transport offset observed only by Mara; April term-sheet arrival; page-nine
      `transmit enable`; the affected area canonically described as `three counties wide`; the
      visitor eleven miles from the array; two post-null years; Tuesday kettle; three unhurried
      knocks; the Mindwars term; the consent rule; the later arriving thought; the null’s successful
      silence, defensive cost, and civilian harm; Safiya’s maternal-language loss; her free consent;
      and the physics/truth basis of Mara’s refusal.
    - Encode the December source-side interval as continuous. Never create a gap or altered duration
      in the source experience; store the eight seconds only as Mara’s receive/transport offset.
    - Record task 1.2’s braid decision. If approved, keep the source and casualty events distinct. If
      rejected, identify Nia’s retained role and the distinct supporting human assigned the other
      role, with no change to the four POVs or provisional scale.
    - Record Novel_Extensions for stable IDs, selected names, institutions, relationships, Safiya’s
      profession, and continuity-affecting dates, each with rationale, first dependency, affected
      records, and state.
    - Define Timeline_IDs, including the continuous December source interval/offset, April record
      alteration followed by Trust formation, composition-versus-deposit times for pre-Trust
      Discovery records, post-formation rolling deposits, shared null-night chronology, and Coda
      visit chronology. Store null extent as the canonical text, never as a derived radial measure.
    - Maintain unresolved Foreign_Signal theories with `confirmed: false`; a Reveal Ledger with
      knowers, owner, release, basis, and payoff for role identity, bidirectionality, casualty
      consequence, counterphase transmission, affected-area extent, Safiya’s Tuesday loss, and
      unresolved provenance; and Canon_Dialogue provenance records.
    - _Requirements: 3.13, 4.11, 6.1–6.16_

  - [~] 4.3 Write `planning/pov-roster.md`
    - Define four human POVs with one-to-one mappings: `CHAR-001`/`POV-MARA`,
      `CHAR-002`/`POV-NIA`, `CHAR-003`/`POV-JULIAN`, and `CHAR-004`/`POV-SAFIYA`.
    - For each, record selected name/aliases, knowledge, moral pressure, plot function,
      relationships, blind spots, reason to narrate, and movement coverage. Mark Mara as Anchor_POV
      and record provisional loads: Mara 56, Nia 32, Julian 33, Safiya 7.
    - Reflect task 1.2 without adding a POV under the rejection fallback. Preserve insertion and
      subtraction as distinct human harms, and forbid any Foreign_Signal or alleged-sender POV.
    - Link to `voice-briefs.md`.
    - _Requirements: 4.1–4.11, 9.8, 9.9_

  - [~] 4.4 Write `planning/voice-briefs.md`
    - Create one qualitative brief per POV covering syntax/rhythm, image and sensory families,
      emotional distance, omission/evasion/delayed notice, Reverb_Profile, and movement evolution.
    - Preserve Mara’s cathedral-to-room-tone profile and chapter-124 Coda_Turn; Nia’s treated booth
      with damaged return feed; Julian’s hearing chamber; and Safiya’s near microphone in a domestic
      room. Do not define sentence-length targets or style scores.
    - Add dated fields for calibration evidence and the Requirement 5.11 first-appearance review.
    - _Requirements: 5.1–5.9, 5.11, 5.13, 9.9_

  - [~] 4.5 Write `planning/motif-ledger.md` with the resolved event mapping
    - Record every Motif_Event’s stable ID, family, function, movement, planned chapter,
      representation mode, literal constraint or `none`, and ArcChange history.
    - Fix `MOT-CHAIN-01..03` exactly as: Discovery spectrum-to-bone; Private Defense wire-to-bone;
      Coda voice-through-air. Mindwars counterphase is connective context, not a fourth chain event,
      unless a later ArcChange creates a separate stable event and synchronizes ledger, outline, and
      headers.
    - Fix `MOT-COPPER-01..03` exactly as: Private Defense private boundary; Mindwars imperfect
      collective defense; Coda retained protection that cannot provide the needed remedy. Discovery
      copper references are unledgered foreshadowing, not a fourth event.
    - Record `MOT-COME-01..04`, `MOT-KNOCK-01..03`, `MOT-KETTLE-01..02`,
      `MOT-RADIUS-01..02`, `MOT-RECORD-01..03`, `MOT-YES-01`, and `MOT-WHOSE-01` with the
      design placements. One arrival-knock event spans chapters 116–117; kettle events occur only in
      118 and 124; Record_Progression has exactly three events.
    - Define only the two specified Literal_Phrase_Constraints: `Did I say yes?` only in Mindwars,
      with no fixed in-scope total; and `Whose was that?` exactly twice inside the declared
      Final_Passage in chapter 128 and nowhere else. Define machine-readable Final_Passage bounds.
    - Treat persistence in one scene/function as one event and exclude Incidental_Mentions.
    - _Requirements: 7.1–7.18_

  - [~] 4.6 Create `planning/editorial-log.md` and `planning/arc-changes.md`
    - In `editorial-log.md`, define evidence-bearing `EditorialFinding` and `GateResult` records with
      scope, chapter/batch, criterion, prose location, result, rationale, action, reviewer, and
      resolution. Never store numeric craft scores.
    - In `arc-changes.md`, define prior/revised state, rationale, affected chapters/documents,
      synchronization obligations, approval, and completion. A post-baseline change remains invalid
      until every listed reference is synchronized.
    - _Requirements: 1.16–1.18, 10.7, 10.8, 13.5–13.10_

- [ ] 5. Write the complete 128-entry Provisional Arc Outline
  - [~] 5.1 Create `planning/arc-outline.md` structure and global invariants
    - Create one ArcEntry per chapter with global sequence, filename, movement, Timeline_ID, POV_ID,
      one-sentence purpose, nonblank hook, reciprocal cross-cuts or `none`, estimated Length_Class,
      outlier purpose where applicable, status, calibration flag/purpose, record horizon, and reveal
      IDs.
    - Record the provisional 128-chapter/140,000-word allocation: 29 Discovery, 32 Private Defense,
      51 Mindwars, 16 Coda. Record at least 108 normal chapters, at most 20 purposeful outliers, no
      chapter over 2,500 words, and a placeholder for author-approved Final_Targets.
    - Record hook taxonomy/variation and the rule against more than two adjacent question-gap hooks.
    - _Requirements: 1.2–1.5, 2.1, 2.7, 2.10–2.12, 3.1, 3.6_

  - [~] 5.2 Write Discovery_Part entries, chapters 1–29
    - Expand the six design clusters: 1–5 noise floor; 6–10 a stranger’s morning; 11–15 the field;
      16–20 open invitation; 21–25 case zero refuses the name; 26–29 the door runs inward.
    - Preserve a continuous source-side morning and assign the eight-second reception/transport
      offset only to Mara’s observation. Keep the later intrusive thought a separate event.
    - Apply task 1.2: if the braid is approved, use Nia for both distinct roles; if rejected, assign
      source/casualty beats and reveal ownership to Nia or the selected supporting human without
      changing chapter count or the Mara 14/Nia 9/Julian 6 load.
    - Record `MOT-CHAIN-01` and `MOT-COME-01`, fair reveal horizons, and no causal promotion of the
      handshake or any sender theory.
    - _Requirements: 1.4–1.7, 3.2, 3.13, 6.3, 6.6, 6.7_

  - [~] 5.3 Write Private_Defense_Part entries, chapters 30–61
    - Expand clusters 30–35 copper and quiet; 36–42 benevolent offer; 43–49 April/page nine; 50–55
      put it in the record; 56–61 handle inside, with Mara 14/Nia 8/Julian 10.
    - Place `MOT-COPPER-01`, `MOT-CHAIN-02`, `MOT-RECORD-01`, `MOT-COME-02`, and
      `MOT-KNOCK-01` according to the ledger.
    - Place Trust formation only after Julian observes alteration of the April negotiation record.
      Treat Discovery logs/voice memoranda as pre-Trust contemporaneous sources later deposited;
      begin rolling Trust witness deposits only after formation.
    - _Requirements: 1.4–1.7, 3.3, 6.3, 6.14, 7.9–7.11_

  - [~] 5.4 Write Mindwars_Part entries, chapters 62–112
    - Expand clusters 62–69 no first shot; 70–77 mirror; 78–85 shield; 86–93 territory; 94–101
      affected area in the model; 102–108 null night; 109–112 history of quiet, with Mara 21/Nia
      14/Julian 16 and the movement longest by words.
    - Keep all null-night entries on one Timeline_ID with reciprocal non-redundant Cross_Cuts. No POV
      enters Safiya’s home.
    - Place `MOT-YES-01` in 73, `MOT-COME-03`, `MOT-COPPER-02`, `MOT-RADIUS-01`, and
      `MOT-RECORD-02`. Treat counterphase as chain context only, not `MOT-CHAIN-04` or another event
      absent a documented ArcChange.
    - Use `affected area canonically described as three counties wide` for null extent. Never derive
      a geometric radius from it. Confine active defender counterphase and rhetorical collective
      declaration to Mindwars.
    - _Requirements: 1.4–1.7, 3.4, 3.7, 3.9, 3.10, 6.4, 8.7_

  - [~] 5.5 Write Aftermath_Coda entries, chapters 113–128
    - Follow the chapter-level design: public intake/request, Safiya’s approach, one three-knock event
      seen from both sides, Safiya’s Tuesday account and exact loss, Mara receiving the affected area
      as people, valid consent, truth-based refusal, relay off/second kettle, dry human presence,
      staying, ordinary voice through air, entry against Mara, and outward threshold obligation.
    - Keep the Coda shortest; no Foreign_Signal return, counterphase, renewed combat, campaign, or
      adversary proof.
    - Place `MOT-KNOCK-02` across 116–117, `MOT-KETTLE-01` and calibration selection in 118,
      `MOT-RADIUS-02` in 120, `MOT-COME-04`/`MOT-KETTLE-02` and calibration selection in 124,
      `MOT-CHAIN-03` in 127, and `MOT-RECORD-03`/`MOT-KNOCK-03`/`MOT-WHOSE-01` in 128.
    - _Requirements: 1.4–1.7, 3.5, 3.11–3.13, 7.8–7.13, 8.2–8.6_

  - [~] 5.6 Audit Cross_Cut reciprocity, reveal links, record horizons, and chronology
    - Require a reciprocal target, shared timeline/consequence/disclosure, distinct
      Material_Narrative_Value, and replay boundary for each Cross_Cut; use `none` otherwise.
    - Verify December source continuity and Mara-only offset; separation of the later intrusive
      thought; task 1.2’s selected role mapping; April alteration before Trust formation; pre-Trust
      composition before later deposit; post-formation-only rolling deposits; and canonical null
      extent wording.
    - Resolve every reveal ID and prevent any purpose/hook from using knowledge beyond its
      narrator’s record horizon.
    - _Requirements: 1.6, 1.7, 4.12, 6.2, 6.7, 12.5_

  - [~] 5.7 Mark the eight-chapter Calibration_Batch
    - Mark chapters **1–5, 73, 118, and 124** as `calibration_selected`.
    - Record representative purposes: 73 tests counterphase consent and Mindwars tone; 118 tests
      Safiya’s own voice, concrete loss, first kettle event, and cultural/linguistic handling; 124
      tests Mara’s response, truth-based refusal, Coda_Turn, and Refused_Swell.
    - Mark 73, 118, and 124 `exploratory` until their surrounding final-continuity batches reconcile
      them. Julian is absent; record that his first later Discovery appearance requires the
      Requirement 5.11 Editorial_Gate before that batch can be approved.
    - _Requirements: 1.8–1.10, 5.11, 13.1_

  - [~] 5.8 Verify the complete provisional plan
    - Verify unique contiguous sequence `1..128`, one entry per planned file, no POV run over three,
      four contiguous movements in order, Anchor coverage, exact provisional POV loads, normal/outlier
      budget, all direct IDs, motif mappings, and reciprocal Cross_Cuts.
    - Confirm task 1.2 is resolved and mirrored before declaring the Provisional_Arc complete.
    - _Requirements: 1.1–1.5, 2.7, 2.8, 4.9, 11.4_

- [~] 6. Checkpoint — planning and site isolation complete **[HARD GATE]**
  - Ensure all planning checks and the site-isolation test pass; confirm every arc ID resolves and
    the complete Provisional_Arc contains no prose.
  - Do not begin any Prose_Body until task 1.2 is resolved and tasks 4–5 are complete.

- [ ] 7. Implement and test the minimal calibration checker
  - The minimal checker is `.tools/check_novel.py`, read-only and fail-closed. It enables safe
    exploratory calibration; it does not need global totals or the full property suite yet.

  - [~] 7.1 Set up Python test dependencies and calibration test layout
    - The repository currently has no suitable novel-checker dependency manifest. At this task—and
      not earlier—create `.tools/requirements-novel-dev.txt` with concrete exact versions selected
      at implementation time in the form `pytest==X.Y.Z` and `hypothesis==A.B.C`; no ranges or
      compatible-release specifiers.
    - Install those pinned dependencies only while executing this task. Create `.tools/tests/`, a
      shared fixture module, focused minimal-checker tests, and reserved modules for one principal
      test per Property 1–15.
    - _Requirements: 12.1, 12.14, 12.15_

  - [~] 7.2 Implement Chapter_File parsing, word counting, and Length_Class validation
    - Parse the header delimiters and exactly one required key each; fail safely when the prose
      boundary is ambiguous. Count whitespace-separated Prose_Words after the header only.
    - Validate filename/directory/header/ArcEntry movement and global sequence agreement; derive
      `microchapter` below 700, `normal` 700–1,600 inclusive, `long-outlier` 1,601–2,500 inclusive;
      reject above 2,500 and require planned purpose for outliers.
    - _Requirements: 2.8–2.11, 9.5–9.7, 12.1–12.3_

  - [~] 7.3 Implement direct-reference parsing and calibration-scope integrity
    - Parse fenced ArcEntry, Timeline_ID, POV_ID/Character_ID, VoiceBrief, and MotifEvent records
      needed by each calibration chapter. Report malformed, missing, duplicate, dangling,
      many-to-one, and disagreeing direct references without inferring from prose commentary.
    - Enforce local filename/header/outline agreement and only those Cross_Cut references whose
      requested batch scope contains the participating changed records.
    - _Requirements: 10.1–10.5, 12.4, 12.5_

  - [~] 7.4 Implement calibration-scope motif and literal checks
    - Enforce ledger/header assignment for the selected chapter/batch scope, including
      `MOT-YES-01` in 73, `MOT-KETTLE-01` in 118, and `MOT-COME-04`/`MOT-KETTLE-02` in 124.
    - Scan Prose_Bodies only. Normalize Unicode NFC and line endings while preserving exact case,
      order, and punctuation. Reject `Did I say yes?` outside Mindwars; do not impose an in-scope
      count. Do not guess a Final_Passage not yet in scope.
    - Enforce the resolved chain/copper mappings for any direct records encountered.
    - _Requirements: 7.2, 7.3, 7.7, 7.12, 7.14, 7.15, 12.6_

  - [~] 7.5 Implement chapter and batch modes with changed-reference consistency
    - Add `--scope chapter --chapter <path>` and `--scope batch --chapters <paths...>` plus changed
      reference inputs. Chapter mode reads only Direct_Planning_References; batch mode reports both
      chapter violations and stale changed references.
    - Accept the eight calibration files as a special pre-baseline batch while retaining the normal
      4–8 size rule for post-baseline Drafting_Batches.
    - _Requirements: 10.1–10.5, 10.9, 13.3_

  - [~] 7.6 Implement deterministic diagnostics, output, and exit behavior
    - Emit stable diagnostics with severity, code, scope, path/ID, observed, and expected fields;
      support text and JSON; exit `0` only for complete readable zero-violation scope, `1` for
      objective violations, and `2` for missing/malformed/incomplete input.
    - Keep the diagnostic allowlist free of voice, originality, pace, hook quality, tenderness,
      restraint, rhetorical force, and emotional-truth judgments.
    - _Requirements: 12.9–12.15_

  - [~] 7.7 Write the focused minimal-checker tests
    - Test required/duplicate/malformed headers; filename/header agreement; empty/Unicode/CRLF word
      counting; 699/700/1,600/1,601/2,500/2,501 boundaries; direct valid/dangling IDs; selected
      motif/literal rules; changed-reference drift; deterministic text/JSON diagnostics; and exits
      0/1/2.
    - Add timeline fixtures proving a continuous source interval with an eight-second offset only on
      Mara’s receive record and Trust formation after record alteration, with pre-Trust composition
      and later deposit timestamps.
    - _Requirements: 6.2, 9.6, 9.7, 10.1–10.5, 12.1–12.6, 12.9–12.15_

  - [~] 7.8 Pass the minimal calibration-readiness gate **[HARD GATE]**
    - Run the minimal focused suite and a synthetic chapter/batch smoke test. Record a
      `calibration-objective` GateResult proving site isolation, complete provisional planning,
      headers, filenames, counts/classes, direct IDs, calibration motif/literal rules,
      changed-reference consistency, diagnostics, and exit behavior are ready.
    - This gate unlocks exploratory calibration only; it does not claim global acceptance.
    - _Requirements: 1.10, 10.1–10.5, 13.1_

- [ ] 8. Draft exploratory calibration while completing the full checker and mandatory suite
  - After task 7.8, the prose track (8.1–8.7) and full-checker track (8.8–8.27) proceed in parallel.
    Exploratory prose is not blocked on global mode or all property tests. Baseline approval is.

  - [~] 8.1 Draft calibration chapters 1–3 **[EXPLORATORY]**
    - Chapter 1 `POV-MARA`: December noise-floor structure. Chapter 2 remains `POV-NIA` under
      either task-1.2 outcome. If Nia retains the source role, she lives the fully continuous
      ordinary morning with no experienced timing anomaly. If the rejection fallback gives the
      source role to a supporting human, follow the approved substitute Nia ArcEntry and present the
      source morning only through attributed contemporaneous material; do not add a fifth POV.
      Chapter 3 `POV-MARA`: verification fails once, then she receives experience rather than a
      message and measures the eight-second reception/transport offset.
    - Use a sensory-match Cross_Cut and preserve role/reveal ownership selected in task 1.2.
    - _Requirements: 2.4–2.6, 2.12, 3.2, 6.3, 9.6, 9.7_

  - [~] 8.2 Draft calibration chapters 4–5 **[EXPLORATORY]**
    - Chapter 4 remains `POV-NIA`. If Nia is the source, it returns to her continuous morning and
      adds lived ordinary detail without retroactively inserting a gap; otherwise it follows the
      approved substitute Nia purpose and keeps the distinct source account attributed rather than
      creating another POV. Chapter 5 returns to Mara as she confirms the reception timing, fails one
      alternative explanation, and recognizes that the structure tracks living attention.
    - Keep the later self-authored-feeling intrusive thought outside this opening event and withhold
      any identity conclusion not yet earned by the chosen role mapping.
    - _Requirements: 2.4–2.6, 3.2, 6.2, 6.9_

  - [~] 8.3 Draft calibration chapter 73 **[EXPLORATORY]**
    - `POV-NIA`, in the first counterphase-consent sequence. Use the exact protected question
      `Did I say yes?` and force consent to be specific, current, revocable, and local.
    - Test Nia’s authorization register, Mara’s technical context, and Mindwars tonal expansion;
      end on decision lock or moral remainder rather than another question gap.
    - _Requirements: 1.9, 3.4, 5.10, 7.14, 7.15_

  - [~] 8.4 Draft calibration chapter 118 **[EXPLORATORY] [HARD GATE]**
    - `POV-SAFIYA`. Give Safiya ownership of her Tuesday account: kettle on, eleven miles from the
      array, no foreign arrival, and the concrete maternal-language access she lost during the null.
      Assign `MOT-KETTLE-01`.
    - Test Safiya’s dry close voice, exact human loss, agency, and refusal to become an emblem. Apply
      task 1.3: draft no language-specific wording, phonetic description, or invented lexical detail
      before the required cultural/linguistic review; if review remains open, record that constrained
      deferral without weakening the loss.
    - _Requirements: 1.9, 5.10, 6.4, 6.11, 7.12, 8.1_

  - [~] 8.5 Draft calibration chapter 124 **[EXPLORATORY]**
    - `POV-MARA`. Affirm Safiya’s consent as genuine, then have Mara refuse because she lacks the
      mother/source truth and any construction could falsely self-authenticate as memory. Switch the
      relay off before putting on the second kettle.
    - Assign `MOT-COME-04` and `MOT-KETTLE-02`; execute the Coda_Turn from cathedral-scale
      explanation to dry human presence. Do not turn the refusal into a lecture on consent.
    - _Requirements: 1.9, 5.9, 6.11–6.13, 7.8, 7.12, 8.6_

  - [~] 8.6 Run the minimal checker over all eight calibration chapters
    - Run chapter scope for 1–5, 73, 118, and 124, then batch scope with every changed direct
      reference. Resolve all objective violations before editorial review while keeping
      representative chapters `exploratory`.
    - _Requirements: 10.1–10.5, 13.3_

  - [~] 8.7 Record the Calibration_Batch Editorial_Review **[EDITORIAL]**
    - Cite representative prose and record `pass`/`revision` for Mara, Nia, and Safiya Voice_Brief
      fidelity/separation; opening momentum; the clear fact that the source morning is continuous and
      the offset belongs only to Mara’s reception; Cross_Cut clarity; hook variety; pacing;
      testimony immediacy; cultural/linguistic handling in 118; Safiya’s ownership of loss; Mara’s
      truth-based refusal and Coda_Turn; tenderness, restraint, human cost, emotional truth, and
      Refused_Swell.
    - Julian is absent. Record the unresolved Requirement 5.11 first-appearance gate for the first
      later Discovery batch containing him.
    - _Requirements: 1.11, 2.13, 5.10, 5.11, 8.9, 13.4_

  - [~] 8.8 Expand `.tools/check_novel.py` to the complete objective checker
    - Add full planning parsing/referential integrity, Cross_Cut symmetry, POV run cap, roster/Anchor
      checks, Chapter_Local/Batch/Global scope separation, outline/file bijection, four ordered
      movement blocks, Final_Target totals, normal share, movement word relationships, full motif
      synchronization, all literal constraints including declared Final_Passage bounds, ArcChange
      atomicity, status demotion/synchronization, finalization requiring both gates, and
      `--site-exclusion` exercising generated-index isolation.
    - Enforce the resolved `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` mappings, canonical
      affected-area wording in structured canon records, source-side continuity/receive-offset
      chronology, and Trust formation/deposit chronology.
    - _Requirements: 1.6–1.18, 2.7–2.11, 4.1–4.10, 7.1–7.18, 10.1–10.9, 11.1–11.11, 12.1–12.15_

  - [~] 8.9 Build shared generated fixtures for the complete suite
    - Create reusable Hypothesis strategies and synthetic workspace builders for headers, bodies,
      ArcEntries, identifiers, Cross_Cuts, role-decision states, chronology, motif ledgers,
      movement allocations, status changes, gates, and source trees.
    - Include approved-braid, rejected-braid-with-fallback, and unresolved-braid states; continuous
      source timelines with Mara-only offset; exact canonical affected-area text; post-alteration
      Trust formation; later deposit of pre-Trust sources; and post-formation rolling deposits.
    - _Requirements: 1.1, 6.1–6.14, 12.1–12.10_

  - [~] 8.10 Write the principal property test for chapter plan/file bijection
    - **Property 1: Chapter plan and file bijection** — one principal Hypothesis test, at least 100
      generated examples.
    - **Validates: Requirements 11.3**; related 1.2, 1.3, 9.4, 12.2.

  - [~] 8.11 Write the principal property test for identifier/metadata integrity
    - **Property 2: Stable identifier and metadata referential integrity** — one principal test, at
      least 100 examples.
    - **Validates: Requirements 10.4**; related 1.4, 1.5, 4.2–4.4, 6.2, 7.1–7.3, 9.5, 9.6,
      10.3, 12.1, 12.4, 12.5.

  - [~] 8.12 Write the principal property test for Cross_Cut symmetry
    - **Property 3: Cross-cut graph symmetry** — one principal test, at least 100 examples.
    - **Validates: Requirements 1.6**; related 1.7.

  - [~] 8.13 Write the principal property test for prose word-count round trips
    - **Property 4: Prose word-count round trip** — one principal test, at least 100 examples,
      including empty, Unicode, punctuation, mixed line endings, and whitespace runs.
    - **Validates: Requirements 9.7**; related 10.3, 12.3.

  - [~] 8.14 Write the principal property test for length classes and limits
    - **Property 5: Length classification and limits** — one principal test, at least 100 examples.
    - **Validates: Requirements 2.8**; related 2.9–2.11, 12.3.

  - [~] 8.15 Write the principal property test for movement order and scale
    - **Property 6: Ordered movement architecture and scale** — one principal test, at least 100
      examples, including 29/32/51/16 and boundary variants.
    - **Validates: Requirements 11.4**; related 2.1–2.3, 3.1, 3.6–3.8, 11.5, 11.6, 12.7.

  - [~] 8.16 Write the principal property test for human POV/Anchor architecture
    - **Property 7: Human POV roster and Anchor coverage** — one principal test, at least 100
      examples.
    - **Validates: Requirements 11.7**; related 4.1, 4.2, 4.8–4.10, 8.8.

  - [~] 8.17 Write the principal property test for the POV run cap
    - **Property 8: POV run cap** — one principal test, at least 100 examples.
    - **Validates: Requirements 2.7**.

  - [~] 8.18 Write the principal property test for motif synchronization
    - **Property 9: Motif event synchronization** — one principal test, at least 100 examples.
    - Enforce chain events only in Discovery/Private Defense/Coda; counterphase as context absent an
      ArcChange; copper events only in Private Defense/Mindwars/Coda; Discovery copper as unledgered
      foreshadowing; two kettle events; and three Record_Progression events.
    - **Validates: Requirements 7.3**; related 7.1, 7.2, 7.12, 7.17, 7.18, 11.8.

  - [~] 8.19 Write the principal property test for ledger-driven literal constraints
    - **Property 10: Ledger-driven literal scope, count, and placement** — one principal test, at
      least 100 examples.
    - **Validates: Requirements 7.16**; related 7.7, 7.14, 7.15, 11.8, 12.6.

  - [~] 8.20 Write the principal property test for ArcChange/status atomicity
    - **Property 11: Post-baseline change and status atomicity** — one principal test, at least 100
      examples.
    - **Validates: Requirements 1.16**; related 1.17, 1.18, 7.3, 10.7, 10.8, 13.7–13.10.

  - [~] 8.21 Write the principal property test for local/global gate separation
    - **Property 12: Chapter-local and manuscript-global gate separation** — one principal test, at
      least 100 examples.
    - **Validates: Requirements 10.9**; related 10.1–10.5.

  - [~] 8.22 Write the principal property test for fail-closed inputs and exits
    - **Property 13: Fail-closed incomplete inputs and exit status** — one principal test, at least
      100 examples.
    - **Validates: Requirements 12.9**; related 11.1, 11.2, 12.10, 12.14, 12.15.

  - [~] 8.23 Write the principal property test for manuscript source exclusion
    - **Property 14: Manuscript source exclusion** — one principal test, at least 100 generated
      workspace trees with manuscript markdown and eligible control songs.
    - Assert against the Manuscript_Exclusion_Contract's reference collector, since Site_Build is
      external to this workspace.
    - **Validates: Requirements 9.3**; related 9.2, 11.9, 12.8.

  - [~] 8.24 Write the principal property test for independent final gates
    - **Property 15: Finalization requires both independent gates** — one principal test, at least
      100 examples.
    - **Validates: Requirements 11.11**; related 11.10.

  - [~] 8.25 Complete the required focused unit and edge-case suite
    - Cover all header, count, length, normal-share, orphan/duplicate/order, filename, Cross_Cut,
      roster, Anchor, POV-run, literal phrase, kettle, Record_Progression, status, incomplete-input,
      diagnostic exclusion, and local/global separation cases from the design.
    - Add explicit cases for unresolved braid blocking continuity; approved braid; rejected braid
      with distinct supporting human and unchanged four-POV/128-chapter allocation; continuous
      source interval plus Mara-only eight-second offset; Trust formation after altered April record;
      later deposit of earlier sources; rolling deposits only after formation; and rejection of any
      derived radial interpretation of the canonical `three counties wide` text.
    - Add exact accepted/rejected cases for `MOT-CHAIN-01..03` and `MOT-COPPER-01..03`.
    - _Requirements: 1.1, 2.7–2.11, 4.1–4.10, 6.2–6.14, 7.1–7.18, 9.5–9.7, 12.1–12.15_

  - [~] 8.26 Complete the required integration and process-smoke suite
    - Test site isolation; minimal calibration gate on 1–5, 73, 118, 124; chapter-local scope;
      changed-reference batch scope; complete 128-entry global scope; and process flow from planning
      through exploratory calibration, full-suite evidence, one Baseline_Revision_Pass, approval,
      revision, and reapproval.
    - Test front-matter prose rights and absence of recording/performance ownership language. Use
      synthetic records/prose only; the tests do not evaluate artistry.
    - _Requirements: 9.3, 9.11, 10.1, 11.1–11.9, 13.3_

  - [~] 8.27 Run and record the complete objective checker suite
    - Run every principal property test (at least 100 generated examples each), all focused tests,
      all integration/smoke tests, and the site-exclusion check. Resolve failures.
    - Record a `baseline-objective` GateResult showing complete global mode, deterministic exits, and
      a green mandatory suite. This evidence is required for task 10.2 and every post-calibration
      Drafting_Batch.
    - _Requirements: 1.14, 11.1–11.9, 12.14, 12.15_

- [~] 9. Checkpoint — calibration reviewed and full objective suite green **[HARD GATE]**
  - Ensure the eight exploratory chapters have clean local/batch results and recorded calibration
    Editorial_Review, and ensure the complete checker, all fifteen principal property tests, focused
    suite, integration suite, and site isolation pass.
  - Do not request Approved_Baseline approval or begin any post-calibration prose batch until this
    checkpoint passes.

- [ ] 10. Revise the baseline and obtain author approval
  - [~] 10.1 Perform the single Baseline_Revision_Pass
    - For every calibration finding, write either an Arc_Outline change or a rationale for no change
      in `planning/arc-changes.md`; synchronize affected outline, Canon_Bible, Motif_Ledger,
      POV_Roster, Voice_Brief, and exploratory chapter references in the same change.
    - Keep representative chapters exploratory until their later movement batches reconcile them.
    - _Requirements: 1.12, 1.13, 1.17_

  - [~] 10.2 Record Approved_Baseline and Final_Targets **[AUTHOR] [HARD GATE]**
    - Only after task 9 and task 10.1, record author approval, exact planned chapter count, and one
      inclusive total Prose_Word range. Record rationale if outside provisional ranges.
    - Resolve or explicitly carry forward allowed post-calibration choices such as title/frame
      visibility. All later structural changes require ArcChanges.
    - _Requirements: 1.14, 1.15, 1.18, 2.2, 2.3_

- [~] 11. Checkpoint — Approved_Baseline established **[HARD GATE]**
  - Ensure Final_Targets and approval are readable by global mode; rerun the full suite after any
    baseline-related checker/reference change.
  - No remaining movement batch may begin before this checkpoint.

- [ ] 12. Draft the remaining Discovery_Part chapters, 6–29
  - Every 4–8 chapter batch requires: clean chapter/batch objective checks; recorded chapter and
    batch Editorial_Review; and synchronized statuses plus affected Canon_Bible, Motif_Ledger,
    POV_Roster, Voice_Brief, ArcEntry, and ArcChange records before approval.

  - [~] 12.1 Draft chapters 6–10 — verification and institutional appetite
    - Follow the planned sequence: Julian audits funding disclosure and confirms the receiver lacks a
      transmit stage; continuous source-side detail appears through the assigned selected POV or an
      attributed supporting-witness record without adding a POV; Mara repeats reception and maps
      neural timing; Julian sees appetite gather; Mara narrows from location toward a person.
    - Keep the eight-second offset exclusively in Mara’s receive observation and apply task 1.2’s
      selected source role.
    - This is Julian’s first appearance after calibration; leave this batch unapproved until 12.2.
    - _Requirements: 2.4–2.7, 3.2, 4.12, 5.11, 6.2_

  - [~] 12.2 Record Julian’s first-appearance Editorial_Gate **[EDITORIAL] [HARD GATE]**
    - Cite representative chapter-6 prose and record `pass` or `revision` against Julian’s
      Voice_Brief: balanced review-facing clauses, documentary sensory field, institutional distance,
      complicity/evasion, and hearing-chamber Reverb_Profile.
    - Resolve any revision before approving the 6–10 batch.
    - _Requirements: 5.11, 5.13, 13.4_

  - [~] 12.3 Draft chapters 11–15 — the field
    - Show attention-linked frequencies, mind-as-field hypothesis, repeatable person-specific result,
      an ordinary call echoing a recorded pattern, rights pressure, and early institute–Consortium
      contact. End on the reversal that a person is inferred more precisely than a location.
    - _Requirements: 3.2, 4.6, 6.16_

  - [~] 12.4 Draft chapters 16–20 — open invitation and separate arrival
    - Mara sends the content-free handshake (`MOT-COME-01`); the casualty selected in task 1.2 later
      receives an intrusive instruction during routing and experiences it as self-authored.
    - Keep that later arrival separate from the continuous morning and preserve unproved causation.
    - _Requirements: 3.13, 6.6, 6.7, 6.9, 7.8_

  - [~] 12.5 Draft chapters 21–25 — the casualty refuses reduction
    - Release the source/casualty identities according to task 1.2. If approved, Nia owns both
      distinct events; if rejected, distribute confirmation between Nia and the selected supporting
      human without changing POV assignments or chapter totals.
    - Give the casualty ownership of the routing consequence and refusal to become “case zero”; let
      evidence, not coy withholding, determine the release point.
    - _Requirements: 1.4, 4.12, 6.8, 6.9_

  - [~] 12.6 Draft chapters 26–29 — the door runs inward
    - Show external interest, Mara’s confirmation that the apparatus can address as well as receive,
      controlled testing, and recognition of an arrival only after action. End Discovery on an
      uninvited crossing while sender and handshake causation remain unresolved.
    - _Requirements: 3.2, 3.13, 6.6, 6.7_

  - [~] 12.7 Record the Discovery_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon beats, movement turn, motif progression, POV distinction,
      cross-cut legibility, reveal fairness, hook variety, source continuity/offset clarity, and
      technical scale attached to human consequence. Reject artificial withholding.
    - _Requirements: 2.13, 2.14, 4.12, 8.9, 13.4_

- [ ] 13. Draft the Private_Defense_Part chapters, 30–61
  - Apply the same per-batch completion rule as task 12.

  - [~] 13.1 Draft chapters 30–35 — copper and quiet
    - Build the copper room on the page: mesh, seams, door, first measured silence. Nia experiences
      relief and the cost of permanent enclosure; Julian separates reception, transmission, and
      consent while the Consortium defaults assent.
    - Assign `MOT-COPPER-01` and `MOT-CHAIN-02` only to their ledgered functions.
    - _Requirements: 3.3, 6.8, 7.9, 7.10_

  - [~] 13.2 Draft chapters 36–42 — the benevolent offer
    - Dramatize real medical, linguistic, and emergency benefits as temptation. Cross-cut saleable
      institutional language against uncertainty over thought ownership. Julian brings the term
      sheet believing a contractual lock is possible.
    - _Requirements: 3.3, 4.6, 4.12, 6.8_

  - [~] 13.3 Draft chapters 43–49 — April, page nine
    - Give negotiation, specification reading, `transmit enable`, and consequence distinct scenes.
      Julian learns bidirectionality is architectural; the casualty learns their experience was used
      without permission.
    - Preserve April arrival and page-nine line as canon.
    - _Requirements: 3.3, 6.3, 6.8_

  - [~] 13.4 Draft chapters 50–55 — put it in the record
    - Mara refuses and demands preservation (`MOT-RECORD-01`). Julian first sees the April record
      altered, then forms the Civic Record Trust and opens post-formation rolling witness deposits.
    - Deposit Discovery-era logs/voice memoranda later as pre-Trust contemporaneous sources with
      original composition provenance. Never backdate Trust activity. Release the casualty’s feared
      operational consequence when evidence supports it.
    - _Requirements: 6.9, 6.14, 7.17, 7.18_

  - [~] 13.5 Draft chapters 56–61 — the handle inside
    - Draft, break, and repair specific/current consent protocol (`MOT-COME-02`, `MOT-KNOCK-01`).
      Copper spreads but cannot restore public life; Julian leaves Consortium representation and
      secures deposits. End on synchronized intrusion beyond private-room defense.
    - _Requirements: 3.3, 6.8, 7.8, 7.11_

  - [~] 13.6 Record the Private_Defense_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon, movement turn, motif progression, voice separation,
      institutional chronology, and whether a valid ethical rule remains a physically inadequate
      answer rather than a simple villain declaration.
    - _Requirements: 2.13, 4.12, 8.9, 13.4_

- [~] 14. Checkpoint — Discovery and Private Defense approved **[HARD GATE]**
  - Ensure all batches, movement Editorial_Gates, statuses, and references are synchronized and all
    tests remain green. Run site isolation with real manuscript files present.
  - Do not begin Mindwars drafting until this checkpoint passes.

- [ ] 15. Draft the Mindwars_Part chapters, 62–112
  - Apply the same per-batch completion rule as task 12. Active counterphase and rhetorical
    collective declaration begin and end in this movement.

  - [~] 15.1 Draft chapters 62–69 — no first shot
    - Show unrelated intrusive arrivals, no unifying sender, emergency classification hardening into
      policy, and Mara refusing a flag. Present the first casualty according to task 1.2, from Nia’s
      experience if approved or through a controlled supporting-witness account if rejected.
    - Keep every origin theory attributed and unconfirmed; characters do not yet possess a stable
      in-scene war name.
    - _Requirements: 3.4, 3.13, 6.5, 6.7_

  - [~] 15.2 Draft chapters 70–77 — mirror of the signal
    - Reconcile exploratory chapter 73 into final continuity and demote it to `revised` after any
      substantive change. Mara proves cancellation also transmits; Nia owns its consent meaning;
      the first bounded test leaves an afterimage that the protocol must confront.
    - Keep `MOT-YES-01` in Mindwars only.
    - _Requirements: 3.4, 6.8, 7.14, 10.8, 13.9_

  - [~] 15.3 Draft chapters 78–85 — a shield can enter
    - Officials seek automatic protection; Julian uses page nine to expose defenders adopting the
      feared capability without implying the Consortium sent the signal. Nia chooses one bounded
      risk. Mara’s public “we” remains answerable to named singular consents.
    - Assign `MOT-COME-03`.
    - _Requirements: 3.13, 6.8, 7.8, 8.7_

  - [~] 15.4 Draft chapters 86–93 — territory
    - Intensify effects and competing unconfirmed theories; reverse the frontier metaphor so minds
      are the shore being crossed; show local counterphase pockets and the predicted synchronized
      breach.
    - Counterphase is connective chain context only. Do not assign a fourth chain Motif_Event.
    - _Requirements: 3.4, 3.13, 6.7, 7.10_

  - [~] 15.5 Draft chapters 94–101 — the affected area in the model
    - Model a broad null as the only likely defense. Julian finds documentation that the affected
      area is canonically described as three counties wide; Mara predicts subtraction but cannot
      identify vulnerable memories; Nia refuses manufactured unanimity.
    - Use `MOT-RADIUS-01` thematically as an admission of cost, never as a computed geographic
      measurement or victory slogan.
    - _Requirements: 3.4, 6.4, 6.10, 7.13, 8.6_

  - [~] 15.6 Draft chapters 102–108 — null night
    - Hold seven reciprocal Cross_Cuts on one Timeline_ID: Nia in a consent shelter, Julian
      preserving authorization, Mara driving exact counterphase. The null affects civilians
      throughout an area canonically described as three counties wide, silences the Foreign_Signal,
      and diminishes Mara’s internal voice.
    - Do not enter Safiya’s home or preempt her Tuesday account. Record purposes for any
      simultaneity/interruption microchapters.
    - _Requirements: 1.6, 2.10, 2.11, 3.10, 6.10_

  - [~] 15.7 Draft chapters 109–112 — the history of quiet
    - Announce success without surrender/counterparty. Julian enters consent dispute and civilian
      uncertainty into history (`MOT-RECORD-02`); Nia rejects “saved” as a complete category; Mara
      ends active counterphase and withdraws behind retained copper (`MOT-COPPER-02`).
    - End the war-level action with the signal silent and uncounted absence remaining.
    - _Requirements: 3.9, 3.10, 6.5, 7.9, 7.17, 7.18_

  - [~] 15.8 Record the Mindwars_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon, turn, motifs, tactical consent pressure, human cost,
      non-glamorized counterphase, unresolved provenance, and a real non-triumphal conclusion with no
      adversary spectacle.
    - _Requirements: 2.13, 4.12, 8.6, 8.9, 13.4_

- [~] 16. Checkpoint — war-level action settled **[HARD GATE]**
  - Ensure all Mindwars batches and gates pass; active counterphase has ended; the Foreign_Signal is
    silent; the affected-area record retains canonical wording; provenance remains unconfirmed.
  - Do not begin Coda drafting until this checkpoint passes.

- [ ] 17. Draft the Aftermath_Coda chapters, 113–128
  - **Completion rule for every Coda batch:** run clean chapter/batch objective checks; record
    chapter-level and batch-level Editorial_Review; and synchronize Chapter_Status, Batch_Status,
    ArcEntries, Canon_Bible, Motif_Ledger, POV_Roster, Voice_Briefs, and affected ArcChanges before
    approval. No renewed signal, counterphase, campaign, or adversary proof is permitted.

  - [~] 17.1 Draft chapters 113–117 — public bill to threshold
    - Nia handles civilian-loss intake; Julian finds Safiya’s request and preserves her control of
      contact; Safiya crosses affected communities without becoming their spokesperson; chapters
      116–117 present the same three unhurried knocks from both sides as one `MOT-KNOCK-02` event.
    - Keep action in accounting, approach, and waiting, not combat.
    - _Requirements: 3.5, 6.4, 7.11, 8.2_

  - [~] 17.2 Draft chapters 118–123 — accounting and valid consent **[HARD GATE]**
    - Reconcile exploratory chapter 118 into final continuity; substantive changes set it and its
      ArcEntry to `revised`. Preserve Safiya’s Tuesday kettle, eleven-mile location, absence of
      foreign intrusion, and maternal-language loss (`MOT-KETTLE-01`).
    - Apply the completed cultural/linguistic review before any specific language wording. Safiya
      owns her account. Mara receives the affected area canonically described as three counties wide
      as people rather than geometry (`MOT-RADIUS-02`). Safiya’s affirmative, sober, repeated consent
      remains valid and does not compel a counterfeit.
    - _Requirements: 6.4, 6.11, 6.12, 7.12, 7.13, 8.1_

  - [~] 17.3 Draft chapters 124–128 — truthful refusal, staying, and outward duty
    - Reconcile exploratory 124 and demote on substantive change. Preserve relay-off/second-kettle
      Coda_Turn (`MOT-COME-04`, `MOT-KETTLE-02`), then narrow Mara to water, chairs, breath, and
      listening; let Safiya accept presence without calling it repair; use ordinary spoken voice
      through air in a consenting room (`MOT-CHAIN-03`).
    - In 128, Mara records an entry against herself (`MOT-RECORD-03`) and visits affected
      communities, knocking and waiting (`MOT-KNOCK-03`) rather than broadcasting. The declared
      Final_Passage contains `Whose was that?` exactly twice and nowhere else; no sender is solved.
    - _Requirements: 3.12, 3.13, 7.10, 7.16, 7.17, 8.3, 8.4, 8.6_

  - [~] 17.4 Record the Aftermath_Coda movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for contraction from public consequence to intimate encounter and
      outward obligation; Safiya’s genuine consent and autonomy; refusal as truth/physics rather
      than moral evasion; no imposed forgiveness; quiet human scale; unmet restoration; and the
      Refused_Swell.
    - Confirm the Coda has not become a fourth war movement. Do not use chapter length, room count,
      or numerical prose metrics as craft proxies.
    - _Requirements: 3.11, 3.12, 6.12, 6.13, 8.9, 8.10_

- [ ] 18. Run manuscript-global acceptance
  - [~] 18.1 Verify Final_Prerequisites
    - Require readable Approved_Baseline, Front_Matter, every planning reference, every planned
      Chapter_File, and passed Chapter_Local_Gate for each file. Missing/incomplete inputs return
      `incomplete` or `revision`, never pass.
    - _Requirements: 10.2, 11.1, 11.2_

  - [~] 18.2 Run the Manuscript_Global_Gate and site-exclusion audit
    - Verify plan/file bijection; contiguous movement order; exact approved count and total range;
      Mindwars longest/Coda shortest; 3–5 POVs with Anchor coverage; 80-percent normal share; all
      literal constraints; motif/header synchronization including chain/copper mappings; canonical
      chronology/extent records; statuses; and zero manuscript site entries.
    - Resolve every violation and require exit `0`.
    - _Requirements: 2.8, 3.7, 3.8, 9.3, 11.3–11.9, 12.7, 12.8, 12.14, 12.15_

  - [~] 18.3 Record the final Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for POV distinctness, Cross_Cut clarity, hook effectiveness, tonal
      coherence, originality, emotional truth, unresolved provenance, real war conclusion, and the
      Coda’s unmet obligation/quiet contraction. Use qualitative evidence, not scores.
    - _Requirements: 2.14, 8.10, 11.10, 12.13_

  - [~] 18.4 Mark the Manuscript `final`
    - Permit final status only when both Manuscript_Global_Gate and final Editorial_Gate pass.
      Synchronize every Chapter_Status, Batch_Status, ArcEntry, and affected reference record.
    - _Requirements: 10.7, 11.11, 13.7, 13.8_

- [~] 19. Final checkpoint
  - Ensure every required test and gate passes, all statuses/references are synchronized, the site
    still excludes the manuscript, and the final quiet ending remains intact. Ask the user if any
    questions arise.

## Notes

- All tests in tasks 3.2, 7.7, and 8.10–8.27 are mandatory. Each design property receives exactly
  one principal property-based test with at least 100 generated examples.
- The Nia braid is a major provisional Novel_Extension, not canon. Task 1.2 blocks the Canon_Bible,
  continuity-dependent ArcEntries, and all prose until approval or rejection plus fallback role
  assignment is recorded.
- The source morning is continuous. Only Mara measures the eight-second reception/transport offset;
  the later arriving thought is a distinct event.
- Null extent is stored and narrated as an affected area canonically described as three counties
  wide. `Silence has a radius` remains a thematic motif, not a geometric conversion.
- The Civic Record Trust forms after Julian sees the April negotiation record altered. Discovery
  logs/voice memoranda predate it and are later deposited; rolling Trust deposits start only after
  formation.
- `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` use the closed mappings in task 4.5. Counterphase and
  Discovery copper foreshadowing do not silently create extra events.
- Site_Build is external to this workspace. Isolation is delivered as the Manuscript_Exclusion_Contract
  plus its reference collector and standing test, which land before root-level front matter. A green
  local test proves the contract is well-formed and honored by a conforming collector; it does not
  prove the external lyrics repository has adopted it. Adoption is an external follow-up.
- The four Canon_Sources are reference copies at `songs/The Synaptic Frontier.md`,
  `songs/Faraday.md`, `songs/The Final Frontier.md`, and `songs/The Radius.md`.
- Tasks 7.1–7.8 are the minimal objective gate for exploratory calibration. Full checker work and
  all mandatory tests run in parallel with task 8’s prose track; task 9 blocks baseline approval and
  every post-calibration batch until the complete suite is green.
- Calibration comprises chapters 1–5, 73, 118, and 124. Representative chapters stay exploratory
  until their final-continuity movement batches reconcile them. Julian’s first later appearance has
  a separate Requirement 5.11 Editorial_Gate.
- **[EDITORIAL]** findings remain human-only. The checker never scores prose craft.
- Every post-baseline 4–8 chapter batch, including every Coda batch, needs clean objective checking,
  chapter/batch editorial review, and synchronized statuses/references before approval.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "3.1"] },
    { "id": 1, "tasks": ["1.1", "3.2"] },
    { "id": 2, "tasks": ["1.2", "2.2"] },
    { "id": 3, "tasks": ["1.3"] },
    { "id": 4, "tasks": ["1.4"] },
    { "id": 5, "tasks": ["1.5"] },
    { "id": 6, "tasks": ["1.6"] },
    { "id": 7, "tasks": ["1.7"] },
    { "id": 8, "tasks": ["4.1"] },
    { "id": 9, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6"] },
    { "id": 10, "tasks": ["5.1"] },
    { "id": 11, "tasks": ["5.2"] },
    { "id": 12, "tasks": ["5.3"] },
    { "id": 13, "tasks": ["5.4"] },
    { "id": 14, "tasks": ["5.5"] },
    { "id": 15, "tasks": ["5.6"] },
    { "id": 16, "tasks": ["5.7"] },
    { "id": 17, "tasks": ["5.8"] },
    { "id": 18, "tasks": ["6"] },
    { "id": 19, "tasks": ["7.1"] },
    { "id": 20, "tasks": ["7.2"] },
    { "id": 21, "tasks": ["7.3"] },
    { "id": 22, "tasks": ["7.4"] },
    { "id": 23, "tasks": ["7.5"] },
    { "id": 24, "tasks": ["7.6"] },
    { "id": 25, "tasks": ["7.7"] },
    { "id": 26, "tasks": ["7.8"] },
    { "id": 27, "tasks": ["8.1", "8.3", "8.4", "8.5", "8.8", "8.9"] },
    { "id": 28, "tasks": ["8.2", "8.10", "8.11", "8.12", "8.13", "8.14", "8.15", "8.16", "8.17", "8.18", "8.19", "8.20", "8.21", "8.22", "8.23", "8.24", "8.25", "8.26"] },
    { "id": 29, "tasks": ["8.6", "8.27"] },
    { "id": 30, "tasks": ["8.7"] },
    { "id": 31, "tasks": ["9"] },
    { "id": 32, "tasks": ["10.1"] },
    { "id": 33, "tasks": ["10.2"] },
    { "id": 34, "tasks": ["11"] },
    { "id": 35, "tasks": ["12.1"] },
    { "id": 36, "tasks": ["12.2"] },
    { "id": 37, "tasks": ["12.3"] },
    { "id": 38, "tasks": ["12.4"] },
    { "id": 39, "tasks": ["12.5"] },
    { "id": 40, "tasks": ["12.6"] },
    { "id": 41, "tasks": ["12.7"] },
    { "id": 42, "tasks": ["13.1"] },
    { "id": 43, "tasks": ["13.2"] },
    { "id": 44, "tasks": ["13.3"] },
    { "id": 45, "tasks": ["13.4"] },
    { "id": 46, "tasks": ["13.5"] },
    { "id": 47, "tasks": ["13.6"] },
    { "id": 48, "tasks": ["14"] },
    { "id": 49, "tasks": ["15.1"] },
    { "id": 50, "tasks": ["15.2"] },
    { "id": 51, "tasks": ["15.3"] },
    { "id": 52, "tasks": ["15.4"] },
    { "id": 53, "tasks": ["15.5"] },
    { "id": 54, "tasks": ["15.6"] },
    { "id": 55, "tasks": ["15.7"] },
    { "id": 56, "tasks": ["15.8"] },
    { "id": 57, "tasks": ["16"] },
    { "id": 58, "tasks": ["17.1"] },
    { "id": 59, "tasks": ["17.2"] },
    { "id": 60, "tasks": ["17.3"] },
    { "id": 61, "tasks": ["17.4"] },
    { "id": 62, "tasks": ["18.1"] },
    { "id": 63, "tasks": ["18.2"] },
    { "id": 64, "tasks": ["18.3"] },
    { "id": 65, "tasks": ["18.4"] },
    { "id": 66, "tasks": ["19"] }
  ]
}
```
