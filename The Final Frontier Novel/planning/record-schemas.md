# Planning Record Schemas

Schema version: **1**  
Amended: **2026-09-11** — `TimelineEntry.technical_state` extended with the four-mode enum, `CancelState`, `PairState`, and `PairingEvidence` under the amended `DEC-015`. No record type was added; mechanism and pairing state live inside the existing chronology record.  
Amended: **2026-09-13** — `ArcEntry` gains the required `estimated_words` key, integer or `null`, so the `DEC-016` same-POV run word limit of 3,600 Prose_Words is checkable at planning time. No record type was added. Existing `ArcEntry` records written before this amendment must gain the key; a conformance note is warranted because the record is closed to unknown fields and permits no omitted key.  
Amended: **2026-09-15** — the [Character ID registry](#character-id-registry) states where a Character ID is authoritatively declared, so a `TimelineEntry.participants` or `PairState.participants` reference to a non-viewpoint supporting character resolves instead of dangling. No record type, field, or enum value was added, and no existing record changes: the registry is the union of `POVProfile.character_id` values and approved `character-name` `NovelExtension` records, all four of which already lead their `fact` with the declared Character ID. The `POVProfile` bijection rule is unchanged and is now explicitly scoped to `POVProfile` records, which is the only place it ever applied.  
Applies to: planning records and the logical representation of Chapter Headers for *The Final Frontier*  
Authority: Requirements 9.6, 12.1, 12.4, 12.5, 12.6, and 14.1 through 14.14; the design data models; and binding author decisions through `DEC-016`

This document defines storage and validation contracts. It does **not** populate the Canon Bible, Arc Outline, roster, ledger, baseline, or any other planning record. Every object below uses an `EXAMPLE` identifier or is explicitly an illustrative fixture; examples have no continuity authority.

Normative words `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` have their ordinary specification meanings.

## Persistence and parsing contract

### Typed JSON fences

Planning documents store machine-readable records in typed fenced JSON blocks. The opening fence MUST be at column zero and have this exact information-string shape:

`json record=<RecordType> schema=1`

The closing fence MUST be exactly three backticks at column zero. `<RecordType>` MUST be one of the sixteen record types defined below. The JSON body MUST be either:

1. one JSON object representing one record; or
2. a nonempty JSON array whose members are all objects of the named record type.

The type comes from `record=<RecordType>` in the fence, never from a nearby heading, prose label, filename, or guessed field set. A checker SHALL ignore ordinary Markdown commentary for record values and SHALL NOT use commentary to repair, complete, or override a fenced record.

JSON parsing is strict:

- UTF-8 input only;
- standard JSON strings, numbers, booleans, arrays, objects, and `null` only;
- no comments, trailing commas, `NaN`, `Infinity`, duplicate object keys, or concatenated top-level values;
- duplicate keys MUST be detected rather than silently keeping the first or last value;
- every record is closed to unknown fields unless this document explicitly declares an open JSON-value field;
- nested objects are likewise closed to unknown fields;
- an unknown record type or unsupported schema version is a malformed required input.

A parser SHALL retain the document path, fence ordinal, array index when applicable, and source line range so diagnostics can identify the exact malformed record.

### Chapter Header storage exception

A real Chapter Header is not stored in a planning-document JSON fence. It is the restricted delimited block at the very beginning of a Chapter File:

- the first physical line MUST be `---`;
- the next lines contain exactly the nine keys defined by `ChapterHeader`, one key per line;
- the next line containing only `---` closes the header;
- no second header block, duplicate key, unknown key, multiline value, YAML anchor/tag, or value inferred from prose is permitted;
- everything after the closing delimiter is the Prose Body;
- if either delimiter is missing or ambiguous, word counting and semantic validation for that file MUST stop with an incomplete-input diagnostic.

The checker parses this restricted header into the logical nine-key JSON object shown in the `ChapterHeader` section. The fenced JSON example exists for fixtures and schema verification only.

### Common types

| Type name | JSON representation | Validation |
|---|---|---|
| `NonBlankString` | string | After Unicode trimming, length is at least one. |
| `SingleLineString` | string | `NonBlankString` with no CR or LF. |
| `StableID` | string | Uppercase ASCII identifier beginning with a letter and containing at least one hyphen; pattern `^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$`. IDs are immutable and never reused for another entity. |
| `ChapterNumber` | integer | At least 1; booleans do not count as integers. |
| `WorkspacePath` | string | POSIX-style, workspace-relative, no leading slash, `.` segment, `..` segment, backslash, or empty segment. Resolution MUST remain under the workspace root. |
| `ISODate` | string | Calendar date `YYYY-MM-DD`. |
| `Timestamp` | string | RFC 3339 timestamp with an explicit offset; normalized checker output SHOULD use UTC `Z`. |
| `Movement` | string enum | Exactly `discovery_part`, `private_defense_part`, `mindwars_part`, or `aftermath_coda`. |
| `LengthClass` | string enum | Exactly `microchapter`, `normal`, or `long-outlier`. |
| `ChapterStatus` | string enum | Exactly `planned`, `exploratory`, `draft`, `revised`, `approved`, or `final`. |
| `RecordRef` | object | Exactly `record_type` and `record_id`; both nonblank, and `record_type` names one defined record type. The target MUST resolve uniquely in the requested project snapshot. |

A `RecordRef` has this logical shape when used below: `{"record_type": "TimelineEntry", "record_id": "TL-EXAMPLE-001"}`.

### Null, absence, and collection rules

Required means the key MUST be present even when its value is conditionally inapplicable.

- A conditionally inapplicable scalar or object is JSON `null` only when its field definition explicitly permits `null`.
- An applicable but currently empty collection is `[]`.
- A Chapter Header with no motifs uses `"motif_events": []`.
- An `ArcEntry` with no Cross Cut uses the exact string `"none"` in `cross_cuts`, as required by the Arc Outline contract. No other field uses the string `"none"` as an absence marker.
- Empty strings, whitespace-only strings, `"N/A"`, `"unknown"`, `0` as a sentinel, and omitted required keys are invalid absence representations.
- Unknown facts are represented by an explicit enum such as `unresolved` or by an explanatory uncertainty field, never by dropping a required key.
- Array members MUST have the declared type. Arrays described as sets MUST contain no duplicates after normalization.

### Identity, references, and validation order

Within one requested project snapshot:

1. Parse every requested input without inference.
2. Validate each record structurally: keys, types, enums, nullability, and conditional fields.
3. Build indexes for stable IDs, chapter numbers, filenames, and other declared unique keys.
4. Reject duplicate identities before resolving references.
5. Resolve every required reference to exactly one target of the required type.
6. Evaluate cross-record agreement and scope-specific invariants.
7. Emit diagnostics without modifying source files.

A missing, unreadable, malformed, duplicate-identity, or structurally incomplete required input makes the requested gate `incomplete` and maps to checker exit status `2`. A complete readable scope with one or more objective semantic violations maps to `revision` and exit status `1`. Only a complete readable scope with zero objective violations maps to `pass` and exit status `0`.

The checker is read-only. It MUST NOT rewrite counts, metadata, names, IDs, statuses, or prose. It MUST NOT infer objective record values from commentary. It also MUST NOT produce pass/fail judgments for prose voice, originality, sentence artistry, emotional tone, Hook quality, POV distinctness, tenderness, restraint, rhetorical force, or emotional truth.

### Character ID registry

Several fields carry Character IDs: `POVProfile.character_id`, each `POVProfile.relationships[].character_id`, `TimelineEntry.participants`, `PairState.participants`, `PairState.calibration_participants`, `CancelState.individual_consent.character_id`, and the `Reveal` knowledge arrays. This section states where such an ID is authoritatively declared, so that a reference to a person who holds no viewpoint resolves instead of dangling.

Within one requested project snapshot the authoritative Character ID set is the **union** of:

1. every `POVProfile.character_id`; and
2. the Character ID declared by every `NovelExtension` whose `extension_kind` is `character-name` and whose `state` is `approved`.

For rule 2 the declaration is machine-readable from the record itself: a `character-name` extension's `fact` MUST begin with the declared Character ID as its first whitespace-delimited token, and that token MUST satisfy `StableID`. A checker reads the ID from that record field only. It MUST NOT take a Character ID from a heading, table, list, sentence of commentary, or any other prose. A `provisional` extension declares no resolvable ID yet, and a `retired` one declares none any longer.

Every Character ID reference MUST resolve to exactly one member of the union. One ID declared both by a `POVProfile` and by a `character-name` extension is one character, not two, and the extension MUST agree with the profile's `selected_name`. A reference resolving to no member is a dangling reference, and two different characters sharing one ID is a duplicate identity; both are caught in validation order steps 4 and 5.

A Character ID with **no** `POVProfile` is a valid **non-viewpoint character**. It creates no POV, no `pov_id`, no `VoiceBrief` obligation, no `movement_coverage`, and no roster load, and it may appear in `participants` arrays, consent objects, and relationship targets like any other Character ID. Holding an ID licenses no narration from inside that person: viewpoint architecture, the roster profile count, and the Anchor rule are governed by `POVProfile` records alone. A non-viewpoint character MUST NOT be used to represent the Foreign Signal or any actual, alleged, or hypothesized sender, and adding one is never a route around the `POVProfile` invariants below.

## Canon authority constants and boundaries

### Exact `DEC-014` Canon Source set

For `CanonFact.authority_basis = "lyric"`, `source_path` MUST resolve to exactly one member of this closed set:

1. `songs/The Synaptic Frontier.md`
2. `songs/Faraday.md`
3. `songs/The Final Frontier.md`
4. `songs/The Radius.md`
5. `songs/Case Zero.md`

No sixth path is allowed. In particular, `songs/One-Time Pad.md` MUST be rejected as a Canon Source and MUST NOT supply a lyric-authority Canon Fact, continuity obligation, or Literal Phrase Constraint.

### Lyric, testimony, and advisory boundaries

- Lyric text in the five paths above may support `authority_basis: "lyric"`.
- First-person lyric testimony remains binding **as the attributed speaker's canonical account**. It is not silently converted into omniscient proof of causation, another person's interior state, or an institution's objective conclusion.
- For *Case Zero*, the binding same-speaker testimony and its first-person details remain distinct from `DEC-002`'s proper-name, person-specific-address, and later-bench-path mapping. Neither layer confirms that the later handshake caused Nia's wanting.
- Production notes, style prompts, exclude-style prompts, generation workflow, credits, and rights metadata are advisory/non-story. Citation alone cannot make any of them a `CanonFact`.
- Such material MAY appear only in `supporting_advisory_citations` with `classification: "advisory-non-story"`, or as the primary note source of a `ratified-note` Canon Fact that also supplies a resolvable higher-tier adoption.
- A `ratified-note` receives authority from its adopting author decision or approved requirement, not from the note itself.
- The contradictory *Case Zero* rights footer remains non-story rights-review metadata; publication and canon status do not turn it into a story fact or legal conclusion.

### Literal scan boundary

Every `LiteralPhraseConstraint` has `scan_scope: "chapter-prose-body-only"`. Literal matching occurs only in Chapter File Prose Bodies after the closing Chapter Header delimiter. Song files—including all five Canon Sources—planning documents, headers, front matter, schema examples, editorial notes, and checker output are outside literal scan scope. *Case Zero* lyric occurrences therefore neither satisfy nor violate a Chapter File phrase constraint.

---

## 1. `ChapterHeader`

**Purpose:** the exact machine-readable metadata block for one Chapter File.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `movement` | `Movement` | yes | Agrees with directory, filename, and `ArcEntry`. |
| `chapter` | `ChapterNumber` | yes | Global sequence; does not reset by movement. |
| `pov_id` | `StableID` | yes | Resolves to exactly one `POVProfile.pov_id`. |
| `timeline_id` | `StableID` | yes | Resolves to exactly one `TimelineEntry.timeline_id`. |
| `motif_events` | array of `StableID` | yes | Unique items; every item resolves to a `MotifEvent` assigned to this chapter. Empty is `[]`. |
| `hook` | `SingleLineString` | yes | Describes the intended final-beat pull; quality remains editorial. |
| `words` | integer | yes | At least 0 and exactly equals whitespace-token count of the Prose Body. |
| `length_class` | `LengthClass` | yes | Derived from observed words: below 700, 700–1,600, or 1,601–2,500. |
| `status` | `ChapterStatus` | yes | Agrees with the matching `ArcEntry`; substantive edits demote `approved`/`final` to `revised`. |

### Invariants

The key set is **exactly** the nine keys above: no discriminator, schema key, title, Cross Cut key, record note, or unknown extension may appear. Each key occurs exactly once. No value may be `null`. Counts above 2,500 are invalid regardless of the declared class.

```json record=ChapterHeader schema=1
{
  "movement": "aftermath_coda",
  "chapter": 124,
  "pov_id": "POV-MARA",
  "timeline_id": "TL-EXAMPLE-CODA-VISIT",
  "motif_events": [
    "MOT-COME-04",
    "MOT-KETTLE-02"
  ],
  "hook": "The machine is refused and an ordinary human response begins.",
  "words": 1040,
  "length_class": "normal",
  "status": "exploratory"
}
```

## 2. `ArcEntry`

**Purpose:** one and only one planned outline record for a Chapter File.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `chapter` | `ChapterNumber` | yes | Unique and contiguous from 1 across the complete outline. |
| `filename` | `WorkspacePath` | yes | Unique; basename follows `<movement>-<three-digit-sequence>-<slug>.md`. |
| `movement` | `Movement` | yes | Exactly one movement and agrees with path/header. |
| `timeline_id` | `StableID` | yes | Resolves uniquely to `TimelineEntry`. |
| `pov_id` | `StableID` | yes | Resolves uniquely to `POVProfile`. |
| `purpose` | `SingleLineString` | yes | One-sentence narrative function. |
| `hook` | `SingleLineString` | yes | Agrees textually with the Chapter Header when the file exists. |
| `cross_cuts` | `"none"` or array of `StableID` | yes | IDs resolve to `CrossCut`; array is nonempty and duplicate-free. |
| `motif_events` | array of `StableID` | yes | Set agrees with the chapter's header and all applicable `MotifEvent` records. |
| `estimated_length_class` | `LengthClass` | yes | Planning class. |
| `estimated_words` | integer or `null` | yes | Planning Prose_Word estimate. When non-null it is 1–2500 inclusive and lies inside the band of `estimated_length_class`. MUST be non-null when the entry belongs to a same-POV run of two or more chapters, because the run word limit cannot be evaluated from a length class alone; MAY be `null` for a single-chapter run, which the Hard_Chapter_Maximum already bounds. |
| `outlier_purpose` | `SingleLineString` or `null` | yes | Non-null for either outlier class; null for `normal`. |
| `status` | `ChapterStatus` | yes | Agrees with header when a file exists. |
| `calibration_selected` | boolean | yes | Marks the 6–8 chapter Calibration Batch. |
| `representative_purpose` | `SingleLineString` or `null` | yes | Required when calibration-selected outside the opening sequence; otherwise null is permitted. |
| `record_horizon` | object | yes | Exactly `through_timeline_id` and `knowledge_limit`. Timeline ref resolves; limit is a `NonBlankString`. |
| `reveal_ids` | array of `StableID` | yes | Unique `Reveal.reveal_id` references. Empty is `[]`. |

### Invariants

`chapter` and `filename` are independently unique. Complete-scope entries form an uninterrupted sequence beginning at 1 and four contiguous movement blocks in the required order. Each Cross Cut ID is declared by the corresponding `CrossCut` and every participant's `ArcEntry`. No purpose, Hook, or reveal may rely on knowledge later than `record_horizon`. No more than three consecutive entries may use one `pov_id`, and no same-POV run may exceed 3,600 combined Prose_Words. A same-POV run is a maximal uninterrupted sequence of entries sharing one `pov_id`, counted on the global chapter sequence so movement boundaries count like any other adjacency. Planning evaluates the run total from `estimated_words`, so every entry in a run of two or more chapters requires a non-null value; the completed manuscript evaluates it from each `ChapterHeader.words`. The two limits are independent and both bind: a legal three-chapter run may still violate the word limit, and a two-chapter run may violate it as well.

```json record=ArcEntry schema=1
{
  "chapter": 124,
  "filename": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
  "movement": "aftermath_coda",
  "timeline_id": "TL-EXAMPLE-CODA-VISIT",
  "pov_id": "POV-MARA",
  "purpose": "Mara affirms Safiya's consent but refuses a counterfeit restoration and turns toward truthful presence.",
  "hook": "The machine is refused and an ordinary human response begins.",
  "cross_cuts": "none",
  "motif_events": [
    "MOT-COME-04",
    "MOT-KETTLE-02"
  ],
  "estimated_length_class": "normal",
  "estimated_words": 1180,
  "outlier_purpose": null,
  "status": "exploratory",
  "calibration_selected": true,
  "representative_purpose": "Tests Mara's truth-based refusal, Coda Turn, and Refused Swell.",
  "record_horizon": {
    "through_timeline_id": "TL-EXAMPLE-CODA-VISIT",
    "knowledge_limit": "Mara knows Safiya's request and loss but has no later threshold knowledge."
  },
  "reveal_ids": []
}
```

## 3. `POVProfile`

**Purpose:** the stable one-to-one Character/POV mapping and the viewpoint's material narrative function.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `character_id` | `StableID` | yes | Unique across profiles. |
| `pov_id` | `StableID` | yes | Unique across profiles and one-to-one with `character_id`. |
| `selected_name` | `NonBlankString` | yes | Maps to exactly this Character ID. Name quality/capitalization is not scored. |
| `aliases` | array of `NonBlankString` | yes | Unique after Unicode normalization; every alias maps to only this character. |
| `entity_type` | string enum | yes | Exactly `human`; signal/adversary POVs are invalid. |
| `anchor` | boolean | yes | Exactly one final profile is true. |
| `knowledge_position` | `NonBlankString` | yes | What this POV can materially know. |
| `moral_pressure` | `NonBlankString` | yes | Distinct ethical pressure. |
| `plot_function` | `NonBlankString` | yes | Distinct structural work. |
| `relationships` | array of objects | yes | Each object is exactly `character_id` and `relationship`; target resolves, description is nonblank. |
| `blind_spots` | array of `NonBlankString` | yes | Nonempty. |
| `reason_to_narrate` | `NonBlankString` | yes | Why this testimony belongs in the record. |
| `movement_coverage` | array of `Movement` | yes | Unique, nonempty, and agrees with Arc assignments. |
| `provisional_load` | object | yes | Exactly four movement integer counts plus `total`; all nonnegative and sum to total. |
| `voice_brief_id` | `StableID` | yes | Resolves one-to-one to `VoiceBrief`. |

### Invariants

The final roster contains 3–5 profiles, all human. **Across `POVProfile` records** the `character_id` and `pov_id` values form a bijection: one profile per character, one character per profile, and no POV without a character. The bijection is a rule about profiles and never about the [Character ID registry](#character-id-registry) as a whole, so a non-viewpoint Character ID with no profile does not violate it and creates no missing `pov_id`. Exactly one Anchor has at least one chapter in all four movements. No profile may represent the Foreign Signal or any actual, alleged, or hypothesized sender. Two profiles with the same combined knowledge, moral pressure, and plot function require editorial consolidation before baseline approval.

```json record=POVProfile schema=1
{
  "character_id": "CHAR-001",
  "pov_id": "POV-MARA",
  "selected_name": "Mara Venn",
  "aliases": [],
  "entity_type": "human",
  "anchor": true,
  "knowledge_position": "Finder, private defender, counterphase lead, and person responsible for the null decision.",
  "moral_pressure": "She must accept responsibility without converting other people's injuries into proof about herself.",
  "plot_function": "Owns technical discovery and the four movement turns without narrating another person's interior harm.",
  "relationships": [
    {
      "character_id": "CHAR-002",
      "relationship": "Collaborator and moral check whose account Mara cannot own."
    }
  ],
  "blind_spots": [
    "Names a system before naming a feeling.",
    "Treats private guilt as if intensity could make it evidence."
  ],
  "reason_to_narrate": "To preserve scientific truth and eventually enter evidence against herself.",
  "movement_coverage": [
    "discovery_part",
    "private_defense_part",
    "mindwars_part",
    "aftermath_coda"
  ],
  "provisional_load": {
    "discovery_part": 14,
    "private_defense_part": 14,
    "mindwars_part": 21,
    "aftermath_coda": 7,
    "total": 56
  },
  "voice_brief_id": "VOICE-MARA"
}
```

## 4. `VoiceBrief`

**Purpose:** qualitative drafting guidance for one POV, never an automated prose score.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `voice_brief_id` | `StableID` | yes | Unique. |
| `pov_id` | `StableID` | yes | Resolves uniquely and one-to-one to a `POVProfile`. |
| `syntax_rhythm` | `NonBlankString` | yes | Qualitative tendencies only. |
| `image_sensory_families` | array of `NonBlankString` | yes | Nonempty. |
| `emotional_distance` | `NonBlankString` | yes | Characteristic relation to events. |
| `omission_evasion_delayed_notice` | array of `NonBlankString` | yes | Nonempty. |
| `reverb_profile` | object | yes | Exactly `name` and `expectations`, both nonblank qualitative strings. |
| `movement_evolution` | array of objects | yes | Each is exactly `movement` and `evolution`; movement unique and agrees with profile coverage. |
| `coda_turn` | object or `null` | yes | If present: exactly `chapter`, `before`, `trigger`, `after`; chapter resolves to this POV. |
| `calibration_evidence` | array of objects | yes | Each has exactly `date`, `editorial_finding_ids`, and `result` (`pass` or `revision`). |
| `first_appearance_review` | object or `null` | yes | If present: same three fields plus `chapter`; supports Requirement 5.11. |

### Invariants

No numeric sentence-length target, vocabulary quota, style score, sentiment score, or automated quality threshold is allowed. Calibration and first-appearance results reference human `EditorialFinding` records. A POV added later must have a complete brief before its first Prose Body is drafted.

```json record=VoiceBrief schema=1
{
  "voice_brief_id": "VOICE-MARA",
  "pov_id": "POV-MARA",
  "syntax_rhythm": "Controlled analytic clauses qualify uncertainty, then land on a plain assertion; fear strips away qualification.",
  "image_sensory_families": [
    "fields and harmonics",
    "thresholds and pressure",
    "copper mesh and bone conduction"
  ],
  "emotional_distance": "She initially converts awe and guilt into mechanism and scale.",
  "omission_evasion_delayed_notice": [
    "Mostly leaves her high handshake-causation conviction unvoiced.",
    "Notices hands, thirst, fatigue, and domestic objects late."
  ],
  "reverb_profile": {
    "name": "Cathedral-to-room-tone",
    "expectations": "Main-Part acts echo into doctrine; after the Coda Turn, concrete actions remain unexpanded."
  },
  "movement_evolution": [
    {
      "movement": "discovery_part",
      "evolution": "Spacious curiosity becomes increasingly ashamed without turning private conviction into proof."
    },
    {
      "movement": "private_defense_part",
      "evolution": "Copper-lined singular argument tests whether refusal can remain private."
    },
    {
      "movement": "mindwars_part",
      "evolution": "A temporary public collective register is broken by the null."
    },
    {
      "movement": "aftermath_coda",
      "evolution": "Cathedral-scale explanation dries into water, chair, breath, listening, and waiting."
    }
  ],
  "coda_turn": {
    "chapter": 124,
    "before": "Mechanism and confession expand toward doctrine.",
    "trigger": "The relay is switched off before the kettle goes on.",
    "after": "Attention narrows to truthful human presence."
  },
  "calibration_evidence": [],
  "first_appearance_review": null
}
```

## 5. `TimelineEntry`

**Purpose:** one stable chronology point or interval, including technical and record-custody distinctions required for continuity.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `timeline_id` | `StableID` | yes | Unique. Shared chronology uses one ID. |
| `chronology_kind` | string enum | yes | Exactly `point` or `interval`. |
| `canon_status` | string enum | yes | Exactly `binding-canon`, `novel-extension`, or `mixed`. |
| `relative_chronology` | `NonBlankString` | yes | Human-readable ordering statement. |
| `exact_time` | `SingleLineString` or `null` | yes | Null when canon does not supply an exact value. |
| `duration` | `SingleLineString` or `null` | yes | Null when not applicable or unestablished. |
| `location` | `SingleLineString` or `null` | yes | Stable selected name or deliberate descriptive reference. |
| `participants` | array of `StableID` | yes | Unique Character IDs; empty only when no person is established. |
| `chapter_numbers` | array of `ChapterNumber` | yes | Unique and sorted ascending. |
| `fact_refs` | array of `RecordRef` | yes | Targets are `CanonFact` or `NovelExtension`. |
| `uncertainty_notes` | array of `NonBlankString` | yes | Empty only when no chronology uncertainty needs protection. |
| `record_chronology` | object or `null` | yes | If present: exactly `composition_timeline_id`, `deposit_timeline_id`, `release_timeline_ids`; nullable refs and unique array refs. |
| `technical_state` | object or `null` | yes | If present, uses the strict technical-state fields below. |
| `cross_cut_ids` | array of `StableID` | yes | Unique `CrossCut` references. |

`technical_state` contains exactly:

- `mode`: `RECEIVE`, `INTRUDE`, `CANCEL`, `PAIR`, or `not-applicable`;
- `source_side_continuity`: `continuous`, `discontinuous`, `unknown`, or `not-applicable`;
- `receiver_offset_seconds`: nonnegative integer or `null`;
- `apparatus_mode`: `receive-only`, `bench-transmit`, `bidirectional-architecture`, or `not-applicable`;
- `transmit_stage_present`: boolean or `null`;
- `person_specific_address_state`: `unidentified`, `identified`, `locked`, `reused`, or `not-applicable`;
- `cancel_state`: the `CancelState` object below, or `null` when `mode` is not `CANCEL`;
- `pair_state`: the `PairState` object below, or `null` when `mode` is not `PAIR`;
- `pairing_evidence`: the `PairingEvidence` object below, or `null` when `mode` is not `PAIR`;
- `evidence_scope`: `NonBlankString` stating what the entry does and does not prove.

#### `mode` and the four-mode invariants

`mode` is the single authoritative classification required by the four-mode mechanism authority. It is never inferred from `apparatus_mode`, prose commentary, or a nearby heading. Exactly one value applies per entry, and the following closed invariants MUST hold.

| `mode` | Required state |
|---|---|
| `RECEIVE` | `transmit_stage_present` is `false`; `source_side_continuity` is `continuous`; `cancel_state`, `pair_state`, and `pairing_evidence` are `null`. |
| `INTRUDE` | `transmit_stage_present` is `true`; `person_specific_address_state` is one of `identified`, `locked`, or `reused`; `cancel_state`, `pair_state`, and `pairing_evidence` are `null`. |
| `CANCEL` | `transmit_stage_present` is `true`; `person_specific_address_state` is exactly `not-applicable`; `cancel_state` is non-null; `pair_state` and `pairing_evidence` are `null`. |
| `PAIR` | `transmit_stage_present` is `true`; `pair_state` and `pairing_evidence` are non-null; `cancel_state` is `null`. |
| `not-applicable` | The entry records no neural communication event; `cancel_state`, `pair_state`, and `pairing_evidence` are `null`. |

`INTRUDE` requires an address and `CANCEL` forbids one. That is the structural boundary between them, and it is why an unaddressed subtractive event MUST NOT be recorded as `INTRUDE`.

#### `CancelState`

`cancel_state` contains exactly:

- `scope`: `bounded-local` or `area-scale`;
- `individual_consent`: object with exactly `character_id`, `current`, `specific_act`, and `revocable`, or `null`. Required non-null when `scope` is `bounded-local`; MUST be `null` when `scope` is `area-scale`.
- `institutional_authorization`: `NonBlankString` naming the authorizing body and instrument, or `null`. Required non-null when `scope` is `area-scale`; MUST be `null` when `scope` is `bounded-local`.
- `subtraction`: `NonBlankString` describing the removal or degradation of access to mental content or faculties;
- `inserted_content`: string enum, exactly `none`;
- `affected_set_predictable_before`: boolean, exactly `false`;
- `affected_set_enumerable_during`: boolean, exactly `false`;
- `affected_set_fully_mapped_after`: boolean, exactly `false`;
- `additive_inverse_exists`: boolean, exactly `false`;
- `provenance_yield`: string enum, exactly `none`.

`CancelState` invariants: `bounded-local` describes a field volume containing one deliberately exposed consenting individual, not cancellation targeted at that person. The owning `TimelineEntry` MUST have every `chapter_numbers` member inside the Mindwars movement block; the three affected-set booleans and `additive_inverse_exists` MUST be `false`; `inserted_content` and `provenance_yield` MUST be `none`; and area-scale authorization MUST NOT be represented as individual consent collected from every affected person. A record asserting a reversal, an enumerated affected set, an inserted payload, a person-specific address, a non-Mindwars chapter, or provenance derived from cancelling a pattern is invalid.

#### `PairState`

`pair_state` contains exactly:

- `participants`: array of exactly two `StableID` Character IDs, both living at the entry's chronology;
- `consent`: object with exactly `current`, `specific_act`, `revocable`, `authorized_a`, and `authorized_b`; all booleans true and `specific_act` nonblank for an authorized session;
- `calibration_id`: `StableID` unique to that pair;
- `calibration_participants`: array of exactly two `StableID` values that MUST equal `participants` as a set;
- `calibration_transferable`: boolean, exactly `false`;
- `deliberate_send_state`: `required`, `paused`, `revoked`, or `integrity-failed`.

`PairState` invariants: exactly two living participants; `calibration_participants` matches `participants`; calibration is never transferable and never resolves to a dead or absent person, simulation, archive, model, or reconstruction; and `paused`, `revoked`, or `integrity-failed` states carry no transported semantic content in the same or a later event without an explicit recorded confirmation, retry, or ordinary-speech fallback.

#### `PairingEvidence`

`pairing_evidence` contains exactly:

- `consent_state_metadata_present`: boolean, exactly `true`;
- `transport_metadata_present`: boolean, exactly `true`;
- `metadata_semantically_opaque`: boolean, exactly `true`;
- `content_recording_enabled`: boolean, default and initial value `false`;
- `recording_consent_a`: boolean;
- `recording_consent_b`: boolean;
- `transcript`: object with exactly `transcript_id`, `session_timeline_id`, and `content_scope`, or `null`.

`PairingEvidence` invariants: consent-state and transport metadata are mandatory and semantically opaque, so no record may claim semantic reconstruction from them; `content_recording_enabled` is `true` only when `recording_consent_a` and `recording_consent_b` are both `true`; `transcript` is non-null only when `content_recording_enabled` is `true`; `session_timeline_id` MUST equal the owning entry's `timeline_id`; and `content_scope` MUST be limited to contributions transported by the protocol during that recorded session, never truth, intent, memory provenance, unoffered thought, or a complete mental state.

#### Conformance of pre-amendment records

These `technical_state` fields were added by the 2026-09-11 amendment to the mechanism authority. A `TimelineEntry` written before that amendment omits `mode`, `cancel_state`, `pair_state`, and `pairing_evidence` and is therefore structurally incomplete under this schema version. Such a record MUST be brought into conformance when its owning numbered task executes; a checker encountering one reports incomplete input rather than inferring a mode.

### Invariants

The December source interval, later bench transmission, page-nine architecture, Trust formation, record composition, later deposit, release, null-night braid, and Coda visit must use distinct chronology where the design requires it. In particular, an eventual December entry must encode `mode: RECEIVE`, a continuous source side, eight-second receiver offset, receive-only apparatus, and no transmit stage; a later entry carries `mode: INTRUDE` for the bench transmit path. Page nine cannot retroactively supply a December transmit event. Trust formation follows alteration of the April record; pre-Trust composition and later deposit remain separate.

The bounded counterphase test and every null-night entry must encode `mode: CANCEL` with a populated `cancel_state`. No entry may record the null as `INTRUDE`, and no entry may record a `CANCEL` effect as reversible.

```json record=TimelineEntry schema=1
{
  "timeline_id": "TL-EXAMPLE-DECEMBER-RECEIVE",
  "chronology_kind": "interval",
  "canon_status": "mixed",
  "relative_chronology": "A continuous December source-side morning observed by Mara through a receive-only apparatus.",
  "exact_time": null,
  "duration": "twenty minutes in the speaker's attributed account",
  "location": "Northline Array and the source-side morning",
  "participants": [
    "CHAR-001",
    "CHAR-002"
  ],
  "chapter_numbers": [
    1,
    2,
    3,
    4,
    5
  ],
  "fact_refs": [],
  "uncertainty_notes": [
    "This fixture does not establish the cause of any later wanting."
  ],
  "record_chronology": null,
  "technical_state": {
    "mode": "RECEIVE",
    "source_side_continuity": "continuous",
    "receiver_offset_seconds": 8,
    "apparatus_mode": "receive-only",
    "transmit_stage_present": false,
    "person_specific_address_state": "locked",
    "cancel_state": null,
    "pair_state": null,
    "pairing_evidence": null,
    "evidence_scope": "The receiver observes an offset and address lock; this is not a transmission event."
  },
  "cross_cut_ids": [
    "CUT-EXAMPLE-OPENING"
  ]
}
```

The following illustrative fixture shows an area-scale `CANCEL` entry. It has no continuity authority.

```json record=TimelineEntry schema=1
{
  "timeline_id": "TL-EXAMPLE-CANCEL-AREA",
  "chronology_kind": "interval",
  "canon_status": "mixed",
  "relative_chronology": "An example area-scale cancellation interval inside the Mindwars movement.",
  "exact_time": null,
  "duration": null,
  "location": "An affected area canonically described as three counties wide",
  "participants": [
    "CHAR-001"
  ],
  "chapter_numbers": [
    104
  ],
  "fact_refs": [],
  "uncertainty_notes": [
    "This fixture identifies no affected individual and supplies no provenance."
  ],
  "record_chronology": null,
  "technical_state": {
    "mode": "CANCEL",
    "source_side_continuity": "not-applicable",
    "receiver_offset_seconds": null,
    "apparatus_mode": "bidirectional-architecture",
    "transmit_stage_present": true,
    "person_specific_address_state": "not-applicable",
    "cancel_state": {
      "scope": "area-scale",
      "individual_consent": null,
      "institutional_authorization": "Emergency defensive authorization issued by the civil authority; not individual consent from affected persons.",
      "subtraction": "Removal or degradation of access to some mental content and faculties among an unknown set of people within the field volume.",
      "inserted_content": "none",
      "affected_set_predictable_before": false,
      "affected_set_enumerable_during": false,
      "affected_set_fully_mapped_after": false,
      "additive_inverse_exists": false,
      "provenance_yield": "none"
    },
    "pair_state": null,
    "pairing_evidence": null,
    "evidence_scope": "The cancellation silences an incoming pattern and subtracts access; it identifies no sender, enumerates no affected person, and cannot be reversed."
  },
  "cross_cut_ids": []
}
```

## 6. `CrossCut`

**Purpose:** one reciprocal relationship among chapters sharing chronology, consequence, or withheld disclosure while contributing distinct narrative value.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `cross_cut_id` | `StableID` | yes | Unique. |
| `chapters` | array of `ChapterNumber` | yes | At least two unique existing chapters, sorted ascending. |
| `shared_timeline_id` | `StableID` or `null` | yes | Resolves when non-null. |
| `shared_reveal_id` | `StableID` or `null` | yes | Resolves when non-null. |
| `shared_consequence` | `NonBlankString` or `null` | yes | At least one of timeline, reveal, or consequence is non-null. |
| `handoff_mode` | string enum | yes | `sensory-match`, `causal-cut`, `contradiction-cut`, `threshold-cut`, `temporal-braid`, or `delayed-return`. |
| `material_narrative_value` | array of objects | yes | Exactly one object per chapter; each is `chapter` plus nonblank `value`. |
| `replay_boundary` | `NonBlankString` | yes | States what may repeat and where the next account begins. |
| `declared_by_chapters` | array of `ChapterNumber` | yes | Set must equal `chapters`. |

### Invariants

Every participating `ArcEntry.cross_cuts` array contains this ID, and no nonparticipant declares it. A one-sided or dangling relationship fails. Repeated scene time is valid only when each `material_narrative_value` is distinct; the checker validates declarations and references, while a human reviews whether the distinction is artistically real.

```json record=CrossCut schema=1
{
  "cross_cut_id": "CUT-EXAMPLE-OPENING",
  "chapters": [
    1,
    2
  ],
  "shared_timeline_id": "TL-EXAMPLE-DECEMBER-RECEIVE",
  "shared_reveal_id": null,
  "shared_consequence": "A waveform feature in the receiver is handed to the uninterrupted source-side sensory detail.",
  "handoff_mode": "sensory-match",
  "material_narrative_value": [
    {
      "chapter": 1,
      "value": "Mara establishes instrument structure without knowing the source person."
    },
    {
      "chapter": 2,
      "value": "Nia supplies the continuous lived morning without experiencing an offset."
    }
  ],
  "replay_boundary": "Chapter 2 begins from the matched ordinary sound and does not replay Mara's measurement.",
  "declared_by_chapters": [
    1,
    2
  ]
}
```

## 7. `CanonFact`

**Purpose:** one binding canon proposition with explicit authority, source location, epistemic scope, and implications.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `canon_id` | `StableID` | yes | Unique. |
| `authority_basis` | string enum | yes | Exactly `author-decision`, `requirement`, `lyric`, or `ratified-note`. |
| `source_path` | `WorkspacePath` | yes | Must be valid for the selected authority; lyric paths use the closed five-path set. |
| `source_location` | `NonBlankString` | yes | Decision/requirement identifier or precise lyric/note location; file path alone is insufficient. |
| `source_material_class` | string enum | yes | `author-decision`, `requirement`, `lyric`, `production-note`, `style-prompt`, `exclude-prompt`, `generation-workflow`, `credits`, or `rights-metadata`. |
| `adopted_by` | object or `null` | yes | Required only for `ratified-note`; exactly `authority_type`, `authority_id`, `source_path`, `source_location`. |
| `statement` | `NonBlankString` | yes | Canonical proposition at the authority's actual epistemic scope. |
| `first_person_testimony` | boolean | yes | Controls the required attribution fields. |
| `speaker` | `NonBlankString` or `null` | yes | Required for first-person lyric testimony; null otherwise unless attribution remains material. |
| `attribution` | `NonBlankString` or `null` | yes | Required for first-person testimony; says whose account it is. |
| `epistemic_limitation` | `NonBlankString` or `null` | yes | Required for first-person testimony; states what the account does not prove. |
| `truth_scope` | string enum | yes | Exactly `authoritative-proposition`, `attributed-testimony`, or `ratified-proposition`. |
| `binding_implications` | array of `NonBlankString` | yes | Nonempty. |
| `protected_ambiguities` | array of `NonBlankString` | yes | Empty only if no ambiguity must remain. |
| `protected_wording` | `SingleLineString` or `null` | yes | Does not itself create a literal scan rule; that requires `LiteralPhraseConstraint`. |
| `affected_timeline_ids` | array of `StableID` | yes | Unique refs; may be empty before timelines are assigned. |
| `affected_chapters` | array of `ChapterNumber` | yes | Unique, sorted; may be empty before the Arc exists. |
| `supporting_advisory_citations` | array of objects | yes | Each object is exactly `source_path`, `source_location`, `material_class`, `classification`, `note`; classification is exactly `advisory-non-story`. |

### Authority matrix and conditional validation

| `authority_basis` | Required source class | `adopted_by` | Additional validation |
|---|---|---|---|
| `author-decision` | `author-decision` | `null` | Location resolves to a binding, nonsuperseded decision. |
| `requirement` | `requirement` | `null` | Location resolves to an approved requirement/design decision. |
| `lyric` | `lyric` | `null` | Path is exactly one of the five `DEC-014` Canon Sources. |
| `ratified-note` | one of the note/metadata classes | required | Adoption resolves to either a binding author decision or approved requirement that adopts this specific proposition. |

For `first_person_testimony: true`, `speaker`, `attribution`, and `epistemic_limitation` are non-null and `truth_scope` MUST be `attributed-testimony`. The schema has no `omniscient` truth scope. A *Case Zero* record may bind what Nia reports while still prohibiting causal proof. Its Nia name/mechanism mapping cites `DEC-002` separately; lyric authority alone cannot manufacture that mapping.

A Production Note, style/exclude prompt, generation workflow item, credit, or rights line with no valid `adopted_by` record MUST NOT be encoded as a Canon Fact. It may only be a supporting advisory citation or ordinary commentary. Even a valid advisory citation contributes no binding implication by itself.

```json record=CanonFact schema=1
{
  "canon_id": "CF-EXAMPLE-CASE-ZERO-OFFSET",
  "authority_basis": "lyric",
  "source_path": "songs/Case Zero.md",
  "source_location": "Lyric: first-person account of the December receiver offset",
  "source_material_class": "lyric",
  "adopted_by": null,
  "statement": "The first-person speaker reports that the receiver owned the eight-second offset and that she experienced no source-side gap.",
  "first_person_testimony": true,
  "speaker": "CHAR-002",
  "attribution": "Binding as Nia's report; the proper-name mapping to CHAR-002 is separately authorized by DEC-002.",
  "epistemic_limitation": "The report does not prove what caused the later wanting and is not omniscient confirmation of any origin account.",
  "truth_scope": "attributed-testimony",
  "binding_implications": [
    "Represent the source-side morning as continuous in Nia's account."
  ],
  "protected_ambiguities": [
    "The later handshake-to-wanting causal link remains unverified."
  ],
  "protected_wording": null,
  "affected_timeline_ids": [
    "TL-EXAMPLE-DECEMBER-RECEIVE"
  ],
  "affected_chapters": [
    1,
    2,
    3,
    4,
    5
  ],
  "supporting_advisory_citations": []
}
```

## 8. `NovelExtension`

**Purpose:** one continuity-affecting fact added by the novel rather than supplied directly by binding lyric canon.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `extension_id` | `StableID` | yes | Unique. |
| `extension_kind` | string enum | yes | `character-name`, `alias`, `relationship`, `place`, `institution`, `product`, `mechanism`, `chronology`, `profession`, `document`, or `other-continuity`. |
| `fact` | `NonBlankString` | yes | The selected continuity proposition. |
| `rationale` | `NonBlankString` | yes | Why the extension is needed and compatible. |
| `authority_ref` | `NonBlankString` or `null` | yes | Required for `approved`; may be null while provisional. Resolves to an author decision, approved design decision, or completed Arc Change. |
| `first_dependency` | `RecordRef` | yes | First record or chapter that depends on the fact. |
| `affected_records` | array of `RecordRef` | yes | Unique references; nonempty. |
| `consistency_implications` | array of `NonBlankString` | yes | Nonempty. |
| `state` | string enum | yes | Exactly `provisional`, `approved`, or `retired`. |
| `superseding_arc_change_id` | `StableID` or `null` | yes | Required when retired by an Arc Change; otherwise null. |

### Invariants

An approved extension cannot conflict with a higher Canon Authority. A continuity-changing fact must be recorded before an approved later chapter depends on it. Advisory Production Notes cannot become an extension's authority by citation; they require an actual higher-tier selection. Names and capitalization are checked for stable mapping/agreement, not artistic quality.

```json record=NovelExtension schema=1
{
  "extension_id": "EXT-EXAMPLE-CIVIC-RECORD-TRUST",
  "extension_kind": "institution",
  "fact": "The public-interest archive is named Civic Record Trust.",
  "rationale": "A stable name distinguishes the custodial institution from the technical and commercial institutions.",
  "authority_ref": "DEC-005",
  "first_dependency": {
    "record_type": "ArcEntry",
    "record_id": "50"
  },
  "affected_records": [
    {
      "record_type": "POVProfile",
      "record_id": "POV-JULIAN"
    }
  ],
  "consistency_implications": [
    "Use the exact institution name wherever continuity depends on it.",
    "Custody warrants provenance rather than objective truth."
  ],
  "state": "approved",
  "superseding_arc_change_id": null
}
```

## 9. `Reveal`

**Purpose:** knowledge-state and reader-release design for one fact, belief, or permanently unresolved question.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `reveal_id` | `StableID` | yes | Unique and referenced by Arc entries. |
| `fact_ref` | `RecordRef` | yes | Target is a `CanonFact` or `NovelExtension`. |
| `truth_status` | string enum | yes | Exactly `confirmed`, `character-belief`, or `unresolved`. |
| `knowers_before` | array of `StableID` | yes | Character IDs; unique. Empty if nobody knows. |
| `belief_holders` | array of objects | yes | Each is exactly `character_id`, `position`, `authority`; authority is `non-authoritative-belief` or `evidence-backed-knowledge`. |
| `reveal_owner_pov` | `StableID` or `null` | yes | Resolves to `POVProfile` when a release exists. |
| `reader_release_chapter` | `ChapterNumber` or `null` | yes | Must agree with owner and Arc entry. |
| `withheld_from` | array of `StableID` | yes | Character IDs; unique. |
| `withholding_basis` | `NonBlankString` or `null` | yes | Required for delayed confirmed/character-belief release; null for a permanently unresolved non-release. |
| `payoff_window` | object or `null` | yes | If present: exactly `earliest_chapter` and `latest_chapter`, ordered integers. |
| `protected_resolution` | `NonBlankString` | yes | States what emotional or practical movement may resolve without changing truth status. |

### Invariants

A permanently unresolved record has `truth_status: "unresolved"`, no reveal owner, no reader-release chapter, and no payoff window. All Foreign Signal origin/sender accounts and both accounts of Nia's wanting remain unresolved as specified. Character belief strength does not upgrade truth status. Nia's eventual usable self-trust is a protected emotional resolution, not causation, forgiveness, or archive validation.

```json record=Reveal schema=1
{
  "reveal_id": "REVEAL-EXAMPLE-HANDSHAKE-ORIGIN",
  "fact_ref": {
    "record_type": "CanonFact",
    "record_id": "CF-EXAMPLE-HANDSHAKE-ORIGIN"
  },
  "truth_status": "unresolved",
  "knowers_before": [],
  "belief_holders": [
    {
      "character_id": "CHAR-001",
      "position": "Mara holds a high private conviction that her later handshake caused the wanting.",
      "authority": "non-authoritative-belief"
    },
    {
      "character_id": "CHAR-003",
      "position": "Julian enters an adversary attribution while privately recognizing it as inference.",
      "authority": "non-authoritative-belief"
    }
  ],
  "reveal_owner_pov": null,
  "reader_release_chapter": null,
  "withheld_from": [],
  "withholding_basis": null,
  "payoff_window": null,
  "protected_resolution": "Nia may regain usable self-trust without deciding origin, forgiving Mara, or validating the archive."
}
```

## 10. `MotifEvent`

**Purpose:** one planned dramatic function performed by a recurring phrase, object, image, sound, action, or scene structure.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `motif_event_id` | `StableID` | yes | Unique. |
| `family` | `NonBlankString` | yes | Stable motif-family label. |
| `dramatic_function` | `NonBlankString` | yes | New function, not a keyword count. |
| `movement` | `Movement` | yes | Agrees with all participating chapters. |
| `planned_chapter` | `ChapterNumber` | yes | Primary owning chapter. |
| `participating_chapters` | array of `ChapterNumber` | yes | Nonempty, unique, includes primary; permits one event spanning a Cross Cut. |
| `representation_mode` | string enum | yes | Exactly `literal`, `adapted`, `image`, `action`, or `scene-structure`. |
| `literal_constraint_id` | `StableID` or `null` | yes | Resolves to `LiteralPhraseConstraint` when non-null. |
| `scene_scope` | `NonBlankString` | yes | Identifies the sustained scene/function boundary. |
| `arc_change_history` | array of `StableID` | yes | Unique `ArcChange` refs; empty before any move/change. |

### Invariants

Every participating Chapter Header and Arc entry lists the same event ID. Persistence inside one scene/function remains one event. An Incidental Mention is not a Motif Event. Moving chapter, movement, function, or representation mode requires synchronized ledger/outline/header updates and, after baseline, a completed Arc Change. A literal representation has no exact checker rule unless `literal_constraint_id` is non-null.

```json record=MotifEvent schema=1
{
  "motif_event_id": "MOT-KETTLE-01",
  "family": "kettle",
  "dramatic_function": "Safiya anchors her account of the null in the ordinary Tuesday moment when access to the private maternal layer disappeared.",
  "movement": "aftermath_coda",
  "planned_chapter": 118,
  "participating_chapters": [
    118
  ],
  "representation_mode": "image",
  "literal_constraint_id": null,
  "scene_scope": "Safiya's continuous Tuesday-null account in chapter 118.",
  "arc_change_history": []
}
```

## 11. `LiteralPhraseConstraint`

**Purpose:** the only record that authorizes exact wording, count, and placement checks in novel prose.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `constraint_id` | `StableID` | yes | Unique. |
| `motif_event_id` | `StableID` | yes | Resolves uniquely to `MotifEvent`. |
| `exact_phrase` | `SingleLineString` | yes | Curly display quotation marks are not part of the phrase unless literally present here. |
| `scan_scope` | string enum | yes | Exactly `chapter-prose-body-only`. |
| `allowed_movements` | array of `Movement` | yes | Nonempty, unique. |
| `allowed_chapters` | array of `ChapterNumber` | yes | Empty means any chapter in allowed movements; otherwise narrows scope. |
| `allowed_files` | array of `WorkspacePath` | yes | Empty means derive files from allowed chapters/movements. |
| `allowed_span` | object or `null` | yes | If present: exactly `span_id`, `chapter`, `start_boundary`, `end_boundary`. |
| `minimum_in_scope` | nonnegative integer or `null` | yes | Null when no minimum is fixed or exact count is used. |
| `maximum_in_scope` | nonnegative integer or `null` | yes | Null when no maximum is fixed or exact count is used. |
| `exact_in_scope` | nonnegative integer or `null` | yes | When non-null, minimum and maximum are null. |
| `maximum_outside_scope` | nonnegative integer | yes | Zero for both protected questions. |
| `normalization` | object | yes | Exactly `unicode`, `line_endings`, `case_sensitive`, `punctuation_sensitive`, `word_order_sensitive`, `match_mode`. |
| `scope_exclusions` | array of string enums | yes | Uses the fixed exclusions below. |
| `diagnostic_code` | `SingleLineString` | yes | Stable uppercase underscore code. |

An `allowed_span` boundary is exactly `kind` and `value`. `kind` is `literal-marker`, `line-number`, `start-of-prose`, or `end-of-prose`; `value` is a nonblank string/integer when required and `null` for start/end-of-prose. Start must precede end. A missing/ambiguous declared span makes the requested gate incomplete; the checker never guesses a literary passage.

`normalization` is fixed to Unicode `NFC`, line endings `LF`, booleans true for case/punctuation/order sensitivity, and `match_mode: "non-overlapping-literal"` unless a later approved schema change says otherwise.

`scope_exclusions` contains exactly these values: `canon-source-songs`, `other-song-files`, `planning-documents`, `chapter-headers`, `front-matter`, `editorial-records`, and `checker-output`.

### Invariants

Only constraints represented by this record type are scanned. `Did I say yes?` is permitted only in Mindwars and has no fixed in-scope total. `Whose was that?` occurs exactly twice in the declared Final Passage of final Coda chapter 128 and zero times elsewhere. Occurrences in *Case Zero* or any other song remain outside scope.

```json record=LiteralPhraseConstraint schema=1
[
  {
    "constraint_id": "LPC-DID-I-SAY-YES",
    "motif_event_id": "MOT-YES-01",
    "exact_phrase": "Did I say yes?",
    "scan_scope": "chapter-prose-body-only",
    "allowed_movements": [
      "mindwars_part"
    ],
    "allowed_chapters": [],
    "allowed_files": [],
    "allowed_span": null,
    "minimum_in_scope": null,
    "maximum_in_scope": null,
    "exact_in_scope": null,
    "maximum_outside_scope": 0,
    "normalization": {
      "unicode": "NFC",
      "line_endings": "LF",
      "case_sensitive": true,
      "punctuation_sensitive": true,
      "word_order_sensitive": true,
      "match_mode": "non-overlapping-literal"
    },
    "scope_exclusions": [
      "canon-source-songs",
      "other-song-files",
      "planning-documents",
      "chapter-headers",
      "front-matter",
      "editorial-records",
      "checker-output"
    ],
    "diagnostic_code": "LITERAL_DID_I_SAY_YES_SCOPE"
  },
  {
    "constraint_id": "LPC-WHOSE-WAS-THAT",
    "motif_event_id": "MOT-WHOSE-01",
    "exact_phrase": "Whose was that?",
    "scan_scope": "chapter-prose-body-only",
    "allowed_movements": [
      "aftermath_coda"
    ],
    "allowed_chapters": [
      128
    ],
    "allowed_files": [
      "chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md"
    ],
    "allowed_span": {
      "span_id": "SPAN-FINAL-PASSAGE",
      "chapter": 128,
      "start_boundary": {
        "kind": "literal-marker",
        "value": "<!-- final-passage:start -->"
      },
      "end_boundary": {
        "kind": "end-of-prose",
        "value": null
      }
    },
    "minimum_in_scope": null,
    "maximum_in_scope": null,
    "exact_in_scope": 2,
    "maximum_outside_scope": 0,
    "normalization": {
      "unicode": "NFC",
      "line_endings": "LF",
      "case_sensitive": true,
      "punctuation_sensitive": true,
      "word_order_sensitive": true,
      "match_mode": "non-overlapping-literal"
    },
    "scope_exclusions": [
      "canon-source-songs",
      "other-song-files",
      "planning-documents",
      "chapter-headers",
      "front-matter",
      "editorial-records",
      "checker-output"
    ],
    "diagnostic_code": "LITERAL_WHOSE_WAS_THAT_PLACEMENT"
  }
]
```

## 12. `Baseline`

**Purpose:** provisional-plan completion, calibration evidence, single revision pass, objective readiness, author approval, and Final Targets.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `baseline_id` | `StableID` | yes | Unique; only one current approved baseline. |
| `state` | string enum | yes | `provisional`, `pending-author-approval`, `approved`, or `superseded`. |
| `provisional_arc_complete` | boolean | yes | True only after all planned entries and direct references exist. |
| `resolved_decision_refs` | array of `StableID` | yes | Unique, binding, nonsuperseded decisions required by the plan. |
| `calibration_chapters` | array of `ChapterNumber` | yes | 6–8 unique chapters. |
| `minimal_checker_gate_result_id` | `StableID` or `null` | yes | Required before calibration prose. |
| `calibration_finding_ids` | array of `StableID` | yes | Unique `EditorialFinding` refs. |
| `baseline_revision_pass` | object or `null` | yes | If present: exactly `performed_at` and `dispositions`; one disposition per finding. |
| `full_suite_gate_result_id` | `StableID` or `null` | yes | Required and passing before approval. |
| `author_approval` | object or `null` | yes | If present: exactly `approved_by`, `approved_at`, `approval_record`. |
| `final_targets` | object or `null` | yes | If present: exactly `chapter_count`, `minimum_words`, `maximum_words`; inclusive bounds. |
| `out_of_range_rationale` | `NonBlankString` or `null` | yes | Required if approved targets fall outside provisional ranges; otherwise null. |

Each revision disposition is exactly `editorial_finding_id`, `outcome` (`arc-change` or `no-change-rationale`), `arc_change_id` (nullable), and `rationale` (nonblank).

### Invariants

`approved` requires complete provisional arc, passed minimal and full-suite Gate Results, all calibration findings dispositioned in exactly one revision pass, non-null author approval, and non-null Final Targets. The target minimum cannot exceed maximum. Post-approval changes require `ArcChange`; they do not overwrite the approved baseline silently.

```json record=Baseline schema=1
{
  "baseline_id": "BASELINE-EXAMPLE-PROVISIONAL",
  "state": "provisional",
  "provisional_arc_complete": false,
  "resolved_decision_refs": [
    "DEC-002",
    "DEC-003",
    "DEC-004",
    "DEC-005",
    "DEC-007",
    "DEC-014"
  ],
  "calibration_chapters": [
    1,
    2,
    3,
    4,
    5,
    73,
    118,
    124
  ],
  "minimal_checker_gate_result_id": null,
  "calibration_finding_ids": [],
  "baseline_revision_pass": null,
  "full_suite_gate_result_id": null,
  "author_approval": null,
  "final_targets": null,
  "out_of_range_rationale": null
}
```

## 13. `ArcChange`

**Purpose:** one atomic, auditable post-baseline change and all required cross-document synchronization.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `arc_change_id` | `StableID` | yes | Unique. |
| `date` | `ISODate` | yes | Proposal date. |
| `prior_state` | JSON object | yes | Nonempty snapshot of the changed logical values. This is an explicitly open JSON-value field. |
| `revised_state` | JSON object | yes | Nonempty replacement values. This is an explicitly open JSON-value field. |
| `rationale` | `NonBlankString` | yes | Narrative/calibration reason. |
| `affected_chapters` | array of `ChapterNumber` | yes | Unique, sorted; may be empty only for reference-only changes. |
| `affected_documents` | array of `WorkspacePath` | yes | Unique and nonempty. |
| `synchronization_obligations` | array of objects | yes | Nonempty; each is exactly `document`, `required_change`, `status`, `evidence_ref`. |
| `approval` | object or `null` | yes | If present: exactly `approved_by`, `approved_at`, `approval_record`. |
| `status` | string enum | yes | `proposed`, `approved`, `in-progress`, `complete`, or `rejected`. |
| `completed_at` | `Timestamp` or `null` | yes | Required only for `complete`. |

Obligation `status` is `pending` or `complete`; `evidence_ref` is null until complete and then a nonblank record/path reference.

### Invariants

A post-baseline changed state is valid only when this record names prior/revised state, rationale, affected chapters/documents, and every synchronization. `complete` requires all obligations complete, evidence present, approval present, and completion time present. Partial synchronization cannot be treated as approval. A substantive edit to an approved/final chapter requires header and Arc entry status `revised` until affected gates pass again.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-EXAMPLE-001",
  "date": "2026-09-10",
  "prior_state": {
    "chapter": 124,
    "status": "approved",
    "motif_events": [
      "MOT-COME-04"
    ]
  },
  "revised_state": {
    "chapter": 124,
    "status": "revised",
    "motif_events": [
      "MOT-COME-04",
      "MOT-KETTLE-02"
    ]
  },
  "rationale": "Illustrates an atomic motif-assignment correction after substantive prose change.",
  "affected_chapters": [
    124
  ],
  "affected_documents": [
    "planning/arc-outline.md",
    "planning/motif-ledger.md",
    "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/arc-outline.md",
      "required_change": "Add the motif assignment and set status to revised.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Assign MOT-KETTLE-02 to chapter 124.",
      "status": "pending",
      "evidence_ref": null
    }
  ],
  "approval": null,
  "status": "proposed",
  "completed_at": null
}
```

## 14. `EditorialFinding`

**Purpose:** evidence-bearing human review of subjective craft, never a synthetic score.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `editorial_finding_id` | `StableID` | yes | Unique. |
| `scope` | string enum | yes | `chapter`, `batch`, `movement`, `calibration`, or `manuscript`. |
| `chapter_numbers` | array of `ChapterNumber` | yes | Unique, sorted; nonempty for chapter/calibration findings. |
| `batch_id` | `StableID` or `null` | yes | Required for batch findings. |
| `criterion` | `NonBlankString` | yes | Human-review criterion. |
| `prose_locations` | array of objects | yes | Nonempty; each exactly `path`, `start_line`, `end_line`, `note`. Lines are positive and ordered. |
| `finding` | string enum | yes | Exactly `pass` or `revision`. |
| `rationale` | `NonBlankString` | yes | Evidence-based judgment. |
| `requested_action` | `NonBlankString` or `null` | yes | Required for `revision`; null permitted for `pass`. |
| `reviewer` | `NonBlankString` | yes | Human reviewer identity/role. |
| `reviewed_at` | `Timestamp` | yes | Review time. |
| `resolution` | object or `null` | yes | If present: exactly `resolved_at`, `action_taken`, `follow_up_finding_id`. |

### Invariants

This is the only record that may decide voice fidelity, distinctness, pacing, Hook effectiveness, tenderness, restraint, originality, rhetorical force, or emotional truth. No numeric craft score is allowed. A revision finding remains unresolved until its resolution and any follow-up pass are recorded; objective checker success cannot override it.

```json record=EditorialFinding schema=1
{
  "editorial_finding_id": "EDITORIAL-EXAMPLE-001",
  "scope": "calibration",
  "chapter_numbers": [
    1,
    2
  ],
  "batch_id": null,
  "criterion": "Opening Cross Cut clarity",
  "prose_locations": [
    {
      "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
      "start_line": 20,
      "end_line": 26,
      "note": "Instrument-side handoff evidence."
    },
    {
      "path": "chapters/discovery-part/discovery-part-002-ordinary-morning.md",
      "start_line": 12,
      "end_line": 19,
      "note": "Continuous source-side sensory match."
    }
  ],
  "finding": "pass",
  "rationale": "The second viewpoint adds lived continuity rather than replaying the measurement.",
  "requested_action": null,
  "reviewer": "Author/editor",
  "reviewed_at": "2026-09-10T12:00:00Z",
  "resolution": null
}
```

## 15. `GateResult`

**Purpose:** an explicit result for one objective or editorial gate without allowing one gate class to substitute for another.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `gate_result_id` | `StableID` | yes | Unique. |
| `gate_type` | string enum | yes | `site-isolation`, `calibration-objective`, `chapter-local`, `batch`, `baseline-objective`, `manuscript-global`, or `editorial`. |
| `scope` | object | yes | Exactly `chapter_numbers`, `documents`, `description`; arrays unique, description nonblank. |
| `prerequisite_state` | string enum | yes | Exactly `complete` or `incomplete`. |
| `objective_diagnostic_ids` | array of `StableID` | yes | Unique `CheckerDiagnostic` refs. |
| `editorial_finding_ids` | array of `StableID` | yes | Unique `EditorialFinding` refs. |
| `result` | string enum | yes | Exactly `pass`, `revision`, or `incomplete`. |
| `checker_exit_status` | integer or `null` | yes | Objective gates use 0, 1, or 2; editorial gates use null. |
| `timestamp` | `Timestamp` | yes | Evaluation completion time. |

### Invariants

`incomplete` prerequisite state forces `result: "incomplete"`; objective gate exit status is 2. Complete objective scope with error diagnostics yields `revision`/1; zero violations yields `pass`/0. Editorial results derive from human findings and never from diagnostic prose analysis. Final Manuscript status requires separate passing `manuscript-global` and final `editorial` Gate Results.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EXAMPLE-SITE-ISOLATION",
  "gate_type": "site-isolation",
  "scope": {
    "chapter_numbers": [],
    "documents": [
      "exclusion-contract.json"
    ],
    "description": "Reference collector validation against the manuscript exclusion contract."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": [],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-10T12:00:00Z"
}
```

## 16. `CheckerDiagnostic`

**Purpose:** one deterministic observation of an objective violation, incomplete input, or non-failing informational condition.

### Fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `diagnostic_id` | `StableID` | yes | Unique within a checker run and deterministic for the same normalized inputs/order. |
| `severity` | string enum | yes | Exactly `error`, `warning`, or `info`. |
| `code` | `SingleLineString` | yes | Stable uppercase underscore code matching `^[A-Z][A-Z0-9_]*$`. |
| `scope` | string enum | yes | `chapter`, `batch`, `planning`, `global`, or `site-exclusion`. |
| `affected_item` | object | yes | Exactly `path`, `record_type`, `record_id`; each nullable only when genuinely inapplicable, but at least one non-null. |
| `observed` | any JSON value | yes | Explicit observed condition. This is an open JSON-value field. |
| `expected` | any JSON value | yes | Explicit expected condition. This is an open JSON-value field. |
| `message` | `NonBlankString` | yes | Human-readable summary without subjective craft judgment. |
| `related_references` | array of `RecordRef` | yes | Unique; may be empty. |
| `exit_class` | string enum | yes | Exactly `violation`, `incomplete`, or `none`. |

### Invariants

An `error` with `exit_class: "violation"` contributes to exit 1. An `error` with `exit_class: "incomplete"` contributes to exit 2, which takes precedence. Warnings and info use `none` and never mask a required failure. The same normalized input produces the same diagnostic ordering and content. Diagnostic codes MUST NOT claim to judge voice, originality, pace, Hook quality, POV distinctness, tenderness, restraint, rhetorical force, or emotional truth.

```json record=CheckerDiagnostic schema=1
{
  "diagnostic_id": "DIAG-EXAMPLE-0001",
  "severity": "error",
  "code": "CHAPTER_WORD_COUNT",
  "scope": "chapter",
  "affected_item": {
    "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
    "record_type": "ChapterHeader",
    "record_id": "124"
  },
  "observed": {
    "declared_words": 1008,
    "observed_words": 1018
  },
  "expected": {
    "relationship": "declared_words equals observed_words"
  },
  "message": "The declared Chapter Header word count does not equal the Prose Body token count.",
  "related_references": [
    {
      "record_type": "ArcEntry",
      "record_id": "124"
    }
  ],
  "exit_class": "violation"
}
```

## Cross-record acceptance summary

A later checker implementation SHALL enforce at least these schema-level relationships:

- every Chapter Header has exactly the nine declared keys and agrees with filename, directory, and `ArcEntry`;
- every declared POV, Timeline, Motif Event, Reveal, Cross Cut, and other direct reference resolves uniquely;
- every `TimelineEntry.technical_state` declares exactly one `mode` and satisfies that mode's closed invariants, with `cancel_state`, `pair_state`, and `pairing_evidence` present only for their own mode;
- every `CANCEL` entry is unaddressed, subtractive only, confined to Mindwars chapters, untargetable, without additive inverse, authorized institutionally at area scale or by one individual's current specific revocable consent when bounded, and yields no provenance;
- an unaddressed subtractive event never resolves as `INTRUDE`, and no record reverses a cancellation;
- every `PAIR` entry has exactly two living participants, matching nontransferable pair calibration, mandatory semantically opaque metadata, default-off recording enabled only by both participants, and a transcript scoped to that recorded session;
- Character ID and POV ID mappings are one-to-one;
- Cross Cuts are reciprocal and Motif Event assignments agree among ledger, outline, and headers;
- Canon Facts use only the four authority bases, with strict `ratified-note` adoption and the exact five lyric paths;
- `songs/One-Time Pad.md` cannot resolve as lyric authority;
- *Case Zero* first-person records remain attributed testimony rather than omniscient causal proof;
- unratified production/style/exclude/workflow/credit/rights material remains advisory/non-story;
- exact phrase checks are created only by `LiteralPhraseConstraint` and scan Chapter File Prose Bodies only;
- missing/malformed inputs fail closed, objective violations fail nonzero, and subjective craft remains exclusively editorial.

Changes to this schema require an explicit update to this document and corresponding checker fixtures. Commentary elsewhere cannot silently extend an enum, add a field, change null behavior, or widen canon/literal authority.