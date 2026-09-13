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

- [x] 1. Settle and record the blocking creative decisions
  - Store each dated decision in `The Final Frontier Novel/planning/decisions.md` with the selected
    option, rationale, binding or deferred state, and affected Canon_Bible/arc records. Creating this
    nested planning file may create the manuscript root before front matter, which is safe: Site_Build
    is external to this workspace, so no local song discovery can reach any path here.

  - [x] 1.1 Record the title decision **[AUTHOR]**
    - **Decided (`DEC-001`, 2026-09-08): the novel is titled *The Final Frontier*,** after the source
      song that led to it. *The Country Behind the Eyes* and *The Quiet Radius* are retired.
    - “The Mindwars” remains the in-world historical name for the undeclared war and is not the cover
      title.
    - The title deliberately duplicates a source-song title, so the task 2.2 acknowledgment must
      state that relationship explicitly.
    - The manuscript root is `The Final Frontier Novel/`, renamed from `Mindwars Novel/` per `DEC-010`
      to match the title. `Mindwars_Part` and the `mindwars-part/` chapter directory are unchanged.
    - _Requirements: 6.5, 9.10_

  - [x] 1.2 Resolve the Nia source/casualty braid **[AUTHOR] [HARD GATE]**
    - **Resolved by `DEC-002`, 2026-09-09: approved in the protected causally linked form.** Nia
      Calder holds both roles. In December, Mara’s receive-only apparatus has no transmit stage; it
      receives Nia’s continuous ordinary morning with an eight-second reception/transport offset and
      identifies her person-specific channel/address. In Chapters 16–20, Mara deliberately adds a
      temporary bench transmit path and sends the content-free handshake through that same address.
      The later handshake may have reached Nia and produced the wanting, but nobody can prove it.
    - Page-nine `transmit enable` later establishes broader bidirectional capability and architectural
      danger. It is not evidence that the December rig transmitted.
    - Five binding constraints follow, recorded in `decisions.md` and the design’s braid section.
      Downstream tasks must honor all five: causation is never confirmed; the adversary still owns the
      war beyond the first casualty; the archive’s adversary attribution is an uncorrectable inference;
      insertion (Nia) and subtraction (Safiya) remain distinct; and Nia’s emotional movement resolves
      through usable self-trust even though factual causation does not.
    - Role-splitting fallbacks are retired. Canon, the four-POV roster/load, and the 128-chapter and
      140,000-word architecture are unchanged.
    - Task 4.2 must mirror this as `status: approved-extension`, `authority: DEC-002`, with the
      causal linkage recorded separately as `unverified`.
    - _Requirements: 1.1, 4.1, 4.7, 6.1, 6.9, 6.14_

  - [x] 1.3 Confirm Safiya Mir’s maternal language and review dependency **[AUTHOR] [HARD GATE]**
    - **Resolved by `DEC-003`, 2026-09-09.** Safiya retains a public heritage language and works as
      an occasional community interpreter. The null removes only the private layer she and her mother
      built together—invented words, private grammar, and shared reference. The heritage base is
      unspecified by the author everywhere, including planning.
    - Task 4.2 records exactly `heritage_base: unspecified_by_author`. No drafting or planning record
      may replace that value or infer/invent real-world linguistic, geographic, religious, ethnic, or
      political particulars from Safiya’s name or from the unspecified base.
    - Wording follows a staged ladder: describe-never-quote is the default and always available;
      invented private-layer words are permitted sparingly; real heritage wording remains unavailable
      unless `DEC-003` is reopened. No real language is named or quoted.
    - Review dependency: **community-portrayal review required** because Safiya is a
      heritage-community interpreter inside the affected area. Linguistic review of wording is not
      required under the current decision. Its absence may never weaken the canonical loss or
      Safiya’s agency.
    - Binding guardrail: no real-world conflict is used as allegory, parallel, or thematic echo for
      the Mindwars, and no record may lean on inferences drawn from Safiya’s name for thematic weight.
      The former Kashmiri proposal is historical and retired, not a live instruction.
    - _Requirements: 4.3, 6.11, 6.12, 6.16_

  - [x] 1.4 Fix the first casualty’s operational consequence **[AUTHOR]**
    - Select the emergency-routing incident influenced by the later arriving thought, its outcome,
      the harm the casualty fears, and the evidence point that can separate fact from shame.
    - **Resolved by `DEC-004`, 2026-09-09.** Triage under scarcity: two calls, one available advanced
      unit. A **wanting** arrives — a certainty indistinguishable from her own judgment, not an
      instruction, because Mara's handshake is content-free and the canonical doctrine edits what
      people want. She routes against ordinary practice because she is sure. One real death, singular
      and documented, no mass casualty.
    - She fears not only a fatal call but that the certainty was never hers, so she cannot own the
      mistake as her own. That is why she refuses "case zero."
    - Evidence point, chapters 50–55: dispatch timestamps show the death was already unsurvivable
      before her routing. The logs clear her decision and are silent on authorship, so the relief does
      not relieve. That same log becomes the anchor the histories misread as the adversary's first
      loss, which makes `DEC-002` constraint 3 concrete.
    - Two `unverified` origin accounts for the wanting coexist and are never confirmed: the record's
      adversary instruction, and Mara's private fear that her own later handshake bled. Binding
      `DEC-007` gives Mara high private conviction, Nia no unsupported attribution, and Julian a
      professional adversary attribution he privately knows is inference.
    - Call specifics, unit type, descriptive county context (never a proper county name under
      `DEC-005`), and supporting-character names stay adjustable during task 5.2 without an
      ArcChange; the structure above does not.
    - _Requirements: 1.4, 4.6, 6.9_

  - [x] 1.5 Fix institutional/geographic names and post-null public visibility **[AUTHOR]**
    - **Resolved by `DEC-005`, 2026-09-09.** Keep the exact names `Northline Array`, `Open Channel
      Consortium`, and `Civic Record Trust`. Keep the country and every individual county unnamed;
      generic county functions and descriptive locations remain available.
    - Use a **contested-archive** model after the null: official summaries and the Trust’s
      provenance-preserving releases compete publicly. Trust releases honor witness embargo and
      release conditions, and complete holdings are not presumed open; the Trust is nevertheless a
      visible ongoing counter-record, not a secret archive or one-time partial disclosure.
    - No unified public inquiry adjudicates between the records. Trust custody warrants provenance,
      not objective truth, so the first-casualty adversary attribution remains the uncorrectable
      inference required by `DEC-002` constraint 3 and both origin accounts remain `unverified`.
    - Preserve the exact canonical affected-area wording `three counties wide` / `affected area
      canonically described as three counties wide`, without named-county substitution or geometric
      derivation. Preserve the settled armistice facts, all `DEC-002`/`DEC-003`/`DEC-004`/`DEC-007`
      constraints, and the pre-Trust/post-formation composition, deposit, and release chronology.
    - _Requirements: 4.5, 6.4, 6.16_

  - [x] 1.6 Choose record-frame visibility **[AUTHOR]**
    - **Resolved by `DEC-006`, 2026-09-09.** Use one concise Front_Matter framing note plus rare
      in-story references. The overall visibility model is binding and is not deferred to calibration.
    - Keep reader-facing chapter labels restrained. Planning metadata, record horizons, and detailed
      chain-of-custody facts stay out of prose unless a specific reference is dramatically necessary;
      do not add routine source notes, transcript apparatus, docket labels, or heavy archival labeling.
    - Calibration may test whether an individual rare reference earns its place, but may not replace
      the selected restrained model with a more visible archival apparatus.
    - Preserve the chronology: the Civic Record Trust is formed only after Julian sees the April
      negotiation record altered; Discovery-era logs and voice memoranda predate the Trust and are
      later deposited with original provenance; rolling Trust deposits begin only after formation.
    - Preserve `DEC-005` as the separate in-world public model: conditioned Trust releases compete
      with official summaries, complete holdings are not presumed public, and provenance does not
      certify objective truth.
    - _Requirements: 2.5, 6.14, 9.10_

  - [x] 1.7 Fix character belief strength about handshake causation **[AUTHOR]**
    - **Resolved by `DEC-007`, 2026-09-09: selected option 1, “Asymmetric, and Nia moves toward
      release.”** Mara holds a high, mostly unvoiced private conviction that her later handshake
      caused Nia’s wanting. Her guilt-seeking tendency to make herself central makes the belief
      non-authoritative rather than confirmatory.
    - Nia refuses both unsupported origin accounts and rejects Mara’s attempted confession as
      appropriation in concept; no literal dialogue is prescribed. She does not absolve Mara.
    - Julian professionally records the adversary attribution because it is the only institutionally
      enterable account, while privately knowing it is inference rather than proof.
    - Nia eventually stops needing to know the origin and regains usable self-trust. This resolves the
      emotional question without deciding causation, forgiving Mara, or validating the archive.
    - Both origin accounts remain `unverified`, with no reveal owner or release window. No instrument
      or narrator confirms either.
    - _Requirements: 3.13, 4.11, 6.6, 6.7_

- [x] 2. Create the manuscript scaffolding and front matter
  - [x] 2.1 Create the visible manuscript directory layout
    - Create `The Final Frontier Novel/`, `planning/`, and `chapters/` with `discovery-part/`,
      `private-defense-part/`, `mindwars-part/`, and `aftermath-coda/`.
    - Record the fixed convention
      `<movement>-<three-digit-global-sequence>-<descriptive-slug>.md`; sequence never resets by
      movement, and directory, filename, header, and ArcEntry must agree.
    - _Requirements: 9.1, 9.4, 9.5, 9.8_

  - [x] 2.2 Write `The Final Frontier Novel/front-matter.md`
    - **Ready for implementation.** Task 3.1's exclusion contract is complete, so the manuscript root
      is declared before root-level markdown is created. Task 3.2 is a later standing regression test,
      not a prerequisite for this file; no task-1 framing decision remains open.
    - Title reads ***The Final Frontier*** per `DEC-001`. The source acknowledgment must state that
      the novel takes its title from the song *The Final Frontier*, so a reader is not left guessing
      why a listed source song shares the book's name.
    - Include `A novel by Jessica Mulein`, and
      `Novel prose © 2026 Jessica Mulein. All rights reserved.`
    - Per `DEC-006`, use one concise Civic Record Trust framing note. State that the Trust formed after
      alteration of the April negotiation record; later received pre-Trust Discovery logs/voice
      memoranda with their original provenance; and accepts rolling deposits only after formation.
      State that archive custody does not certify each account’s objective truth or every witness’s
      later status. Preserve `DEC-005`: conditioned, provenance-preserving Trust releases compete with
      official summaries, complete holdings are not presumed public, and no adjudicating public
      inquiry resolves the records.
    - Do not introduce routine source notes, transcript apparatus, chain-of-custody detail, or heavy
      archival labeling. In-story record references remain rare and dramatically necessary.
    - Acknowledge all five Canon_Source songs—*The Synaptic Frontier*, *Faraday*, *The Final Frontier*,
      *The Radius*, and *Case Zero*—without importing sound-recording (`℗`) or performance ownership
      language into the prose notice. State that the novel takes its title from *The Final Frontier*;
      do not list *One-Time Pad* as a Canon_Source.
    - _Requirements: 9.10, 9.11, 9.12_

- [x] 3. Isolate the manuscript from the lyrics site build
  - **Scope revised per `DEC-008`.** Site_Build lives in a separate lyrics repository and is not
    present in this workspace, so there is no local `build_site.py` to edit and no local song
    discovery that could collect the manuscript. Requirements 9.2, 9.3, 11.9, and 12.8 are met by a
    Manuscript_Exclusion_Contract this project owns and the lyrics repository can adopt. Confirmed
    binding by the author 2026-09-09; options A and C are retired and choice 9 is closed.

  - [x] 3.1 Write the Manuscript_Exclusion_Contract
    - Create `The Final Frontier Novel/exclusion-contract.json` declaring `The Final Frontier Novel` as an excluded
      source root, using a workspace-relative path resolved as a direct workspace child.
    - State the matching rule the contract requires of any consumer: compare resolved direct
      workspace children and skip exclusions **before** any markdown glob or visibility-plan
      fallback; never use substring, slug, front-matter, or missing-visibility-row heuristics; fail
      closed if the declared root would enter song discovery.
    - State the contract's honest limit: it does not prove the external Site_Build has adopted it.
      Record lyrics-repository adoption as an external follow-up outside this project's acceptance.
    - _Requirements: 9.2_

  - [x] 3.2 Write and pass the exclusion fixture test
    - Implement the contract's reference collector in `.tools/check_novel.py --site-exclusion`: walk
      direct workspace children, skip declared exclusions first, then glob markdown.
    - Build a temporary workspace with manuscript root markdown, nested planning/chapter markdown,
      and one valid control song plus visibility row. Assert only the control becomes a `Song` and
      no manuscript-derived path appears in lyrics, search, or index artifacts.
    - Also assert the committed contract names the real manuscript root, so it cannot drift from the
      directory it protects. Fail closed on a missing, malformed, or stale contract.
    - This test is mandatory and remains a standing regression gate.
    - _Requirements: 9.2, 9.3, 11.9, 12.8_

- [x] 4. Write the planning reference documents
  - [x] 4.1 Define machine-readable planning schemas in `planning/record-schemas.md`
    - Specify readable Markdown containing fenced structured JSON records for `ChapterHeader`,
      `ArcEntry`, `POVProfile`, `VoiceBrief`, `TimelineEntry`, `CrossCut`, `CanonFact`,
      `NovelExtension`, `Reveal`, `MotifEvent`, `LiteralPhraseConstraint`, `Baseline`, `ArcChange`,
      `EditorialFinding`, `GateResult`, and `CheckerDiagnostic`.
    - In `CanonFact`, require `authority_basis` with one of `author-decision`, `requirement`, `lyric`,
      or `ratified-note`; require the adopting requirement/decision for `ratified-note`; and require
      speaker/attribution and epistemic-limitation fields for first-person lyric testimony. A `lyric`
      source must resolve to one of the exact five Canon_Source paths in `DEC-014`; *One-Time Pad*
      cannot resolve as canon. Permit citations to Production_Notes and other non-lyric metadata as
      advisory records, but never as binding facts without higher-tier adoption.
    - Fix the delimited Chapter_Header to exactly one each of `movement`, `chapter`, `pov_id`,
      `timeline_id`, `motif_events`, `hook`, `words`, `length_class`, and `status`.
    - The checker reads fenced records only and never infers values from commentary.
    - _Requirements: 9.6, 12.1, 12.4, 12.5, 12.6_

  - [x] 4.2 Write `planning/canon-bible.md`
    - Apply `DEC-011` and `DEC-014`: every Binding_Canon_Fact records `authority_basis`; lyric and
      higher-tier decisions may bind continuity; a `ratified-note` identifies the requirement or
      author decision that adopted it; first-person lyric facts preserve speaker attribution and
      epistemic limitation; and material from unratified Production_Notes, style prompts, exclude
      lists, generation workflow, credits, or rights metadata remains labeled advisory/non-story and
      cannot establish identity, chronology, naming, continuity, or a Literal_Phrase_Constraint.
    - Record `DEC-012` and `DEC-015` as one coherent Novel_Extension family: `ESP` means
      **Electronic Speech Pairings**, one authorized link is a **pairing**, and the term is a contested
      late institutional simplification rather than supernatural ESP. Preserve post-Discovery coinage,
      Julian/institutional/public register, rare technical Mara usage, and Nia's resistance. Record
      exactly four non-overlapping modes: `RECEIVE` passively observes high-dimensional structure in
      one living person's field with no write or transmit stage; `INTRUDE` is an active unconsented or
      uncalibrated write to a person-specific address, limited to nonsemantic salience, valence,
      urgency, certainty, preference, or wanting; `CANCEL` is an unaddressed subtractive counterphase
      field; and `PAIR` transports deliberately offered near-natural internal speech between exactly
      two living people with current specific revocable mutual consent and Pair_Calibration unique to
      that pair. Repeated calibration may become fluent, but no unoffered thought, imagery, emotion,
      memory, or background mentation crosses; pause or revocation stops transport; and calibration
      cannot transfer to a replacement, dead or absent person, simulation, archive, model, or
      reconstruction.
    - Record all eight binding `CANCEL` properties, because the null cannot be classified without them
      and `INTRUDE` structurally forbids what the null does. `CANCEL` carries no person-specific
      address, which is why it is not `INTRUDE`; it is nonsemantic in both directions; its only effect
      is removal or degradation of access to mental content and faculties, inserting nothing; the
      affected faculties, memories, and people are unpredictable before, unenumerable during, and
      incompletely mapped after the event; it has no additive inverse, so nothing it removed can be
      restored by another `CANCEL`, by `PAIR`, or by any combination of modes; individual consent is
      obtainable only for a bounded local cancellation while area scale is institutionally authorized
      and never individual consent from every affected person; it is confined to `Mindwars_Part`; and
      cancelling the Foreign_Signal supplies no provenance. Record the bounded Chapter 73 test and
      null night as the same mode at two scopes. Record the absent inverse as a second, independent
      physical reason Chapter 124's refusal is truthful, alongside the missing source corpus, and keep
      Nia's insertion injury categorically distinct from Safiya's defensive subtraction.
    - Record the `DEC-015` evidence boundary independently from narrative inference: each authorized
      Pairing_Session preserves Consent_State_Metadata and Transport_Metadata; Content_Recording is a
      separate explicit mutual choice initialized off; and a Pairing_Transcript contains only
      protocol-carried content from that recorded session. Metadata cannot reconstruct semantics, and
      no transcript proves truth, intent, memory provenance, unoffered thought, complete mental state,
      Nia's earlier causation, or the Foreign_Signal's provenance. Endpoint compromise may be a bounded
      danger only, never hidden provenance closure. Pairing cannot restore Safiya's corpus-less private
      maternal layer.
    - Record `DEC-014`, which supersedes `DEC-013`: the Canon_Source set is exactly
      `songs/The Synaptic Frontier.md`, `songs/Faraday.md`, `songs/The Final Frontier.md`,
      `songs/The Radius.md`, and `songs/Case Zero.md`. *Case Zero* publication is author-approved and
      in progress, and its lyric has the same tier-3 authority as the other four Canon_Source lyrics.
      The *One-Time Pad* draft is preserved in git history and removed from the working tree; it is
      unpublished and noncanonical for book purposes. Do not add it as a Canon_Source or continuity
      authority.
    - Inventory *Case Zero* lyric facts with `authority_basis: lyric`, exact source/location,
      speaker, and attribution/limitation fields: Nia’s reported alarm, shower, road call,
      twenty-minute interval, and console at ten to seven; her report that the receiver owned the
      eight-second offset and she experienced no gap; two close calls, one available unit, and one
      death; the five-person/whiteboard consent confrontation; current, specific, revocable consent
      with noon as the lyric’s example; history/song appropriation as Nia’s testimony rather than
      automatic proof of a literal diegetic choir; the logs’ limited exoneration without origin proof;
      her postwar loss-intake work; and “Go ahead.” with dialogue provenance when adapted or quoted.
      Do not silently convert first-person statements into objective omniscient facts or turn the noon
      example into a universal deadline.
    - Keep the *Case Zero* account compatible with `DEC-002`, `DEC-004`, and `DEC-007`: the arrival is
      a wanting/certainty rather than words, a voice, or an order; both origin accounts remain
      `unverified`; publication and lyric authority confirm no handshake causation; limited
      exoneration supplies no origin; and Nia’s usable self-trust supplies neither absolution nor
      archive validation. Record the binding same-speaker lyric account separately from `DEC-002`’s
      proper-name/person-specific-channel/bench-path mapping.
    - Keep *Case Zero* Production_Notes, style prompt, exclude list, generation workflow, credits, and
      rights metadata non-story/advisory unless separately ratified. Song occurrences of protected
      phrases remain outside Chapter_File Prose_Body scans unless a requirement explicitly changes
      that scope. Preserve the contradictory performance-copyright/public-domain footer only as an
      unresolved nonlegal author/rights-review follow-up; publication/canon status supplies no legal
      conclusion or replacement language.
    - Record as binding the title's governing premise: the final frontier was not outer space but
      humanity's own minds; people expected to cross it as explorers, but it crossed them and made
      human minds the shore and contested territory. The Mindwars are an event within this argument,
      not the title or whole meaning of the book.
    - Record `DEC-016` as binding architecture rather than prose mimicry: three active information
      threads through Chapters 1–112, followed by Safiya as a fourth Coda viewpoint that changes the
      moral scale; experiment/action/result/immediate-consequence exposition; stakes-changing capability
      escalation; fastest/tightest Mindwars threading; and deliberate post-112 deceleration. Record
      the explicit rejection of sender/adversary POV, culprit closure, exposition set pieces,
      spectacle Coda, group mind, global twenty-four-hour compression, and imitation of Dan Brown's
      or Douglas E. Richards's sentence-level prose, distinctive voice, phrasing, scenes, or
      characters.
    - Record every Binding_Canon_Fact with source/location, including December discovery; the
      stranger’s continuous ordinary morning received by Mara with an eight-second
      reception/transport offset observed only by Mara; April term-sheet arrival; page-nine
      `transmit enable`; the affected area canonically described as `three counties wide`; the
      visitor eleven miles from the array; two post-null years; Tuesday kettle; three unhurried
      knocks; the Mindwars term; the consent rule; the later arriving thought; the null’s successful
      silence, defensive cost, and civilian harm; Safiya’s maternal-language loss; her free consent;
      and the physics/truth basis of Mara’s refusal.
    - Encode the December source-side interval as continuous and the apparatus as receive-only with no
      transmit stage. Store the eight seconds only as Mara’s receive/transport offset, and record the
      person-specific channel/address identified in that receive event. Add a distinct later entry for
      the temporary bench transmit path and content-free handshake through the same address. Record
      page-nine `transmit enable` as evidence of broader architectural capability, never as evidence
      that the December rig transmitted.
    - Record the `DEC-002` proper-name and mechanism mapping: Nia is the *Case Zero* speaker, the
      December receive event identifies her person-specific address, and the later bench path uses
      that address. Keep this author-decision layer distinct from `DEC-014`’s binding same-speaker
      lyric testimony. The December receive event and later handshake/wanting event remain distinct in
      kind and time; record their causal linkage as a **separate** `unverified` entry with no reveal
      owner or release window. Tag all five `DEC-002` constraints, including that Nia’s emotional
      question resolves even though factual causation never does.
    - Record binding `DEC-007` without upgrading either origin account: Mara has high, mostly unvoiced
      private conviction that her later handshake caused the wanting; Nia refuses both unsupported
      accounts and eventually stops needing an origin to regain usable self-trust; Julian enters the
      adversary attribution professionally while privately knowing it is inference. Record that Nia’s
      movement supplies neither absolution nor archive validation.
    - Record `heritage_base: unspecified_by_author` under `DEC-003`. No Canon_Bible, Arc_Outline,
      Voice_Brief, chapter, or other project record may infer or invent real-world linguistic,
      geographic, religious, ethnic, or political particulars from Safiya’s name or the unspecified
      base. Preserve her public heritage language, occasional interpreting work, private-layer loss,
      wording ladder, community-portrayal review, and no-allegory guardrail.
    - Record Novel_Extensions for stable IDs, selected names, institutions, relationships, Safiya’s
      profession, and continuity-affecting dates, each with rationale, first dependency, affected
      records, and state. Under `DEC-005`, record `Northline Array`, `Open Channel Consortium`, and
      `Civic Record Trust` as the exact approved institutional names; record the country and every
      individual county as intentionally unnamed rather than unresolved placeholders.
    - Record the `DEC-005` contested-archive model as the in-world public state and distinguish it from
      `DEC-006`'s selected reader-facing presentation: one concise Front_Matter note plus rare,
      dramatically necessary in-story references, with no routine source notes, transcript apparatus,
      or heavy archival labeling. Official summaries and conditioned, provenance-preserving Trust
      releases compete publicly; witness embargo/release conditions remain enforceable; complete
      holdings are not presumed public; the Trust warrants provenance rather than truth; and no
      inquiry or release adjudicates the first-casualty attribution. Preserve the settled armistice
      facts and `DEC-002` constraint 3.
    - Define Timeline_IDs, including the continuous receive-only December source interval/offset and
      person-specific lock, the distinct later bench-transmit handshake, page nine as architectural
      capability rather than retroactive December evidence, April record alteration followed by Trust
      formation, composition-versus-deposit times for pre-Trust Discovery records, post-formation
      rolling deposits, post-null conditioned Trust releases competing with official summaries,
      shared null-night chronology, and Coda visit chronology. Store null extent as the canonical
      text, never as a derived radial measure or a list of named counties.
    - Maintain unresolved Foreign_Signal theories with `confirmed: false`; a Reveal Ledger with
      knowers, owner, release, basis, and payoff for role identity, bidirectionality, casualty
      consequence, counterphase transmission, affected-area extent, Safiya’s Tuesday loss, and
      unresolved provenance; and Canon_Dialogue provenance records.
    - _Requirements: 3.13, 4.11, 6.1–6.19, 14.1–14.14, 15.2, 15.3, 15.5–15.8_

  - [x] 4.3 Write `planning/pov-roster.md`
    - Define four human POVs with one-to-one mappings: `CHAR-001`/`POV-MARA`,
      `CHAR-002`/`POV-NIA`, `CHAR-003`/`POV-JULIAN`, and `CHAR-004`/`POV-SAFIYA`.
    - For each, record selected name/aliases, knowledge, moral pressure, plot function,
      relationships, blind spots, reason to narrate, and movement coverage. Mark Mara as Anchor_POV
      and record provisional loads: Mara 56, Nia 32, Julian 33, Safiya 7.
    - Reflect `DEC-002`: Nia holds both roles and the roster stays at four POVs. Preserve insertion
      (Nia) and subtraction (Safiya) as distinct human harms, and forbid any Foreign_Signal or
      alleged-sender POV. Carry `DEC-007` in the POV profiles: Mara’s high causal conviction is
      private and non-authoritative; Nia refuses both accounts and moves toward self-trust without
      absolution; Julian records an inference professionally without mistaking it for proof.
      Under `DEC-012`/`DEC-015`, every Pairing_Session remains supporting action or a deposited
      record inside one of the four existing POV chapters. Task 5 may select living pair identities
      and supporting participants, but the roster adds no sender, operative, adversary, archive,
      simulation, or group-mind POV and preserves the provisional 56/32/33/7 loads.
    - Link to `voice-briefs.md`.
    - _Requirements: 4.1–4.11, 9.8, 9.9, 14.10, 15.2, 15.3_

  - [x] 4.4 Write `planning/voice-briefs.md`
    - Create one qualitative brief per POV covering syntax/rhythm, image and sensory families,
      emotional distance, omission/evasion/delayed notice, Reverb_Profile, and movement evolution.
    - Preserve Mara’s cathedral-to-room-tone profile and chapter-124 Coda_Turn; Nia’s treated booth
      with damaged return feed; Julian’s hearing chamber; and Safiya’s near microphone in a domestic
      room. Carry `DEC-007` through movement evolution and characteristic evasion: Mara mostly leaves
      her high causal conviction unvoiced and centralizes herself when confessing; Nia refuses both
      accounts and eventually no longer needs provenance for usable self-trust; Julian’s professional
      attribution remains an inference he privately recognizes. Safiya’s brief must keep
      `heritage_base: unspecified_by_author` unfilled and forbid inferred real-world particulars.
      Carry `DEC-012`/`DEC-015` register discipline: Julian and institutional/public language carry
      most `ESP`/pairing usage, Mara uses the disputed term rarely and technically, and Nia resists
      the misnomer. Give each Voice_Brief distinct experiential language for passive `RECEIVE`,
      nonsemantic `INTRUDE`, and deliberate fluent `PAIR`; pairing may feel conversational but every
      contribution remains consciously sent and background mentation remains private. Carry
      `DEC-016` only as original craft behavior—information-bearing rotations, technical action tied
      to human consequence, fastest Mindwars threading, and Coda deceleration—without imitating Dan
      Brown's or Douglas E. Richards's sentence-level prose, distinctive voice, phrasing, scenes, or
      characters. Do not define sentence-length targets, resemblance scores, or style scores.
    - Add dated fields for calibration evidence and the Requirement 5.11 first-appearance review.
    - _Requirements: 5.1–5.9, 5.11, 5.13, 9.9, 14.1–14.4, 14.10, 15.5–15.8_

  - [x] 4.5 Write `planning/motif-ledger.md` with the resolved event mapping
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

  - [x] 4.6 Create `planning/editorial-log.md` and `planning/arc-changes.md`
    - In `editorial-log.md`, define evidence-bearing `EditorialFinding` and `GateResult` records with
      scope, chapter/batch, criterion, prose location, result, rationale, action, reviewer, and
      resolution. Never store numeric craft scores.
    - In `arc-changes.md`, define prior/revised state, rationale, affected chapters/documents,
      synchronization obligations, approval, and completion. A post-baseline change remains invalid
      until every listed reference is synchronized.
    - _Requirements: 1.16–1.18, 10.7, 10.8, 13.5–13.10_

- [x] 5. Write the complete 128-entry Provisional Arc Outline
  - [x] 5.1 Create `planning/arc-outline.md` structure and global invariants
    - Create one ArcEntry per chapter with global sequence, filename, movement, Timeline_ID, POV_ID,
      one-sentence purpose, nonblank hook, reciprocal cross-cuts or `none`, estimated Length_Class,
      outlier purpose where applicable, status, calibration flag/purpose, record horizon, and reveal
      IDs.
    - Record the provisional 128-chapter/140,000-word allocation: 29 Discovery, 32 Private Defense,
      51 Mindwars, 16 Coda. Record at least 108 normal chapters, at most 20 purposeful outliers, no
      chapter over 2,500 words, and a placeholder for author-approved Final_Targets. Record the
      `DEC-016` same-POV run limit of at most three chapters and at most 3,600 combined estimated
      Prose_Words, and record `estimated_words` for every entry in a run of two or more chapters.
    - Record the `DEC-016` original-thriller controls: varied information/decision/reversal/arrival/
      danger/moral-remainder hooks with no more than two adjacent question-gap hooks; technical beats
      staged as experiment → action → result → immediate human or institutional consequence;
      chronology-supported compressed-clock clusters rather than whole-book twenty-four-hour
      compression; fastest/tightest Mindwars threading; and deliberate post-112 deceleration. Record
      these as human Editorial_Gates, never automated prose or resemblance scores.
    - _Requirements: 1.2–1.5, 2.1, 2.7, 2.10–2.12, 3.1, 3.6, 15.5–15.8_

  - [x] 5.2 Write Discovery_Part entries, chapters 1–29
    - Expand the six design clusters: 1–5 noise floor; 6–10 a stranger’s morning; 11–15 the field;
      16–20 open invitation; 21–25 case zero refuses the name; 26–29 the door runs inward.
    - Preserve a continuous source-side morning and assign the eight-second reception/transport
      offset only to Mara’s receive-only December observation. The December apparatus has no transmit
      stage; it identifies and locks Nia’s person-specific channel/address. Chapters 16–20 separately
      add the temporary bench transmit path and later handshake/wanting event. Under
      `DEC-012`/`DEC-015`, no Discovery POV uses `ESP` or `Electronic Speech Pairings` as an
      established term, and no later historical back-label implies that December transmitted.
    - Apply `DEC-002`: Nia holds both roles. Entries may fix the shared identity, but no entry may
      resolve whether Mara’s later handshake caused the wanting—that question has no reveal owner or
      release window. Apply `DEC-007`: Mara’s high private conviction remains non-authoritative, Nia
      refuses both origin accounts and rejects appropriation without absolution, and Julian treats the
      professional adversary attribution as inference. Keep the Mara 14/Nia 9/Julian 6 load and
      chapter count unchanged.
    - Record `MOT-CHAIN-01` and `MOT-COME-01`, fair reveal horizons, and no causal promotion of the
      handshake or any sender theory.
    - _Requirements: 1.4–1.7, 3.2, 3.13, 6.3, 6.6, 6.7, 14.2_

  - [x] 5.3 Write Private_Defense_Part entries, chapters 30–61
    - Expand clusters 30–35 copper and quiet; 36–42 benevolent offer; 43–49 April/page nine; 50–55
      put it in the record; 56–61 handle inside, with Mara 14/Nia 8/Julian 10.
    - Place `MOT-COPPER-01`, `MOT-CHAIN-02`, `MOT-RECORD-01`, `MOT-COME-02`, and
      `MOT-KNOCK-01` according to the ledger.
    - `Electronic Speech Pairings` may be coined here at the earliest through Julian or
      institutional/public language; keep the term a disputed simplification, rare in Mara's
      technical speech and resisted by Nia. In Chapters 36–42, select living pair identities inside
      the existing POV architecture, dramatize legitimate medical, linguistic, and emergency benefit,
      begin Pair_Calibration, and establish why participants freely choose the technology. In Chapters
      56–61, place the first sustained Fluent_Pairing conversation on page: each contribution has a
      Deliberate_Send_Act; pause/revocation stops transport; a clipping, latency, or integrity failure
      triggers confirmation, retry, or ordinary-speech fallback; and one consent-protocol failure is
      followed by repair. Record mandatory Consent_State_Metadata and Transport_Metadata, initialize
      Content_Recording off, and create a Pairing_Transcript only if separate explicit mutual recording
      consent is part of the selected scene. Preserve the Mara 14/Nia 8/Julian 10 movement load and
      add no operative or sender POV.
    - Place Trust formation only after Julian observes alteration of the April negotiation record.
      Treat Discovery logs/voice memoranda as pre-Trust contemporaneous sources later deposited;
      begin rolling Trust witness deposits only after formation. Under `DEC-007`, Julian may enter the
      adversary attribution professionally only while the ArcEntry preserves his private knowledge
      that it is inference, and Nia must still refuse both origin accounts.
    - _Requirements: 1.4–1.7, 3.3, 6.3, 6.14, 7.9–7.11, 14.10–14.12, 15.1–15.3, 15.6_

  - [x] 5.4 Write Mindwars_Part entries, chapters 62–112
    - Expand clusters 62–69 no first shot; 70–77 mirror; 78–85 shield; 86–93 territory; 94–101
      affected area in the model; 102–108 null night; 109–112 history of quiet, with Mara 21/Nia
      14/Julian 16 and the movement longest by words. Under `DEC-016`, give Mindwars the Manuscript's
      fastest chapter turnover and tightest converging-thread pattern; stage technical disclosures as
      experiment → action → result → immediate human or institutional consequence, with each
      capability escalation changing consent, relationship, evidence, power, or bodily risk.
    - Make Chapters 86–93 earn the title's binding reversal from `DEC-011`: inherited maps point out
      toward space, but the human mind proves to be the frontier, people the shore and territory, and
      humanity the crossed rather than the crosser. Treat the Mindwars as the event that reveals this,
      not as an alternate title or the book's whole meaning.
    - Apply `DEC-012`/`DEC-015`: use `ESP`/Electronic Speech Pairings only as a late contested
      institutional term and keep `RECEIVE`, `INTRUDE`, and `PAIR` non-overlapping. Chapters 70–77
      use fluent `PAIR` under counterphase pressure while Chapter 73 tests current local consent and
      Nia's authority. Chapters 78–93 make operational Fluent_Pairing a principal thriller engine;
      assign every session to Mara, Nia, or Julian's existing chapters, with supporting participants
      or deposited records where needed, and reveal only Consent_State_Metadata/Transport_Metadata
      traffic patterns rather than unrecorded meaning. Chapters 94–108 escalate two-person pairing
      into ethical and infrastructural risk without group mind, hive mind, mass mind reading,
      transferred calibration, or provenance proof. Chapters 109–112 preserve Nia's usable-self-trust
      resolution and the contested public record without using fluent communication to settle either
      origin account. Every semantic contribution remains deliberately sent; unoffered mentation stays
      private; recording remains separately mutual and off by default; transcripts prove only recorded
      protocol-carried content; and no fifth, sender, operative, adversary, archive, or simulation POV
      is added. Pairing remains unable to reconstruct Safiya's corpus-less private layer.
    - Keep all null-night entries on one Timeline_ID with reciprocal non-redundant Cross_Cuts. No POV
      enters Safiya’s home.
    - Place `MOT-YES-01` in 73, `MOT-COME-03`, `MOT-COPPER-02`, `MOT-RADIUS-01`, and
      `MOT-RECORD-02`. Treat counterphase as chain context only, not `MOT-CHAIN-04` or another event
      absent a documented ArcChange.
    - Apply `DEC-017`. Because the bounded Chapter 73 test and null night are the same `CANCEL`
      operation at two scopes, give Chapter 73 a concrete physical vocabulary for a cancellation field
      experienced from inside — a specific sensation, sound, or bodily register — that Chapter 118 can
      reuse without narration. Chapter 73 is where the authorization question is asked and answered.
      No ArcEntry purpose or hook in 62–112 may have Mara, Nia, or Julian state the parallel between
      that consented bounded cancellation and the later unconsentable area-scale null; the silence runs
      through Chapter 123 and is characterization, not withheld information. Add no Motif_Event ID, no
      Literal_Phrase_Constraint, and no Reveal record for the parallel.
    - Use `affected area canonically described as three counties wide` for null extent. Never derive
      a geometric radius, substitute named counties, or name the country or any individual county.
      Confine active defender counterphase and rhetorical collective declaration to Mindwars.
    - In 109–112 complete `DEC-007`’s emotional movement: Nia stops needing the wanting’s origin and
      regains usable self-trust without deciding causation, forgiving Mara, or validating Julian’s
      archive; both origin accounts remain `unverified`. Apply `DEC-005`: official summaries and
      conditioned, provenance-preserving Trust releases begin their public contest without a unified
      inquiry, complete-holdings disclosure, or correction of the first-casualty attribution.
    - _Requirements: 1.4–1.7, 3.4, 3.7, 3.9, 3.10, 6.4, 8.7, 14.1–14.14, 15.1–15.8_

  - [x] 5.5 Write Aftermath_Coda entries, chapters 113–128
    - Follow the chapter-level design: public intake/request inside `DEC-005`’s contested archive,
      including an ongoing conditioned Trust release that competes with official summaries without
      opening complete holdings; Safiya’s approach; one three-knock event seen from both sides;
      Safiya’s Tuesday account and exact loss; Mara receiving the affected area as people; valid
      consent; truth-based refusal; relay off/second kettle; dry human presence, staying, ordinary
      voice through air, entry against Mara, and outward threshold obligation. Preserve
      `heritage_base: unspecified_by_author` everywhere and infer no real-world particulars from
      Safiya’s name or the unspecified base.
    - Apply `DEC-015`/`DEC-016` after Chapter 112: make the neural channel recede and decelerate the
      Coda through disclosure, arrival, refusal, emotional choice, and moral remainder. Pairing,
      Pairing_Transcripts, archives, simulations, models, and reconstructions cannot supply Safiya's
      dead second participant or missing corpus and cannot turn her Chapter-124 request into truthful
      restoration. Let ordinary spoken voice, listening, presence, and refusal carry the ending.
    - Keep the Coda shortest; no Foreign_Signal return, counterphase, renewed combat, campaign, or
      adversary proof.
    - Place `MOT-KNOCK-02` across 116–117, `MOT-KETTLE-01` and calibration selection in 118,
      `MOT-RADIUS-02` in 120, `MOT-COME-04`/`MOT-KETTLE-02` and calibration selection in 124,
      `MOT-CHAIN-03` in 127, and `MOT-RECORD-03`/`MOT-KNOCK-03`/`MOT-WHOSE-01` in 128.
    - Apply `DEC-017`. Chapter 118 reuses the Chapter 73 cancellation-field vocabulary with no
      authorization question anywhere near it; the absence of the question is the echo, and Safiya
      neither knows about Chapter 73 nor supplies the link. Keep the parallel unnamed through Chapter
      123. In Chapter 128, inside the existing `MOT-RECORD-03` entry against herself, Mara names it
      exactly once: the protocol she was held to was one room wide, and she then ran the same mechanism
      across an area canonically described as three counties wide with no one to ask. That is the only
      explicit statement permitted anywhere in the manuscript. It stays dry self-indictment and
      resolves no provenance, absolves nothing, validates no archive, and does not reinterpret Safiya's
      consent. Create no new Motif_Event ID, Literal_Phrase_Constraint, or Reveal record for it.
    - _Requirements: 1.4–1.7, 3.5, 3.11–3.13, 7.8–7.13, 8.2–8.6, 14.13, 14.14, 15.6_

  - [x] 5.6 Audit Cross_Cut reciprocity, reveal links, record horizons, and chronology
    - Require a reciprocal target, shared timeline/consequence/disclosure, distinct
      Material_Narrative_Value, and replay boundary for each Cross_Cut; use `none` otherwise.
    - Verify December source continuity, Mara-only offset, and an explicitly receive-only apparatus
      with no transmit stage; the person-specific address lock; the distinct later bench-transmit
      handshake/wanting event; page nine as broader capability rather than proof of December
      transmission; Nia holding both roles per `DEC-002` with causation unresolved; the full
      `DEC-007` belief distribution and Nia’s eventual release from needing provenance; April
      alteration before Trust formation; pre-Trust composition before later deposit;
      post-formation-only rolling deposits; the exact `DEC-005` institutional names; intentionally
      unnamed country/counties; conditioned public Trust releases competing with official summaries
      without adjudication or complete-holdings disclosure; canonical null extent wording; exactly one
      `RECEIVE`/`INTRUDE`/`PAIR` mode per neural event; valid living participants, current consent,
      pair-specific calibration, Deliberate_Send_Acts, pause/revocation, and failure recovery for every
      Pairing_Session; mandatory consent/transport metadata; separately mutual default-off recording;
      transcript claims limited to recorded protocol-carried content; mandatory Fluent_Pairing beat
      coverage in 36–42, 56–61, 70–77, 78–93, and 94–108; the existing four POVs and 56/32/33/7
      loads; and the `DEC-012`/`DEC-015` chronology in which `ESP` is coined only after Discovery and
      no backward label creates December transmission, articulate unconsented speech, semantic
      metadata reconstruction, or provenance closure. Verify every same-POV run against both
      `DEC-016` limits, at most three chapters and at most 3,600 combined estimated Prose_Words, and
      confirm that each entry in a multi-chapter run carries a non-null `estimated_words`.
    - Resolve every reveal ID and prevent any purpose/hook from using knowledge beyond its
      narrator’s record horizon.
    - _Requirements: 1.6, 1.7, 4.12, 6.2, 6.7, 12.5, 14.1–14.14, 15.1–15.3, 15.5_

  - [x] 5.7 Mark the eight-chapter Calibration_Batch
    - Mark chapters **1–5, 73, 118, and 124** as `calibration_selected`.
    - Record representative purposes: 73 tests counterphase consent, Mindwars tone, and Nia’s ability
      to exercise authority without resolved provenance (`DEC-007`); 118 tests Safiya’s own voice,
      concrete loss, first kettle event, describe-never-quote handling, and the
      `unspecified_by_author` guardrail; 124 tests Mara’s response, truth-based refusal, Coda_Turn,
      and Refused_Swell.
    - Mark 73, 118, and 124 `exploratory` until their surrounding final-continuity batches reconcile
      them. Julian is absent; record that his first later Discovery appearance requires the
      Requirement 5.11 Editorial_Gate before that batch can be approved.
    - _Requirements: 1.8–1.10, 5.11, 13.1_

  - [x] 5.8 Verify the complete provisional plan
    - Verify unique contiguous sequence `1..128`, one entry per planned file, no POV run over three
      chapters or 3,600 combined estimated Prose_Words,
      four contiguous movements in order, Anchor coverage, exact provisional POV loads, normal/outlier
      budget, all direct IDs, motif mappings, reciprocal Cross_Cuts, every required Fluent_Pairing
      range, Pairing_Session-to-existing-POV references, fastest/tightest Mindwars threading, and
      deliberate post-112 deceleration.
    - Confirm tasks 1.2, 1.3, 1.4, 1.5, and 1.7 are resolved and mirrored before declaring the
      Provisional_Arc complete.
    - _Requirements: 1.1–1.5, 2.7, 2.8, 4.9, 11.4, 14.1, 15.1–15.3, 15.5, 15.6_

- [x] 6. Checkpoint — planning and site isolation complete **[HARD GATE]**
  - Ensure all planning checks and the site-isolation test pass; confirm every arc ID resolves and
    the complete Provisional_Arc contains no prose.
  - Tasks 1.2, 1.3, 1.4, 1.5, and 1.7 are resolved (`DEC-002`, `DEC-003`, `DEC-004`, `DEC-005`,
    `DEC-007`). Do not begin any Prose_Body until tasks 4–5 are complete and mirror each resolved
    decision.

- [x] 7. Implement and test the minimal calibration checker
  - The minimal checker is `.tools/check_novel.py`, read-only and fail-closed. It enables safe
    exploratory calibration; it does not need global totals or the full property suite yet.

  - [x] 7.1 Set up Python test dependencies and calibration test layout
    - The repository currently has no suitable novel-checker dependency manifest. At this task—and
      not earlier—create `.tools/requirements-novel-dev.txt` with concrete exact versions selected
      at implementation time in the form `pytest==X.Y.Z` and `hypothesis==A.B.C`; no ranges or
      compatible-release specifiers.
    - Install those pinned dependencies only while executing this task. Create `.tools/tests/`, a
      shared fixture module, focused minimal-checker tests, and reserved modules for one principal
      test per Property 1–15.
    - _Requirements: 12.1, 12.14, 12.15_

  - [x] 7.2 Implement Chapter_File parsing, word counting, and Length_Class validation
    - Parse the header delimiters and exactly one required key each; fail safely when the prose
      boundary is ambiguous. Count whitespace-separated Prose_Words after the header only.
    - Validate filename/directory/header/ArcEntry movement and global sequence agreement; derive
      `microchapter` below 700, `normal` 700–1,600 inclusive, `long-outlier` 1,601–2,500 inclusive;
      reject above 2,500 and require planned purpose for outliers.
    - _Requirements: 2.8–2.11, 9.5–9.7, 12.1–12.3_

  - [x] 7.3 Implement direct-reference parsing and calibration-scope integrity
    - Parse fenced ArcEntry, Timeline_ID, POV_ID/Character_ID, VoiceBrief, and MotifEvent records
      needed by each calibration chapter, including each Timeline_ID's `technical_state` object with
      its `mode`, `cancel_state`, `pair_state`, and `pairing_evidence` fields. Mechanism and pairing
      state are fields of `TimelineEntry`, not separate record types.
      Report malformed, missing, duplicate, dangling, many-to-one, and disagreeing direct references
      without inferring mechanism state or semantic content from prose commentary. For chapter 73,
      validate only the objective `CANCEL` bounded-consent state and `PAIR` metadata and references;
      the checker does not judge whether the fluent scene or consent conflict succeeds dramatically.
    - Enforce local filename/header/outline agreement and only those Cross_Cut references whose
      requested batch scope contains the participating changed records.
    - _Requirements: 10.1–10.5, 12.4, 12.5, 14.1, 14.3–14.12_

  - [x] 7.4 Implement calibration-scope motif and literal checks
    - Enforce ledger/header assignment for the selected chapter/batch scope, including
      `MOT-YES-01` in 73, `MOT-KETTLE-01` in 118, and `MOT-COME-04`/`MOT-KETTLE-02` in 124.
    - Scan Prose_Bodies only. Normalize Unicode NFC and line endings while preserving exact case,
      order, and punctuation. Reject `Did I say yes?` outside Mindwars; do not impose an in-scope
      count. Do not guess a Final_Passage not yet in scope.
    - Enforce the resolved chain/copper mappings for any direct records encountered.
    - _Requirements: 7.2, 7.3, 7.7, 7.12, 7.14, 7.15, 12.6_

  - [x] 7.5 Implement chapter and batch modes with changed-reference consistency
    - Add `--scope chapter --chapter <path>` and `--scope batch --chapters <paths...>` plus changed
      reference inputs. Chapter mode reads only Direct_Planning_References; batch mode reports both
      chapter violations and stale changed references.
    - Accept the eight calibration files as a special pre-baseline batch while retaining the normal
      4–8 size rule for post-baseline Drafting_Batches.
    - _Requirements: 10.1–10.5, 10.9, 13.3_

  - [x] 7.6 Implement deterministic diagnostics, output, and exit behavior
    - Emit stable diagnostics with severity, code, scope, path/ID, observed, and expected fields;
      support text and JSON; exit `0` only for complete readable zero-violation scope, `1` for
      objective violations, and `2` for missing/malformed/incomplete input.
    - Keep the diagnostic allowlist free of voice, originality, pace, hook quality, tenderness,
      restraint, rhetorical force, and emotional-truth judgments.
    - _Requirements: 12.9–12.15_

  - [x] 7.7 Write the focused minimal-checker tests
    - Test required/duplicate/malformed headers; filename/header agreement; empty/Unicode/CRLF word
      counting; 699/700/1,600/1,601/2,500/2,501 boundaries; direct valid/dangling IDs; selected
      motif/literal rules; changed-reference drift; deterministic text/JSON diagnostics; and exits
      0/1/2.
    - Add timeline fixtures proving a continuous source interval with an eight-second offset only on
      Mara's `RECEIVE` record, an explicitly receive-only December apparatus with no transmit stage,
      a distinct later `INTRUDE` bench handshake over the locked person-specific address, and page
      nine as broader capability rather than December evidence; also prove Trust formation after
      record alteration, with pre-Trust composition and later deposit timestamps.
    - Add structured `DEC-015` cases for exactly-one mode; the consent/calibration truth table;
      two-living-participant and pair-specific calibration constraints; Deliberate_Send_Act coverage;
      immediate stop after pause/revocation; explicit recovery after clipping/latency/integrity
      failure; mandatory consent/transport metadata; default-off independently mutual recording;
      transcripts limited to transported session content; semantically opaque metadata; and
      unconfirmed Nia/Foreign_Signal provenance. Include dead, absent, replacement, simulation,
      archive, model, and reconstruction participants as rejected cases. Use synthetic records only.
    - _Requirements: 6.2, 9.6, 9.7, 10.1–10.5, 12.1–12.6, 12.9–12.15, 14.1–14.14_

  - [x] 7.8 Pass the minimal calibration-readiness gate **[HARD GATE]**
    - Run the minimal focused suite and a synthetic chapter/batch smoke test. Record a
      `calibration-objective` GateResult proving site isolation, complete provisional planning,
      headers, filenames, counts/classes, direct IDs, calibration motif/literal rules,
      changed-reference consistency, diagnostics, and exit behavior are ready.
    - This gate unlocks exploratory calibration only; it does not claim global acceptance.
    - _Requirements: 1.10, 10.1–10.5, 13.1_

- [ ] 8. Draft exploratory calibration while completing the full checker and mandatory suite
  - After task 7.8, the prose track (8.1–8.7) and full-checker track (8.8–8.27) proceed in parallel.
    Exploratory prose is not blocked on global mode or all property tests. Baseline approval is.

  - [x] 8.1 Draft calibration chapters 1–3 **[EXPLORATORY]**
    - Chapter 1 `POV-MARA`: December noise-floor structure. Chapter 2 `POV-NIA`: she lives the fully
      continuous ordinary morning with no experienced timing anomaly, and is the source per
      `DEC-002`. Chapter 3 `POV-MARA`: verification fails once, then she receives experience rather
      than a message and measures the eight-second reception/transport offset.
    - Use a sensory-match Cross_Cut and preserve `DEC-002` reveal ownership. The December apparatus
      is receive-only and has no transmit stage; do not hint otherwise. The causal question begins
      only after Mara deliberately adds the later bench transmit path in Chapters 16–20.
    - _Requirements: 2.4–2.6, 2.12, 3.2, 6.3, 9.6, 9.7_

  - [x] 8.2 Draft calibration chapters 4–5 **[EXPLORATORY]**
    - Chapter 4 `POV-NIA` returns to her continuous morning and adds lived ordinary detail without
      retroactively inserting a gap. Chapter 5 returns to Mara as she confirms the reception timing,
      fails one alternative explanation, and recognizes that the structure tracks living attention.
    - Keep the later self-authored-feeling wanting outside this opening receive event and withhold the
      Nia identity conclusion until the `DEC-002` reveal horizon earns it.
    - _Requirements: 2.4–2.6, 3.2, 6.2, 6.9_

  - [x] 8.3 Draft calibration chapter 73 **[EXPLORATORY]**
    - `POV-NIA`, in the first counterphase-consent sequence. Use the exact protected question
      `Did I say yes?` and force consent to be specific, current, revocable, and local; Nia answers
      aloud in the room and never gives consent over a channel. Stage the chapter’s own Fluent_Pairing
      beat through an existing POV: she and Mara coordinate the conditions she sets over their
      consented paired channel, each contribution is deliberately sent, unoffered mentation remains
      private, and pause or revocation stops semantic transport at once.
    - The planning records now carry the state this chapter dramatizes, so consume it rather than
      invent it. `TL-MINDWARS-COUNTERPHASE` holds the bounded-local `CANCEL` state with Nia’s current
      revocable individual consent, and `TL-PAIR-MARA-NIA-COUNTERPHASE` holds the `PAIR` state across
      73–75 with `PAIR-CAL-MARA-NIA`, two living participants, `deliberate_send_state: required`,
      mandatory semantically opaque consent/transport metadata, `content_recording_enabled: false`,
      and a null transcript. Keep the two modes separate on the page: the channel coordinates the
      field and never carries it, no metadata is readable as content, and Nia reports her concrete
      gap in access aloud rather than through the channel.
    - Test Nia’s authorization register, Mara’s technical context, Mindwars tonal expansion, and the
      `DEC-007` movement toward exercising judgment without resolved provenance; end on decision lock
      or moral remainder rather than another question gap. Do not turn that movement into absolution
      or archive validation.
    - Apply `DEC-017`. Establish the concrete physical vocabulary for a cancellation field experienced
      from inside — a specific sensation, sound, or bodily register — that Chapter 118 will reuse. This
      chapter is half of a delayed disclosure, so it is also a primary calibration test of whether that
      vocabulary is distinctive enough to be recognized forty-five chapters later without narration. No
      character may state the parallel between this consented bounded cancellation and the later
      area-scale null; Mara in particular does not, because saying it here would convert the scene into
      the consent lecture this task already forbids.
    - _Requirements: 1.9, 3.4, 5.10, 7.14, 7.15, 14.5, 14.6, 14.9, 14.10, 14.12, 15.6_

  - [x] 8.4 Draft calibration chapter 118 **[EXPLORATORY] [HARD GATE]**
    - `POV-SAFIYA`. Give Safiya ownership of her Tuesday account: kettle on, eleven miles from the
      array, no foreign arrival, and the concrete maternal-language access she lost during the null.
      Assign `MOT-KETTLE-01`.
    - Test Safiya’s dry close voice, exact human loss, agency, and refusal to become an emblem. Apply
      `DEC-003`: use describe-never-quote as the default register; preserve
      `heritage_base: unspecified_by_author` in every planning and drafting record; infer or invent no
      real-world linguistic, geographic, religious, ethnic, or political particulars from Safiya’s
      name or the unspecified base; quote no real-language wording; and perform no aphasia. Invented
      private-layer words are permitted sparingly—the absence carries more than a glossary would.
      This chapter is the main test of whether describe-never-quote is sufficient.
    - Apply `DEC-017`. Reuse the Chapter 73 cancellation-field vocabulary so a reader can assemble the
      consent parallel unaided, and keep every authorization question away from this account — the
      absence of the question is the echo. Safiya does not know about Chapter 73, no narrator supplies
      the link, and the parallel stays unnamed until Chapter 128. Because 73 and 118 are both
      calibration chapters, this pairing is directly testable now: the review asks whether the shared
      register is recognizable without being underlined.
    - _Requirements: 1.9, 5.10, 6.4, 6.11, 7.12, 8.1_

  - [x] 8.5 Draft calibration chapter 124 **[EXPLORATORY]**
    - `POV-MARA`. Affirm Safiya’s consent as genuine, then have Mara refuse because she lacks the
      living second participant, mother/source truth, and corpus required for truthful transport or
      reconstruction; Pair_Calibration cannot connect Safiya to the dead, an archive, simulation,
      model, or generated proxy, and any construction could falsely self-authenticate as memory.
      Switch the relay off before putting on the second kettle.
    - Assign `MOT-COME-04` and `MOT-KETTLE-02`; execute the Coda_Turn from cathedral-scale
      explanation to dry human presence. Do not turn the refusal into a lecture on consent.
    - _Requirements: 1.9, 5.9, 6.11–6.13, 7.8, 7.12, 8.6, 14.8, 14.11, 14.13_

  - [x] 8.6 Run the minimal checker over all eight calibration chapters
    - Run chapter scope for 1–5, 73, 118, and 124, then batch scope with every changed direct
      reference. Resolve all objective violations before editorial review while keeping
      representative chapters `exploratory`.
    - _Requirements: 10.1–10.5, 13.3_

  - [x] 8.7 Record the Calibration_Batch Editorial_Review **[EDITORIAL]**
    - Cite representative prose and record `pass`/`revision` for Mara, Nia, and Safiya Voice_Brief
      fidelity/separation; opening momentum; the clear fact that the source morning is continuous,
      the offset belongs only to Mara’s receive-only December apparatus, and that apparatus has no
      transmit stage; Cross_Cut clarity; hook variety; pacing; testimony immediacy; Safiya’s
      materially specific loss without any inferred real-world particulars under `DEC-003`; Nia’s
      Chapter-73 ability to exercise authority without resolved provenance, absolution, or archive
      validation under `DEC-007`; Chapter 73's Fluent_Pairing clarity under `DEC-015`, including
      deliberate send, local revocability, private unoffered mentation, failure handling, and
      semantically opaque metadata; Safiya’s ownership of loss; Mara’s truth-based refusal and
      Coda_Turn; tenderness, restraint, human cost, emotional truth, Refused_Swell, and absence of
      recognizable imitation or technical exposition detached from immediate human consequence.
    - Under `DEC-017`, record `pass`/`revision` on the delayed consent disclosure using the 73/118
      pairing this batch uniquely makes testable: whether the two chapters share a concrete
      cancellation-field vocabulary distinctive enough for a reader to assemble the parallel unaided,
      whether Chapter 118 keeps every authorization question away from the account so the absence reads
      as echo rather than oversight, and whether both chapters stay clear of naming the parallel. Flag
      as `revision` any prose in which a character states or gestures at the connection, or in which
      the shared register is so underlined that it functions as narration.
    - Julian is absent. Record the unresolved Requirement 5.11 first-appearance gate for the first
      later Discovery batch containing him.
    - _Requirements: 1.11, 2.13, 5.10, 5.11, 8.9, 13.4, 14.10, 14.12, 15.6, 15.7_

  - [x] 8.8 Expand `.tools/check_novel.py` to the complete objective checker
    - Add full planning parsing/referential integrity, Cross_Cut symmetry, POV run cap in both chapters
      and combined run words, roster/Anchor
      checks, Chapter_Local/Batch/Global scope separation, outline/file bijection, four ordered
      movement blocks, Final_Target totals, normal share, movement word relationships, full motif
      synchronization, all literal constraints including declared Final_Passage bounds, ArcChange
      atomicity, status demotion/synchronization, finalization requiring both gates, and
      `--site-exclusion` exercising generated-index isolation.
    - Validate CanonFact authority under `DEC-011` and `DEC-014`: allow only `author-decision`,
      `requirement`, `lyric`, and `ratified-note`; require an adopting requirement/decision for
      `ratified-note`; require speaker/limitation metadata for first-person lyric testimony; accept
      `lyric` sources only from the exact five Canon_Source paths; reject *One-Time Pad* as a canon
      source; and reject unratified Production_Notes or other non-lyric metadata represented as a
      Binding_Canon_Fact.
    - Validate the structured `DEC-012`/`DEC-015` state without inferring mechanism or meaning from
      prose: late contested ESP terminology; exactly one `RECEIVE`/`INTRUDE`/`CANCEL`/`PAIR` mode per
      event, read from `TimelineEntry.technical_state.mode` and never inferred from `apparatus_mode` or
      commentary; receive-only December; nonsemantic addressed unconsented writes; and two-living-person
      `PAIR` with current
      specific revocable mutual consent, matching pair-specific calibration, Deliberate_Send_Acts,
      immediate pause/revocation, and explicit failure recovery. Validate mandatory consent/transport
      metadata, default-off separately mutual Content_Recording, transcript subset/session identity,
      semantic opacity and evidentiary scope, nontransferable calibration, prohibited nonliving or
      substituted participants, unconfirmed Nia/Foreign_Signal provenance, Fluent_Pairing coverage in
      all required ranges, existing-POV session ownership, and unchanged 56/32/33/7 loads.
    - Validate every `CANCEL` record's `cancel_state`: absent person-specific address, subtraction-only
      effect with `inserted_content` of `none`, all three untargetability flags false, absent additive
      inverse, `provenance_yield` of `none`, chapters inside the Mindwars block, individual current
      specific revocable consent for `bounded-local` scope, and institutional authorization only
      for `area-scale` scope. Reject an addressed or insertive `CANCEL`, a declared reversal, an
      enumerated affected set, area-scale consent claimed from every affected person, a non-Mindwars
      chapter, provenance derived from cancelling a pattern, and any attempt to classify the null as
      `INTRUDE`.
    - Validate the structured `DEC-014` state without scanning song prose: exactly five Canon_Sources
      resolve to the required paths; *Case Zero* lyric is binding attributed testimony with
      author-approved publication in progress; *One-Time Pad* is excluded; and *Case Zero*
      production/style/generation/credits/rights material remains non-story/advisory. Keep all
      Canon_Source song occurrences outside Chapter_File literal scope, preserve both origin accounts
      as `unverified`, and treat the contradictory footer as a nonlegal follow-up field rather than a
      legal diagnostic. `DEC-013` is superseded history, not a valid current-state fixture.
    - Enforce the resolved `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` mappings, canonical
      affected-area wording in structured canon records, receive-only December continuity and offset,
      the distinct later bench-transmit handshake, page nine as broader capability rather than
      December evidence, `heritage_base: unspecified_by_author` without inferred real-world
      particulars, the unresolved `DEC-007` accounts/distribution, Trust formation/deposit
      chronology, and structured `DEC-005` decision/reference state for approved institutions,
      intentionally unnamed country/counties, and a conditioned public Trust counter-record that
      competes with official summaries without claiming complete holdings or adjudicating
      attribution. Treat missing or dangling decision/entity references as metadata errors, but keep
      name wording and capitalization outside automated pass/fail under Requirement 12.11.
    - _Requirements: 1.6–1.18, 2.7–2.11, 4.1–4.10, 6.1–6.19, 7.1–7.18, 10.1–10.9, 11.1–11.11, 12.1–12.15, 14.1–14.14, 15.1–15.5_

  - [x] 8.9 Build shared generated fixtures for the complete suite
    - Create reusable Hypothesis strategies and synthetic workspace builders for headers, bodies,
      ArcEntries, identifiers, Cross_Cuts, role-decision states, chronology, motif ledgers,
      movement allocations, status changes, gates, and source trees.
    - Include the `DEC-002` proper-name/person-specific-address/bench-path mapping plus the separate
      `DEC-014` same-speaker lyric testimony. Malformed states must include collapsing the entire
      mechanism into a lyric fact, omitting or demoting the *Case Zero* testimony, a causal-linkage
      record with a reveal owner/release window, any December transmit stage/event, or page nine
      treated as proof of December transmission. Include the valid receive-only December interval and
      person-specific lock plus the distinct later bench path/handshake. Include `DEC-007` records
      that preserve Mara’s high non-authoritative belief, Nia’s refusal/release movement, Julian’s
      professional inference, and both accounts as `unverified`. Include `heritage_base: unspecified_by_author` plus malformed fixtures that fill
      the base or infer real-world particulars. Also include every valid CanonFact authority basis;
      ratified notes with adoption references; rejected unratified-note facts; the inward-frontier
      premise as lyric-authority canon; exact canonical affected-area text; post-alteration Trust
      formation; later deposit of pre-Trust sources; and post-formation rolling deposits. Include the
      valid `DEC-005` state with the three selected institutions, intentionally unnamed geography, and
      conditioned public Trust releases competing with official summaries. Include malformed states
      with missing/dangling decision or entity references, contradictory geography state, complete-
      holdings adjudication, a hidden-only/one-time release model, or provenance treated as truth.
      Include name/capitalization variants that preserve stable IDs as nonviolations under Requirement
      12.11.
    - Include valid `DEC-012`/`DEC-015` records plus malformed pre-Discovery coinage,
      December-transmission, collapsed-mode, semantic-`INTRUDE`, and arbitrary-memory-reading states.
      Generate the consent/calibration truth table; living/nonliving and replacement participant
      identities; deliberately sent and unoffered content; pause/revocation event streams; clipping,
      latency, and integrity failures with and without explicit recovery; mandatory/missing
      consent-state and transport metadata; independent recording-consent combinations; transcript
      subset and cross-session violations; semantic metadata claims; provenance confirmations;
      required fluent-range coverage; Pairing_Sessions in valid existing POV chapters and prohibited
      sender/operative/adversary/archive/simulation/group-mind POVs; and exact versus changed
      56/32/33/7 load vectors. Include valid `DEC-014` records with the exact five paths,
      author-approved/in-progress *Case Zero* publication, binding attributed lyric facts, advisory
      non-lyric metadata, Chapter_File-only phrase scans, and the rights-footer conflict as unresolved
      follow-up metadata. Include malformed states with a missing *Case Zero*, an added *One-Time Pad*,
      *Case Zero* lyric marked advisory, production/style/rights metadata marked binding, testimony
      treated as omniscient causal proof, or Canon_Source song text scanned as Chapter_File prose.
    - _Requirements: 1.1, 6.1–6.19, 12.1–12.10, 14.1–14.4, 14.10–14.14, 15.1–15.5_

  - [x] 8.10 Write the principal property test for chapter plan/file bijection
    - **Property 1: Chapter plan and file bijection** — one principal Hypothesis test, at least 100
      generated examples.
    - **Validates: Requirements 11.3**; related 1.2, 1.3, 9.4, 12.2.

  - [x] 8.11 Write the principal property test for identifier/metadata integrity
    - **Property 2: Stable identifier, mechanism-state, and evidence referential integrity** — one
      principal test, at least 100 examples. Include every allowed CanonFact authority basis,
      valid/invalid ratified-note adoption, exact-five `DEC-014` inventories, omitted *Case Zero*,
      added *One-Time Pad*, demoted or unattributed *Case Zero* testimony, promoted non-lyric metadata,
      and testimony/publication used as causal proof. Also generate exactly-one-of-four-modes records;
      valid bounded and area-scale `CANCEL` records alongside addressed, insertive, reversible,
      enumerated-affected-set, area-scale-individual-consent, non-Mindwars, and provenance-yielding
      `CANCEL` rejections; consent/calibration/participant truth
      tables; send/pause/revoke/failure-recovery event streams; nontransferable Pair_Calibration;
      mandatory consent/transport metadata; default-off independently mutual recording; transcript
      subset/session/evidentiary scope; semantically opaque metadata; mandatory fluent-range coverage;
      Pairing_Session-to-existing-POV references; exact 56/32/33/7 loads; and rejected provenance
      confirmation. This remains one principal property test, not new Properties 16 or 17.
    - **Validates: Requirements 10.4, 14.1, 14.3, 14.4, 14.10–14.12, 14.14, 15.1–15.4**;
      related 1.4, 1.5, 4.2–4.4, 6.2, 6.17, 7.1–7.3, 9.5, 9.6, 10.3, 12.1, 12.4, 12.5,
      14.2, 14.13, 15.5.

  - [x] 8.12 Write the principal property test for Cross_Cut symmetry
    - **Property 3: Cross-cut graph symmetry** — one principal test, at least 100 examples.
    - **Validates: Requirements 1.6**; related 1.7.

  - [x] 8.13 Write the principal property test for prose word-count round trips
    - **Property 4: Prose word-count round trip** — one principal test, at least 100 examples,
      including empty, Unicode, punctuation, mixed line endings, and whitespace runs.
    - **Validates: Requirements 9.7**; related 10.3, 12.3.

  - [x] 8.14 Write the principal property test for length classes and limits
    - **Property 5: Length classification and limits** — one principal test, at least 100 examples.
    - **Validates: Requirements 2.8**; related 2.9–2.11, 12.3.

  - [x] 8.15 Write the principal property test for movement order and scale
    - **Property 6: Ordered movement architecture and scale** — one principal test, at least 100
      examples, including 29/32/51/16 and boundary variants.
    - **Validates: Requirements 11.4**; related 2.1–2.3, 3.1, 3.6–3.8, 11.5, 11.6, 12.7,
      15.5.

  - [x] 8.16 Write the principal property test for human POV/Anchor architecture
    - **Property 7: Human POV roster and Anchor coverage** — one principal test, at least 100
      examples.
    - **Validates: Requirements 11.7**; related 4.1, 4.2, 4.8–4.10, 8.8, 15.2, 15.3.

  - [x] 8.17 Write the principal property test for the POV run cap and run word limit
    - **Property 8: POV run cap and run word limit** — one principal test, at least 100 examples.
      Generate POV_ID and Prose_Word sequences together and exercise both bounds independently,
      including a three-chapter run totalling 3,601 words and a legal-length two-chapter run
      totalling 5,000 words. Both must fail.
    - **Validates: Requirements 2.7, 2.15, 11.12**; related 11.4, 12.16. The Mindwars turnover
      cadence formerly cited here is now Editorial_Review criterion 15.6, which no checker evaluates.

  - [x] 8.18 Write the principal property test for motif synchronization
    - **Property 9: Motif event synchronization** — one principal test, at least 100 examples.
    - Enforce chain events only in Discovery/Private Defense/Coda; counterphase as context absent an
      ArcChange; copper events only in Private Defense/Mindwars/Coda; Discovery copper as unledgered
      foreshadowing; two kettle events; and three Record_Progression events.
    - **Validates: Requirements 7.3**; related 7.1, 7.2, 7.12, 7.17, 7.18, 11.8.

  - [x] 8.19 Write the principal property test for ledger-driven literal constraints
    - **Property 10: Ledger-driven literal scope, count, and placement** — one principal test, at
      least 100 examples.
    - **Validates: Requirements 7.16**; related 7.7, 7.14, 7.15, 11.8, 12.6.

  - [x] 8.20 Write the principal property test for ArcChange/status atomicity
    - **Property 11: Post-baseline change and status atomicity** — one principal test, at least 100
      examples.
    - **Validates: Requirements 1.16**; related 1.17, 1.18, 7.3, 10.7, 10.8, 13.7–13.10.

  - [x] 8.21 Write the principal property test for local/global gate separation
    - **Property 12: Chapter-local and manuscript-global gate separation** — one principal test, at
      least 100 examples.
    - **Validates: Requirements 10.9**; related 10.1–10.5.

  - [x] 8.22 Write the principal property test for fail-closed inputs and exits
    - **Property 13: Fail-closed incomplete inputs and exit status** — one principal test, at least
      100 examples.
    - **Validates: Requirements 12.9**; related 11.1, 11.2, 12.10, 12.14, 12.15.

  - [x] 8.23 Write the principal property test for manuscript source exclusion
    - **Property 14: Manuscript source exclusion** — one principal test, at least 100 generated
      workspace trees with manuscript markdown and eligible control songs.
    - Assert against the Manuscript_Exclusion_Contract's reference collector, since Site_Build is
      external to this workspace.
    - **Validates: Requirements 9.3**; related 9.2, 11.9, 12.8.

  - [x] 8.24 Write the principal property test for independent final gates
    - **Property 15: Finalization requires both independent gates** — one principal test, at least
      100 examples.
    - **Validates: Requirements 11.11**; related 11.10.

  - [x] 8.25 Complete the required focused unit and edge-case suite
    - Cover all header, count, length, normal-share, orphan/duplicate/order, filename, Cross_Cut,
      roster, Anchor, POV-run, literal phrase, kettle, Record_Progression, status, incomplete-input,
      diagnostic exclusion, and local/global separation cases from the design.
    - Add explicit cases that keep `DEC-002`’s Nia name/person-specific-address/bench-path mapping
      distinct from `DEC-014`’s binding same-speaker lyric testimony; reject a record that collapses
      the entire mechanism into lyric authority or omits/demotes the canonical testimony; reject a
      causal-linkage record with a reveal owner or release window; accept an explicitly receive-only
      December apparatus with no transmit stage and a distinct later bench-transmit handshake over the
      same person-specific address; reject any December transmit event or use of page nine as proof of
      December transmission; binding `DEC-007` distribution records with both origin accounts
      still `unverified`; `heritage_base: unspecified_by_author` and rejection of any filled base or
      inferred real-world linguistic, geographic, religious, ethnic, or political particulars; Trust
      formation after the altered April record; later deposit of earlier sources; rolling deposits
      only after formation; present and resolvable `DEC-005` decision/entity references;
      intentionally unnamed geography state; accepted conditioned public Trust releases competing
      with official summaries; and rejection of a fully open adjudicating inquiry, a hidden/one-time
      release model, or provenance represented as objective truth. Confirm that name wording and
      capitalization variants preserving stable IDs produce no pass/fail diagnostic under Requirement
      12.11. Also cover accepted CanonFact authority bases; required adoption references for
      `ratified-note`; exact acceptance of the five `DEC-014` Canon_Source paths; rejection of a
      missing *Case Zero*, added *One-Time Pad*, advisory *Case Zero* lyric, missing speaker/limitation
      metadata, first-person testimony or publication status used as omniscient causal proof, and
      Production_Notes/style/exclude/generation/credits/rights metadata represented as binding facts
      or literal constraints; preservation of Canon_Source song text outside Chapter_File literal
      scans; preservation of the unresolved rights-footer follow-up and inward-frontier premise; and
      rejection of any derived radial interpretation of the canonical `three counties wide` text.
    - Add exact accepted/rejected `DEC-015` cases for one of four modes per event; passive live
      `RECEIVE`; nonsemantic addressed `INTRUDE`; unaddressed subtractive `CANCEL` in both bounded and
      area scope, with rejection of an addressed, insertive, reversible, enumerated, non-Mindwars, or
      provenance-yielding cancellation and of the null classified as `INTRUDE`;
      two-living-participant `PAIR`; current consent and matching
      Pair_Calibration; Deliberate_Send_Acts; unoffered-content exclusion; pause/revocation stop;
      clipping/latency/integrity recovery; nontransferable calibration; mandatory consent/transport
      metadata; recording disabled by default and enabled only by separate mutual consent; transcript
      session/subset/evidence limits; metadata semantic opacity; unconfirmed provenance; required
      Fluent_Pairing ranges; existing-POV session ownership; exact load vector; and rejection of dead,
      absent, replacement, simulation, archive, model, reconstruction, group-mind, and fifth-POV
      states. These tests validate structured records only and never score pairing prose.
    - Add exact accepted/rejected cases for `MOT-CHAIN-01..03` and `MOT-COPPER-01..03`.
    - _Requirements: 1.1, 2.7–2.11, 4.1–4.10, 6.2–6.19, 7.1–7.18, 9.5–9.7, 12.1–12.15, 14.1–14.4, 14.10–14.14, 15.1–15.5_

  - [x] 8.26 Complete the required integration and process-smoke suite
    - Test site isolation; minimal calibration gate on 1–5, 73, 118, 124; chapter-local scope;
      changed-reference batch scope; complete 128-entry global scope; and process flow from planning
      through exploratory calibration, full-suite evidence, one Baseline_Revision_Pass, approval,
      revision, and reapproval.
    - Test front-matter prose rights, acknowledgment of all five Canon_Source songs without
      *One-Time Pad*, and absence of recording/performance ownership language. Add a Canon-source
      authority smoke fixture that accepts the exact five `DEC-014` paths, attributed *Case Zero*
      lyric facts, advisory non-lyric metadata, and Chapter_File-only phrase scans, then rejects a
      missing *Case Zero*, added *One-Time Pad*, demoted lyric, promoted production metadata, or
      testimony used as causal proof. Use synthetic records/prose only; the tests do not evaluate
      artistry.
    - Add one Pairing mode/evidence smoke flow that loads valid `RECEIVE`, `INTRUDE`, and fluent
      `PAIR` records; pauses and revokes transport; injects an integrity failure and explicit recovery;
      verifies mandatory metadata and independent default-off recording; records only transported
      contributions; and rejects semantic metadata reconstruction, substituted/nonliving participants,
      transferred calibration, prohibited POV ownership, changed loads, and provenance closure.
    - _Requirements: 9.3, 9.11, 10.1, 11.1–11.9, 13.3, 14.1–14.14, 15.1–15.4_

  - [x] 8.27 Run and record the complete objective checker suite
    - Run every principal property test (at least 100 generated examples each), all focused tests,
      all integration/smoke tests, and the site-exclusion check. Resolve failures.
    - Record a `baseline-objective` GateResult showing complete global mode, deterministic exits, and
      a green mandatory suite. This evidence is required for task 10.2 and every post-calibration
      Drafting_Batch.
    - _Requirements: 1.14, 11.1–11.9, 12.14, 12.15_

- [x] 9. Checkpoint — calibration reviewed and full objective suite green **[HARD GATE]**
  - Ensure the eight exploratory chapters have clean local/batch results and recorded calibration
    Editorial_Review, and ensure the complete checker, all fifteen principal property tests, focused
    suite, integration suite, and site isolation pass.
  - Do not request Approved_Baseline approval or begin any post-calibration prose batch until this
    checkpoint passes.

- [x] 10. Revise the baseline and obtain author approval
  - [x] 10.1 Perform the single Baseline_Revision_Pass
    - For every calibration finding, write either an Arc_Outline change or a rationale for no change
      in `planning/arc-changes.md`; synchronize affected outline, Canon_Bible, Motif_Ledger,
      POV_Roster, Voice_Brief, and exploratory chapter references in the same change.
    - Keep representative chapters exploratory until their later movement batches reconcile them.
    - _Requirements: 1.12, 1.13, 1.17_

  - [x] 10.2 Record Approved_Baseline and Final_Targets **[AUTHOR] [HARD GATE]**
    - Only after task 9 and task 10.1, record author approval, exact planned chapter count, and one
      inclusive total Prose_Word range. Record rationale if outside provisional ranges.
    - Carry forward the binding title and record-frame selections from `DEC-001` and `DEC-006`.
      Calibration may remove or retain individual rare record references for dramatic necessity, but
      it may not reopen the selected restrained visibility model. Any later structural change requires
      an ArcChange; changing the author decision itself requires author adjudication.
    - _Requirements: 1.14, 1.15, 1.18, 2.2, 2.3_

- [x] 11. Checkpoint — Approved_Baseline established **[HARD GATE]**
  - Ensure Final_Targets and approval are readable by global mode; rerun the full suite after any
    baseline-related checker/reference change.
  - No remaining movement batch may begin before this checkpoint.

- [x] 12. Draft the remaining Discovery_Part chapters, 6–29
  - Every 4–8 chapter batch requires: clean chapter/batch objective checks; recorded chapter and
    batch Editorial_Review; and synchronized statuses plus affected Canon_Bible, Motif_Ledger,
    POV_Roster, Voice_Brief, ArcEntry, and ArcChange records before approval.

  - [x] 12.1 Draft chapters 6–10 — verification and institutional appetite
    - Follow the planned sequence: Julian audits funding disclosure and confirms the December
      receiver is receive-only and lacks any transmit stage; continuous source-side detail appears
      through the assigned selected POV or an attributed supporting-witness record without adding a
      POV; Mara repeats reception and maps neural timing; Julian sees appetite gather; Mara narrows
      from location toward a person-specific channel/address.
    - Keep the eight-second offset exclusively in Mara’s receive observation. Nia holds the source
      role per `DEC-002`; there is no alternate role assignment to select.
    - This is Julian’s first appearance after calibration; leave this batch unapproved until 12.2.
    - _Requirements: 2.4–2.7, 3.2, 4.12, 5.11, 6.2_

  - [x] 12.2 Record Julian’s first-appearance Editorial_Gate **[EDITORIAL] [HARD GATE]**
    - Cite representative chapter-6 prose and record `pass` or `revision` against Julian’s
      Voice_Brief: balanced review-facing clauses, documentary sensory field, institutional distance,
      complicity/evasion, and hearing-chamber Reverb_Profile.
    - Resolve any revision before approving the 6–10 batch.
    - _Requirements: 5.11, 5.13, 13.4_

  - [x] 12.3 Draft chapters 11–15 — the field
    - Show attention-linked frequencies, mind-as-field hypothesis, a repeatable person-specific
      channel/address the receive-only apparatus can identify and lock, an ordinary call echoing a
      recorded pattern, rights pressure, and early institute–Consortium contact. End on the reversal
      that a person is inferred more precisely than a location.
    - _Requirements: 3.2, 4.6, 6.16_

  - [x] 12.4 Draft chapters 16–20 — open invitation and separate arrival
    - Mara deliberately adds a temporary bench transmit path to the receive-only setup and sends the
      content-free handshake through the person-specific channel/address identified in December
      (`MOT-COME-01`). Nia later experiences a **wanting** during a two-call triage decision and routes
      on it as self-authored judgment (`DEC-002`, `DEC-004`). Nothing is said to her and no instruction
      crosses—a content-free handshake could not carry one, and the doctrine edits what people want
      rather than issuing orders.
    - Keep that later arrival separate from the continuous receive event and preserve unproved
      causation. Begin the `DEC-007` asymmetry: Mara develops high private conviction, but Nia accepts
      neither origin account and no narrator or instrument confirms either.
    - _Requirements: 3.13, 6.6, 6.7, 6.9, 7.8_

  - [x] 12.5 Draft chapters 21–25 — the casualty refuses reduction
    - Release the source/casualty identities per `DEC-002`: Nia owns both events, and this cluster is
      where the shared identity lands. Mara’s possible causation stays unresolved; give the reader
      every reason to connect the later handshake and wanting and no instrument that can prove it.
    - Carry `DEC-007` without fixed dialogue: Mara’s high, mostly unvoiced conviction drives an
      attempted confession; Nia rejects both unsupported origin accounts and refuses to let Mara make
      Nia’s injury into Mara’s story. That refusal is not absolution.
    - Give Nia ownership of the routing consequence and her refusal to become “case zero”. Per
      `DEC-004` she reconstructs the decision and finds no chain of reasoning that produced the
      certainty — she recovers what she wanted and not why. Let dispatch evidence, not coy
      withholding, determine the release point in chapters 50–55.
    - _Requirements: 1.4, 4.12, 6.8, 6.9_

  - [x] 12.6 Draft chapters 26–29 — the door runs inward
    - Show external interest, Mara’s confirmation that the apparatus can address as well as receive,
      controlled testing, and recognition of an arrival only after action. End Discovery on an
      uninvited crossing while sender and handshake causation remain unresolved.
    - _Requirements: 3.2, 3.13, 6.6, 6.7_

  - [x] 12.7 Record the Discovery_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon beats, movement turn, motif progression, POV distinction,
      cross-cut legibility, reveal fairness, hook variety, receive-only source continuity/offset
      clarity, later bench-transmission separation, page-nine chronology, technical scale attached to
      human consequence, and the `DEC-007` asymmetry without confirmation, appropriation, or
      absolution. Reject artificial withholding.
    - _Requirements: 2.13, 2.14, 4.12, 8.9, 13.4_

- [ ] 13. Draft the Private_Defense_Part chapters, 30–61
  - Apply the same per-batch completion rule as task 12.

  - [x] 13.1 Draft chapters 30–35 — copper and quiet
    - Build the copper room on the page: mesh, seams, door, first measured silence. Nia experiences
      relief and the cost of permanent enclosure; Julian separates reception, transmission, and
      consent while the Consortium defaults assent.
    - Assign `MOT-COPPER-01` and `MOT-CHAIN-02` only to their ledgered functions.
    - _Requirements: 3.3, 6.8, 7.9, 7.10_

  - [x] 13.2 Draft chapters 36–42 — the benevolent offer
    - Dramatize real medical, linguistic, and emergency benefits rather than merely naming them as
      temptation. Select living participants inside the four established POV chapters, begin
      pair-specific calibration through voluntary repeated sessions, show why participants freely
      choose the technology, and preserve Deliberate_Send_Acts and private unoffered mentation from
      the first useful exchange. Cross-cut the lived benefit against saleable institutional language
      and uncertainty over thought ownership. Julian brings the term sheet believing a contractual
      lock is possible.
    - _Requirements: 3.3, 4.6, 4.12, 6.8, 14.10, 15.2, 15.3, 15.6_

  - [x] 13.3 Draft chapters 43–49 — April, page nine
    - Give negotiation, specification reading, `transmit enable`, and consequence distinct scenes.
      Julian learns write capability is architectural; the casualty learns her experience was used
      without permission. Page nine confirms the broader danger and is never treated as evidence that
      Mara’s receive-only December rig transmitted.
    - Preserve April arrival and page-nine line as canon.
    - _Requirements: 3.3, 6.3, 6.8_

  - [x] 13.4 Draft chapters 50–55 — put it in the record
    - Mara refuses and demands preservation (`MOT-RECORD-01`). Julian first sees the April record
      altered, then forms the Civic Record Trust and opens post-formation rolling witness deposits.
    - Deposit Discovery-era logs/voice memoranda later as pre-Trust contemporaneous sources with
      original composition provenance. Never backdate Trust activity.
    - Release the `DEC-004` consequence here: the dispatch timestamps show the death was already
      unsurvivable before Nia's routing. Her decision is cleared; her authorship is not, and she still
      cannot say whose certainty it was. Deposit the log with her account—it is the anchor the
      histories later misread. Under `DEC-007`, Julian professionally records the adversary
      attribution because it is institutionally enterable while privately preserving that it is
      inference, and Nia refuses both that account and Mara’s.
    - _Requirements: 6.9, 6.14, 7.17, 7.18_

  - [ ] 13.5 Draft chapters 56–61 — the handle inside
    - Put the first sustained Fluent_Pairing conversation on page. Draft, break, and repair the
      specific/current/revocable consent protocol (`MOT-COME-02`, `MOT-KNOCK-01`): every contribution
      has a Deliberate_Send_Act; pause or revocation stops transport; clipping, latency, or integrity
      failure is exposed; and participants confirm, retry, or fall back to ordinary speech rather than
      accepting guessed completion. Preserve mandatory Consent_State_Metadata and Transport_Metadata;
      keep Content_Recording separately mutual and off by default; and limit any selected transcript
      to contributions actually carried in that session. Copper spreads but cannot restore public
      life; Julian leaves Consortium representation and secures deposits. End on synchronized
      intrusion beyond private-room defense.
    - _Requirements: 3.3, 6.8, 7.8, 7.11, 14.10–14.12, 15.2, 15.3, 15.6_

  - [ ] 13.6 Record the Private_Defense_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon, movement turn, motif progression, voice separation,
      institutional chronology, Julian’s professional-attribution/private-inference split, Nia’s
      refusal of both origin accounts, whether a valid ethical rule remains a physically inadequate
      answer rather than a simple villain declaration, whether Chapters 36–42 establish freely chosen
      benefit and calibration, and whether Chapters 56–61 make Fluent_Pairing clear, send-gated,
      revocable, failure-aware, and dramatically consequential without exposing background thought or
      overclaiming metadata/transcripts. Confirm technical information arrives through action/result/
      consequence rather than an exposition set piece or recognizable imitation.
    - _Requirements: 2.13, 4.12, 8.9, 13.4, 14.10–14.12, 15.6–15.8_

- [ ] 14. Checkpoint — Discovery and Private Defense approved **[HARD GATE]**
  - Ensure all batches, movement Editorial_Gates, statuses, and references are synchronized and all
    tests remain green. Run site isolation with real manuscript files present.
  - Do not begin Mindwars drafting until this checkpoint passes.

- [ ] 15. Draft the Mindwars_Part chapters, 62–112
  - Apply the same per-batch completion rule as task 12. Active counterphase and rhetorical
    collective declaration begin and end in this movement.

  - [ ] 15.1 Draft chapters 62–69 — no first shot
    - Show unrelated intrusive arrivals, no unifying sender, emergency classification hardening into
      policy, and Mara refusing a public flag despite her high private conviction about the later
      handshake. Present the first casualty from Nia’s experience per `DEC-002`; Nia still refuses
      both unsupported origin accounts. Under `DEC-007`, Julian enters the adversary attribution
      because it is the only institutionally available account while privately knowing it is
      inference. Nothing here confirms or refutes either origin account.
    - Keep every origin theory attributed and unconfirmed; characters do not yet possess a stable
      in-scene war name.
    - _Requirements: 3.4, 3.13, 6.5, 6.7_

  - [ ] 15.2 Draft chapters 70–77 — mirror of the signal
    - Reconcile exploratory chapter 73 into final continuity and demote it to `revised` after any
      substantive change. Mara proves cancellation also transmits; Nia owns its consent meaning; and
      Fluent_Pairing operates under counterphase pressure through the existing POV architecture. Make
      each contribution deliberately sent, preserve unoffered mentation, expose pause/revocation and
      transport integrity state, and let the first bounded-local field-volume test leave Nia with a
      concrete gap in access to a familiar phrase that the protocol must confront. Mara may know only
      Nia's failed deliberate send and/or immediate report, never unoffered thought. Keep consent
      current and local; metadata records transport but reveals no unrecorded meaning.
    - Keep `MOT-YES-01` in Mindwars only.
    - _Requirements: 3.4, 6.8, 7.14, 10.8, 13.9, 14.10, 14.12, 15.6_

  - [ ] 15.3 Draft chapters 78–85 — a shield can enter
    - Officials seek automatic protection; Julian uses page nine to expose defenders adopting the
      feared capability without implying the Consortium sent the signal. Nia chooses one bounded
      risk. Mara’s public “we” remains answerable to named singular consents. Make operational
      Fluent_Pairing a mandatory principal thriller engine here and through Chapter 93.
    - Select living pair identities and supporting participants while keeping every session inside
      Mara, Nia, or Julian's existing POV chapters and preserving all four POVs and fixed loads.
      Dramatize speed and legitimate tactical value alongside send gating, pause/revocation, latency,
      clipping, and integrity handling. Traffic analysis may reveal timing, volume, acknowledgments,
      consent transitions, and errors but never unrecorded meaning; Content_Recording remains separate
      and default-off, and any transcript proves only carried session content. Do not make a human
      faction the source of the Foreign_Signal or Nia's wanting, transfer calibration, read arbitrary
      memory, expose unoffered thought, or treat engineered records as a substitute for Safiya's
      corpus-less private layer.
    - Assign `MOT-COME-03`.
    - _Requirements: 3.13, 6.8, 7.8, 8.7, 14.10–14.12, 14.14, 15.2–15.4, 15.6_

  - [ ] 15.4 Draft chapters 86–93 — territory
    - Intensify effects and competing unconfirmed theories; earn the title's governing reversal
      rather than merely invoking a frontier metaphor: every inherited map points out toward space,
      but human minds are the shore being crossed, humanity is the territory rather than the explorer,
      and the Mindwars are the event that makes that truth legible. Continue operational
      Fluent_Pairing as a principal engine across converging existing POV threads: pair-specific
      exchanges change tactical knowledge and relationships, while traffic analysis changes the
      evidentiary position without reconstructing content. Show local counterphase pockets and the
      predicted synchronized breach without converting the premise into an explanatory speech or
      adding a sender/operative POV.
    - Counterphase is connective chain context only. Do not assign a fourth chain Motif_Event.
    - _Requirements: 3.4, 3.13, 6.7, 6.18, 6.19, 7.10, 14.10–14.12, 14.14, 15.2–15.4, 15.6_

  - [ ] 15.5 Draft chapters 94–101 — the affected area in the model
    - Model a broad null as the only likely defense. Julian finds documentation that the affected
      area is canonically described as three counties wide; the country and each county remain
      unnamed under `DEC-005`. Mara predicts subtraction but cannot identify vulnerable memories;
      Nia refuses manufactured unanimity. Scale `PAIR` into ethical and infrastructural risk through
      two-person sessions, metadata aggregation, coercive deployment pressure, and bounded endpoint
      danger without group mind, hive mind, mass mind reading, transferable calibration, semantic
      metadata recovery, or provenance proof. Tie each technical escalation immediately to consent,
      relationship, evidence, institutional power, or bodily risk.
    - Use `MOT-RADIUS-01` thematically as an admission of cost, never as a computed geographic
      measurement or victory slogan.
    - _Requirements: 3.4, 6.4, 6.10, 7.13, 8.6, 14.5–14.14, 15.6_

  - [ ] 15.6 Draft chapters 102–108 — null night
    - Hold seven reciprocal Cross_Cuts on one Timeline_ID: Nia in a consent shelter, Julian
      preserving authorization, Mara driving exact counterphase. Use two-person Fluent_Pairing to
      coordinate under failure pressure without collapsing distinct participants into collective
      consciousness; preserve local consent, Deliberate_Send_Acts, pause/revocation, integrity state,
      and semantically opaque evidence even at infrastructure scale. The null affects civilians
      throughout an area canonically described as three counties wide, silences the Foreign_Signal,
      and diminishes Mara’s internal voice.
    - Do not enter Safiya’s home or preempt her Tuesday account. Record purposes for any
      simultaneity/interruption microchapters.
    - _Requirements: 1.6, 2.10, 2.11, 3.10, 6.10, 14.5–14.12, 14.14, 15.2, 15.3, 15.6_

  - [ ] 15.7 Draft chapters 109–112 — the history of quiet
    - Announce success without surrender, counterparty, treaty, or all-clear. Julian enters consent
      dispute and civilian uncertainty into history (`MOT-RECORD-02`) while official summaries begin
      smoothing inference into fact. Under `DEC-005`, the Civic Record Trust begins conditioned,
      provenance-preserving public releases that challenge those summaries without opening complete
      holdings or creating an adjudicating inquiry; the first-casualty attribution stays an
      uncorrectable inference. Nia rejects “saved” as a complete category and, under `DEC-007`, stops
      making usable self-trust contingent on learning the wanting’s origin. She can exercise judgment
      without deciding causation, forgiving Mara, or validating the archive. Pairing metadata,
      transcripts, traffic analysis, and endpoint danger remain unable to settle the wanting or the
      Foreign_Signal; Fluent_Pairing begins to recede as the war-level action ends. Mara ends active
      counterphase and withdraws behind retained copper (`MOT-COPPER-02`).
    - End the war-level action with the signal silent and uncounted absence remaining.
    - _Requirements: 3.9, 3.10, 6.5, 7.9, 7.17, 7.18, 14.12, 14.14, 15.6_

  - [ ] 15.8 Record the Mindwars_Part movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for canon, turn, motifs, tactical consent pressure, human cost,
      non-glamorized counterphase, unresolved provenance, Mara’s belief remaining non-authoritative,
      Julian’s inference remaining labeled, Nia’s usable-self-trust resolution without absolution or
      archive validation, and a real non-triumphal conclusion with no adversary spectacle. Confirm
      Chapters 70–108 make Fluent_Pairing repeatedly useful, send-gated, revocable, failure-aware,
      two-person, and evidence-bounded without exposing unoffered thought, creating a new POV, or
      resolving origin. Confirm `DEC-016`'s fastest/tightest Mindwars threading, varied information
      turns, experiment/action/result/consequence exposition, and immediate human stakes without
      repetitive fake cliffhangers, lecture set pieces, culprit reveal, group mind, or recognizable
      imitation of either cited author.
    - _Requirements: 2.13, 4.12, 8.6, 8.9, 13.4, 14.10–14.14, 15.2–15.8_

- [ ] 16. Checkpoint — war-level action settled **[HARD GATE]**
  - Ensure all Mindwars batches and gates pass; active counterphase has ended; the Foreign_Signal is
    silent; the affected-area record retains canonical wording; provenance remains unconfirmed.
  - Do not begin Coda drafting until this checkpoint passes.

- [ ] 17. Draft the Aftermath_Coda chapters, 113–128
  - **Completion rule for every Coda batch:** run clean chapter/batch objective checks; record
    chapter-level and batch-level Editorial_Review; and synchronize Chapter_Status, Batch_Status,
    ArcEntries, Canon_Bible, Motif_Ledger, POV_Roster, Voice_Briefs, and affected ArcChanges before
    approval. No renewed signal, counterphase, campaign, adversary proof, spectacle escalation, or
    Pairing-based counterfeit restoration is permitted. Neural-channel use must recede across the
    Coda so ordinary voice, listening, presence, refusal, and outward obligation carry the action.

  - [ ] 17.1 Draft chapters 113–117 — public bill to threshold
    - Nia handles civilian-loss intake from usable self-trust that no longer depends on resolving her
      wanting’s origin; this is not absolution or archive validation. Within `DEC-005`’s contested
      public record, Julian finds Safiya’s request while preparing another witness-conditioned Trust
      release that competes with official summaries without opening complete holdings or adjudicating
      truth. He preserves Safiya’s control of contact; Safiya crosses affected communities without
      becoming their spokesperson; chapters 116–117 present the same three unhurried knocks from both
      sides as one `MOT-KNOCK-02` event.
    - Keep action in accounting, approach, and waiting, not combat. Begin deliberate post-112
      deceleration through disclosure, arrival, and threshold choice; do not use Fluent_Pairing or a
      new threat as the Coda's propulsion.
    - _Requirements: 3.5, 6.4, 7.11, 8.2, 14.14, 15.6_

  - [ ] 17.2 Draft chapters 118–123 — accounting and valid consent **[HARD GATE]**
    - Reconcile exploratory chapter 118 into final continuity; substantive changes set it and its
      ArcEntry to `revised`. Preserve Safiya’s Tuesday kettle, eleven-mile location, absence of
      foreign intrusion, and maternal-language loss (`MOT-KETTLE-01`).
    - Apply `DEC-003`: describe-never-quote; preserve
      `heritage_base: unspecified_by_author` everywhere; infer or invent no real-world linguistic,
      geographic, religious, ethnic, or political particulars from Safiya’s name or the unspecified
      base; use no real-language wording or allegory. Safiya owns her account. Mara receives the
      affected area canonically described as three counties wide as people rather than geometry
      (`MOT-RADIUS-02`). Safiya’s affirmative, sober, repeated consent remains valid and does not
      compel a counterfeit. Make the `DEC-015` physics explicit without turning the scene into a
      lecture: `PAIR` requires a living second participant and pair-specific calibration; Safiya's
      mother is dead; no corpus survives; and no archive, simulation, model, reconstruction, metadata,
      or Pairing_Transcript can supply the missing source truth.
    - _Requirements: 6.4, 6.11, 6.12, 7.12, 7.13, 8.1, 14.6, 14.8, 14.11, 14.13, 15.6_

  - [ ] 17.3 Draft chapters 124–128 — truthful refusal, staying, and outward duty
    - Reconcile exploratory 124 and demote on substantive change. Preserve relay-off/second-kettle
      Coda_Turn (`MOT-COME-04`, `MOT-KETTLE-02`), then narrow Mara to water, chairs, breath, and
      listening; let Safiya accept presence without calling it repair; use ordinary spoken voice
      through air in a consenting room (`MOT-CHAIN-03`). Do not reactivate Fluent_Pairing, use a
      Pairing_Transcript as substitute memory, or let metadata/archive/simulation language make the
      refusal ambiguous; the available remedy is presence, not reconstructed content.
    - In 128, Mara records an entry against herself (`MOT-RECORD-03`) and visits affected
      communities, knocking and waiting (`MOT-KNOCK-03`) rather than broadcasting. The declared
      Final_Passage contains `Whose was that?` exactly twice and nowhere else; no sender is solved.
    - Apply `DEC-017`. Inside that same `MOT-RECORD-03` entry, and only there, Mara names the consent
      parallel exactly once: the protocol she was held to was one room wide, and she then ran the same
      mechanism across an area canonically described as three counties wide with no one to ask. This is
      the manuscript's only explicit statement of the parallel and the payoff of a disclosure the reader
      could have assembled since Chapter 118. Keep it dry and self-indicting rather than explanatory: it
      resolves no provenance, absolves nothing, validates no archive, does not reinterpret Safiya's
      consent, and does not turn the Coda into argument. It is her last act before going out to knock
      and wait, and it adds no Motif_Event ID, Literal_Phrase_Constraint, or Reveal record.
    - _Requirements: 3.12, 3.13, 7.10, 7.16, 7.17, 8.3, 8.4, 8.6, 14.8, 14.12–14.14, 15.6_

  - [ ] 17.4 Record the Aftermath_Coda movement Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for contraction from public consequence to intimate encounter and
      outward obligation; Safiya’s genuine consent and autonomy; refusal as truth/physics rather
      than moral evasion; no imposed forgiveness; quiet human scale; unmet restoration; the
      Refused_Swell; neural-channel recession; ordinary spoken voice and listening retaining their
      force; and Pairing evidence never becoming reconstruction or provenance proof. Confirm
      `DEC-016`'s post-112 deceleration through disclosure, arrival, refusal, emotional choice, and
      moral remainder without renewed threat, spectacle, group mind, repetitive fake cliffhangers,
      exposition set pieces, or recognizable imitation.
    - Under `DEC-017`, record `pass`/`revision` on the single named payoff: whether Mara's Chapter 128
      statement of the consent parallel reads as dry self-indictment inside the existing entry against
      herself rather than as a closing thesis about consent; whether it leaves provenance unresolved,
      grants no absolution, validates no archive, and leaves Safiya's consent intact; and whether
      Chapters 113–123 stayed silent so the naming still lands. Flag as `revision` any second explicit
      statement anywhere in the Coda, any version that explains the world instead of indicting Mara, and
      any drift of the naming outside the `MOT-RECORD-03` beat.
    - Confirm the Coda has not become a fourth war movement. Do not use chapter length, room count,
      or numerical prose metrics as craft proxies.
    - _Requirements: 3.11, 3.12, 6.12, 6.13, 8.9, 8.10, 14.12–14.14, 15.6–15.8_

- [ ] 18. Run manuscript-global acceptance
  - [ ] 18.1 Verify Final_Prerequisites
    - Require readable Approved_Baseline, Front_Matter, every planning reference, every planned
      Chapter_File, and passed Chapter_Local_Gate for each file. Missing/incomplete inputs return
      `incomplete` or `revision`, never pass.
    - _Requirements: 10.2, 11.1, 11.2_

  - [ ] 18.2 Run the Manuscript_Global_Gate and site-exclusion audit
    - Verify plan/file bijection; contiguous movement order; exact approved count and total range;
      Mindwars longest/Coda shortest; 3–5 POVs with Anchor coverage; 80-percent normal share; no
      Same_POV_Run exceeding three chapters or 3,600 combined actual Prose_Words using final
      `ChapterHeader.words`; all literal constraints; motif/header synchronization including
      chain/copper mappings; canonical chronology/extent records; structured `DEC-015` mode, consent,
      calibration, send-event, pause/revocation, failure-recovery, metadata, recording, transcript,
      evidence-scope, fluent-range, session-to-existing-POV, and fixed-load invariants; resolvable
      `DEC-005` decision/entity references plus its structured unnamed-geography and contested-archive
      state, without scoring name wording/capitalization; statuses; and zero manuscript site entries.
    - Resolve every violation and require exit `0`.
    - _Requirements: 2.8, 3.7, 3.8, 9.3, 11.3–11.9, 11.12, 12.7, 12.8, 12.14–12.16, 14.1–14.14, 15.1–15.5_

  - [ ] 18.3 Record the final Editorial_Gate **[EDITORIAL]**
    - Record `pass`/`revision` for POV distinctness, Cross_Cut clarity, hook effectiveness, tonal
      coherence, originality, emotional truth, unresolved provenance, Nia’s completed usable-self-trust
      movement without absolution or archive validation, Safiya’s unspecified-base guardrail, real war
      conclusion, the Coda’s unmet obligation/quiet contraction, mandatory Fluent_Pairing serving
      action and consequence without privacy/evidence overreach, the fastest/tightest Mindwars
      threading, and deliberate post-112 deceleration. Reject recognizable named-author imitation,
      repetitive artificial cliffhangers, exposition set pieces, culprit closure, renewed Coda
      spectacle, and group mind. Use qualitative evidence, not scores.
    - _Requirements: 2.14, 8.10, 11.10, 12.13, 14.13, 14.14, 15.4–15.8_

  - [ ] 18.4 Mark the Manuscript `final`
    - Permit final status only when both Manuscript_Global_Gate and final Editorial_Gate pass.
      Synchronize every Chapter_Status, Batch_Status, ArcEntry, and affected reference record.
    - _Requirements: 10.7, 11.11, 13.7, 13.8_

- [ ] 19. Final checkpoint
  - Ensure every required test and gate passes, all statuses/references are synchronized, the site
    still excludes the manuscript, and the final quiet ending remains intact. Ask the user if any
    questions arise.

## Notes

- All tests in tasks 3.2, 7.7, and 8.10–8.27 are mandatory. Each design property receives exactly
  one principal property-based test with at least 100 generated examples.
- The Nia name/person-specific-address/bench-path mapping remains controlled by `DEC-002` in its
  protected causally linked form. `DEC-014` separately makes *Case Zero*’s first-person same-speaker
  account binding Canon_Lyric. December is receive-only with no transmit stage; Chapters 16–20 add a
  temporary bench transmit path and later handshake through the locked address. Keep the lyric
  testimony and author-decision mechanism as distinct authority records, and keep the causal linkage
  `unverified`, with no reveal owner or release window. Page nine establishes broader architectural
  capability, not December transmission.
- Binding `DEC-007` selects “Asymmetric, and Nia moves toward release”: Mara’s high private causal
  conviction is non-authoritative; Nia rejects both accounts and eventually regains usable self-trust
  without absolution or archive validation; Julian professionally records an attribution he privately
  knows is inference. Neither origin account is ever confirmed.
- Binding `DEC-012` retains the late contested institutional term **Electronic Speech Pairings**;
  binding `DEC-015`, as amended 2026-09-11, supplies the complete four-mode authority. `RECEIVE` is
  passive live observation
  with no write or transmit stage; `INTRUDE` is an unconsented or uncalibrated nonsemantic write to a
  person-specific address; `CANCEL` is an unaddressed subtractive counterphase field;
  `PAIR` is deliberately sent near-natural internal speech between exactly two living people with
  current specific revocable mutual consent and pair-specific calibration. Unoffered mentation stays
  private; pause/revocation stops transport; calibration cannot transfer or connect to the dead,
  absent people, simulations, archives, models, or reconstructions. Every Pairing_Session has
  semantically opaque consent/transport metadata; Content_Recording is separately mutual and off by
  default; transcripts prove only recorded protocol-carried content. Pairing cannot reconstruct
  Safiya's private layer or close Nia's or the Foreign_Signal's provenance. Fluent use is mandatory in
  36–42, 56–61, 70–77, 78–93, and 94–108, remains inside the four POVs and 56/32/33/7 loads, and
  recedes after Chapter 112.
- The 2026-09-11 `DEC-015` amendment added the fourth mode `CANCEL` to resolve a real contradiction
  rather than to add capability. The null-night chronology records an active transmit stage with no
  person-specific address whose effect cancels the Foreign_Signal and causes subtraction. The old
  three-mode taxonomy left only `INTRUDE`, which requires a target and is limited to nonsemantic
  salience, valence, urgency, certainty, preference, or wanting — and Safiya losing access to her
  private maternal layer is not a preference. Because every event must occupy exactly one mode, the
  only available mode forbade what the null canonically does, and the whole Coda rests on that event.
  `INTRUDE`'s limit is unchanged; the null is simply no longer an `INTRUDE` event. December stays
  receive-only, page nine stays broader-capability-only, and both origin accounts stay `unverified`.
- Requirements 14 and 15 were trimmed in the same pass. Requirement 14 went from 19 criteria to 14
  including five new `CANCEL` rules; Requirement 15 went from 18 to 8. Every removed criterion was
  one that could only be judged by reading prose, which Requirement 12.12 forbids the checker from
  doing. Their substance is carried by the structural criteria that remain and by new Requirement 15.6,
  which names Editorial_Review as the owner of freely chosen pairing benefit, sustained on-page fluent
  conversation, experiment/action/result/consequence staging, immediate human stakes for escalation,
  Mindwars threading cadence, Coda deceleration, and evidentiary claims no broader than their records.
  The movement Editorial_Gates in tasks 8.7, 12.7, 13.6, 15.8, 17.4, and 18.3 already perform that
  review; the beat content itself already lives in the design beat tables and in tasks 5.3–5.5,
  13.2, 13.5, and 15.2–15.7. Nothing was dropped, only relocated to the gate that can actually judge it.
- Binding `DEC-017` governs the Chapter 73 / null-night consent parallel as delayed disclosure with a
  single named payoff. `DEC-015`'s fourth mode makes the bounded Chapter 73 test and null night the
  same `CANCEL` operation at two scopes, so Nia's `Did I say yes?` consents to the mechanism that later
  takes Safiya's private maternal layer at a scale where consent is structurally impossible. No
  character states that connection in Chapters 62–123 — not Mara, not Nia, not Julian — because Mara's
  binding weakness is converting a room into doctrine, and naming it while the war or the accounting is
  live produces exactly the consent lecture tasks 8.5, 17.2, and 17.3 forbid. Instead the parallel is
  made findable: Chapters 73 and 118 share a concrete physical vocabulary for a cancellation field
  experienced from inside, Chapter 73 has the authorization question asked and answered, and Chapter 118
  has the same experience with no question anywhere near it. The absence of the question is the echo,
  and a reader who assembles it gets the connection roughly forty-five chapters early. Mara names it
  exactly once, in the Chapter 128 entry against herself inside `MOT-RECORD-03`: the protocol she was
  held to was one room wide, and she then ran the same mechanism across an area canonically described as
  three counties wide with no one to ask. That naming resolves no provenance, absolves nothing,
  validates no archive, does not reinterpret Safiya's consent, and does not convert the Coda into
  argument. Retired alternatives are naming it during the Mindwars or the accounting, never naming it,
  and giving the naming to Nia or Julian — the first flattens it into thesis, the second lets Safiya's
  injury read as bad luck rather than the structural cost of a defense Mara and the authorizing
  institution chose after abandoning the individual protocol because it could not scale, and the third
  turns self-indictment into accusation or policy. Like `DEC-016`, this is craft direction enforced by human
  Editorial_Gates: tasks 8.7 and 17.4 record it explicitly, and the remaining movement and final gates
  own it under their existing canon, motif, doctrine, and Coda-contraction criteria. It adds no
  requirement, acceptance
  criterion, correctness property, Motif_Event ID, Literal_Phrase_Constraint, or Reveal record; the
  parallel rides entirely on existing `MOT-YES-01`, `MOT-KETTLE-01`, and `MOT-RECORD-03`, and the closed
  `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` mappings stay closed. `planning/canon-bible.md`,
  `pov-roster.md`, `voice-briefs.md`, and `motif-ledger.md` carry it later under tasks 4.2–4.5.
- Binding `DEC-016` selects an original rotating-perspective technothriller architecture: three
  active information threads through Chapters 1–112, followed by Safiya as a fourth Coda viewpoint
  that changes the moral scale; varied information/decision/moral turns; experiment → action → result
  → consequence exposition; fastest and tightest Mindwars threading; and deliberate Coda deceleration. Dan Brown and Douglas E.
  Richards are structural references only; do not imitate either author's sentence-level prose,
  distinctive voice, recognizable phrasing, scenes, or characters.
- This corrective design-first pass intentionally does not edit Task 4 artifacts. Before Task 5
  execution, downstream synchronization still required is exact. `planning/record-schemas.md` no
  longer owes work: on 2026-09-11 it received a `DEC-015` amendment that extended the existing
  `TimelineEntry.technical_state` object with a `mode` enum covering `RECEIVE`, `INTRUDE`, `CANCEL`,
  `PAIR`, and `not-applicable`; a closed four-mode invariant table; a `CancelState` object carrying
  scope, individual consent or institutional authorization, subtraction description, the three
  untargetability flags, absent additive inverse, and zero provenance yield; a `PairState` object
  carrying two living participants, consent, pair-calibration identity and nontransferability, and
  deliberate-send state; a `PairingEvidence` object carrying mandatory semantically opaque metadata,
  default-off per-participant recording consent, and transcript scope; an area-scale `CANCEL` fixture
  example; and a conformance note for records written before the amendment. No new record type was
  added, and the earlier proposal for separate `MechanismState`, `PairingEvidence`, and
  `PairingTranscript` records is withdrawn. Task 4.1's checkbox stays checked because its original
  scope was met; this amendment is later work on a completed file, not an unmet obligation.
  Artifact synchronization under tasks 4.2, 4.3, and 4.4 is complete: `planning/canon-bible.md`
  carries the `DEC-012`/`DEC-015`/`DEC-016` canon, four-mode, evidence, Safiya, and provenance
  records; `planning/pov-roster.md` binds the selected pair identities to existing POV chapters
  without changing the roster or loads; `planning/voice-briefs.md` distinguishes mode experience and
  register while carrying only original `DEC-016` craft traits; and the existing `technical_state`
  objects conform to the amended schema. The closed motif mapping needs no redesign-only change, and
  generic EditorialFinding/ArcChange schemas remain sufficient.
- Binding `DEC-014` supersedes `DEC-013`: `songs/Case Zero.md` is the fifth Canon_Source and its
  publication is author-approved/in progress. Its lyric is binding tier-3 testimony with
  first-person attribution; its Production_Notes, style/exclude directions, generation workflow,
  credits, and rights metadata remain non-story/advisory unless separately ratified. The lyric keeps
  the wanting nonverbal, both origin accounts unverified, and Nia’s resolution free of absolution or
  archive validation. Song occurrences remain outside Chapter_File literal scans. The contradictory
  rights footer remains an unresolved nonlegal author/rights-review follow-up that publication does
  not settle. The *One-Time Pad* draft is preserved in git history and removed from the working tree;
  it is unpublished and noncanonical for the book.
- Safiya's lost language is a two-person private layer; her public heritage language and occasional
  interpreting work survive. The base remains `heritage_base: unspecified_by_author` everywhere
  (`DEC-003`). Describe-never-quote is the default, invented private-layer words are permitted
  sparingly, real heritage wording is unavailable, and no record may infer real-world linguistic,
  geographic, religious, ethnic, or political particulars from her name or the unspecified base.
- The source morning is continuous. Only Mara measures the eight-second reception/transport offset;
  the December apparatus is receive-only, and the later bench-path handshake/wanting event is
  distinct.
- Null extent is stored and narrated as an affected area canonically described as three counties
  wide. `Silence has a radius` remains a thematic motif, not a geometric conversion.
- The Civic Record Trust forms after Julian sees the April negotiation record altered. Discovery
  logs/voice memoranda predate it and are later deposited; rolling Trust deposits start only after
  formation.
- Binding `DEC-005` confirms `Northline Array`, `Open Channel Consortium`, and `Civic Record Trust`
  and keeps the country and individual counties unnamed. After the null, conditioned,
  provenance-preserving Trust releases and official summaries compete publicly; neither a fully open
  inquiry nor a secret/one-time partial release replaces that contest, complete holdings are not
  presumed public, and the first-casualty attribution remains an uncorrectable inference.
- `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` use the closed mappings in task 4.5. Counterphase and
  Discovery copper foreshadowing do not silently create extra events.
- Site_Build is external to this workspace. Isolation is delivered as the Manuscript_Exclusion_Contract
  plus its reference collector and standing test, which land before root-level front matter. A green
  local test proves the contract is well-formed and honored by a conforming collector; it does not
  prove the external lyrics repository has adopted it. Adoption is an external follow-up.
- The five Canon_Sources are exactly the reference copies at `songs/The Synaptic Frontier.md`,
  `songs/Faraday.md`, `songs/The Final Frontier.md`, `songs/The Radius.md`, and
  `songs/Case Zero.md`. Under `DEC-011` and `DEC-014`, Canon_Lyric and explicit author decisions bind
  continuity while first-person testimony remains attributed rather than omniscient. Production_Notes
  and other non-lyric metadata are advisory unless an approved requirement or author decision
  expressly ratifies a proposition; the checker rejects unratified material represented as a
  Binding_Canon_Fact or Literal_Phrase_Constraint. The *One-Time Pad* draft is preserved in git
  history, removed from the working tree, not a Canon_Source, and supplies no required novel
  continuity.
- The title's governing premise is binding: the final frontier was not outer space but humanity's own
  minds. The Mindwars are the event that reveals people as the territory crossed, not the title or
  whole meaning of the book.
- Tasks 7.1–7.8 are the minimal objective gate for exploratory calibration. Full checker work and
  all mandatory tests run in parallel with task 8’s prose track; task 9 blocks baseline approval and
  every post-calibration batch until the complete suite is green.
- Calibration comprises chapters 1–5, 73, 118, and 124. Representative chapters stay exploratory
  until their final-continuity movement batches reconcile them. Julian’s first later appearance has
  a separate Requirement 5.11 Editorial_Gate.
- **[EDITORIAL]** findings remain human-only. The checker never scores prose craft.
- Every post-baseline 4–8 chapter batch, including every Coda batch, needs clean objective checking,
  chapter/batch editorial review, and synchronized statuses/references before approval.
- Binding `DEC-016`, as amended 2026-09-13, caps a same-POV run at three chapters **and** 3,600
  combined Prose_Words, counted on the global sequence so the 29/30, 61/62, and 112/113 boundaries
  count like any other adjacency. The word limit is the operative one, because three normal chapters
  could reach 4,800 words and even a two-chapter run could reach 5,000. `ArcEntry.estimated_words`
  carries the planning value and is required for every entry in a multi-chapter run; the finished
  manuscript is checked against `ChapterHeader.words`. The 2,500-word Hard_Chapter_Maximum is
  unchanged and applies independently.
- Two `DEC-015`/Trust invariants are only partly automatable at this schema version, and task 7.7
  implements exactly the decidable part rather than guessing the rest. First, the `PairState` rule
  that a `paused`, `revoked`, or `integrity-failed` session carries no transported semantic content
  "in the same or a later event without an explicit recorded confirmation, retry, or ordinary-speech
  fallback": a transcript is the only transported content the schema represents, so the checker
  enforces the single-entry rule (`PAIR_STOPPED_SESSION_TRANSPORT`) and treats a later entry
  returning to `required` as the recovery. Ordering a recovery marker across an event stream would
  need fields `record-schemas.md` does not define; until an ArcChange adds them, that part stays a
  human continuity reading. Second, `record_chronology` proves composition, deposit, and release are
  separate resolvable entries, but not which is earlier — order lives in the prose
  `relative_chronology` field, and reading it would mean inferring continuity from commentary. Both
  limits are stated in the affected test docstrings rather than left implicit.

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
