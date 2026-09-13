# Arc Outline

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `ArcEntry`, `CrossCut`, and `Baseline`  
Structural authority: Requirements 1.2–1.5, 1.7–1.9, 2.1, 2.7, 2.10–2.12, 3.1, 3.6, and 15.5–15.8  
Narrative authority: the design's *Detailed Sequence and Beat Architecture*, *POV Rotation, Cross-Cut Grammar, and Reveal Ownership*, and *Original Thriller Pacing Architecture*  
Decision authority: binding, nonsuperseded decisions through `DEC-019`; `DEC-016` governs pacing architecture, `DEC-011` the title reversal, `DEC-017` the delayed consent parallel, `DEC-018` chapter shape, forward pressure, voice separation, human cost, warmth, and the normal-class word target, and `DEC-019` intermittent frame presence, spent outlier budget, irregular rotation, one Discovery compressed-clock cluster, and completion of the `DEC-018` frontier  
Created by: task 5.1  
Amended: **2026-09-18** — `DEC-018` planning obligations. The Mindwars and Coda movement sections carry the new drafting obligation to make the class of uncounted private civilian loss vivid inside Chapters 109–114, and `DEC-018` clause 10's 1,050–1,200 `normal`-class target is recorded beside the length-class budget. No `ArcEntry`, `CrossCut`, or `Baseline` record value changed in this pass: still 128 entries, 65 cross-cuts, the same length classes, `estimated_words`, motifs, reveals, statuses, and calibration selections. Re-budgeting `estimated_words` to the clause 10 band is an open obligation of `ARC-CHANGE-REVISION-001` and belongs to a later wave.
Amended: **2026-09-13** — every `ArcEntry` gains the required `estimated_words` key under the amended `record-schemas.md`, and global invariant 6 gains the `DEC-016` same-POV run word limit of 3,600 Prose_Words.
Amended: **2026-09-14** — task 5.6 audit. The reveal reference rules state the `reader_release_chapter`/`reveal_owner_pov` agreement rule explicitly, and the reveal table's release chapters for `REVEAL-NIA-SOURCE-CASUALTY` and `REVEAL-CASUALTY-CONSEQUENCE` are corrected to 24 and 52. The [task 5.6 audit result](#task-56-audit-result) records the complete pass, the repairs, and the one finding referred upward.
Amended: **2026-09-14** — task 5.7 Calibration Batch. Chapters 1–5, 73, 118, and 124 now carry `calibration_selected: true`; 73, 118, and 124 carry a non-null `representative_purpose` and `status: "exploratory"`. The `status` and calibration rows of the field contract and global invariants 19 and 20 record the post-5.7 state, and the [task 5.7 Calibration Batch](#task-57-calibration-batch) section records the selection, the exploratory scope, and Julian's unresolved Requirement 5.11 first-appearance gate.
Amended: **2026-09-14** — task 5.8 verification pass. `Baseline.provisional_arc_complete` is `true`. Five stale prose statements are repaired: the four movement-section sentences that still named the pre-5.6 reveal release chapters 23 and 53, and the worked template's claim that no chapter 124 entry exists. The [task 5.8 verification pass](#task-58-verification-pass) records all eighty checks, the repairs, the flag decision, and the one gap that remains open against task 4.2.
Amended: **2026-09-15** — author-approved amendment pass closing that gap. The Canon Bible now holds thirteen `mode: PAIR` chronology entries and six non-viewpoint supporting Character IDs, so this document names the participants who were previously described only by role, and the [chronology assignment](#chronology-assignment) window table lists the new overlapping PAIR windows. Chapter 73 gains a coordinated Fluent_Pairing beat, making the 70–77 beat set 73, 74, 75, 77 and unblocking tasks 7.3 and 8.3. Nothing structural moved: still 128 entries, 65 cross-cuts, the same eight calibration selections and three exploratory statuses, unchanged POV loads, unchanged length classes, estimates, motifs, cross-cuts, reveals, and `timeline_id` assignments. See the [2026-09-15 amendment pass](#2026-09-15-author-approved-amendment-pass).

This document is the Provisional Arc. It holds one `ArcEntry` per planned Chapter File, the reciprocal `CrossCut` records those entries reference, and the provisional `Baseline`. It is the single place where sequence, movement, chronology assignment, viewpoint, purpose, hook, cross-cut, length class, status, calibration selection, record horizon, and reveal references are fixed for the whole book.

It does not restate canon. Timeline IDs and Reveal IDs are declared in [`canon-bible.md`](canon-bible.md), POV IDs in [`pov-roster.md`](pov-roster.md), and Motif Event IDs and literal-phrase constraints in [`motif-ledger.md`](motif-ledger.md). This document references them and must agree with them.

## Initialization state

**Active `ArcEntry` records: 128 (chapters 1–128). Active `CrossCut` records: 65. Active `Baseline` records: 1 (`provisional`).**

Task 5.1 established this frame. The 128 entries themselves are written by four later tasks, each into the entry section named for its movement:

| Task | Chapters | Writes into |
|---|---:|---|
| 5.2 | 1–29 | [Discovery_Part entries](#discovery_part-entries--chapters-129) |
| 5.3 | 30–61 | [Private_Defense_Part entries](#private_defense_part-entries--chapters-3061) |
| 5.4 | 62–112 | [Mindwars_Part entries](#mindwars_part-entries--chapters-62112) |
| 5.5 | 113–128 | [Aftermath_Coda entries](#aftermath_coda-entries--chapters-113128) |

Task 5.6 audits cross-cut reciprocity, reveal links, record horizons, and chronology across the finished set. Task 5.7 sets the Calibration Batch flags, and has now done so: see [task 5.7 Calibration Batch](#task-57-calibration-batch). Until 5.2–5.5 have run, the absence of entries is stated in prose here rather than represented by an empty or invented JSON record.

### Persistence contract

An actual project record exists in this document only inside a schema-compatible typed JSON fence whose opening line is exactly one of:

- `json record=ArcEntry schema=1`
- `json record=CrossCut schema=1`
- `json record=Baseline schema=1`

The JSON body is one object or a nonempty array of objects of the declared type. Typed fences are reserved for real project records. Templates, placeholders, illustrative entries, empty arrays, and `EXAMPLE` identifiers must not appear in a typed fence in this file. Commentary, prose, and tables outside typed fences are never parsed as record values and can never repair, complete, or override a record.

The [worked template](#worked-arcentry-template) below therefore uses an untyped `json` fence and `EXAMPLE` identifiers, matching the convention already used in [`editorial-log.md`](editorial-log.md) and [`arc-changes.md`](arc-changes.md). Because it carries no `record=` type, the parsing contract never treats it as an `ArcEntry`, and it has no continuity authority.

No record type other than the three above may appear in a typed fence in this document. In particular, this document creates no `ChapterHeader`, `MotifEvent`, `LiteralPhraseConstraint`, `Reveal`, `TimelineEntry`, `EditorialFinding`, or `GateResult` record.

---

## Movement order and boundaries

Exactly four Story Movements in exactly this order (Requirement 3.1). The fourth is labeled **Aftermath_Coda** and is never a fourth Main Part (Requirement 3.6); part pages label only the first three as "Part."

| # | Story_Movement | `movement` value | Chapters | Directory and filename prefix |
|---:|---|---|---:|---|
| 1 | Discovery_Part | `discovery_part` | 1–29 | `chapters/discovery-part/discovery-part-NNN-<slug>.md` |
| 2 | Private_Defense_Part | `private_defense_part` | 30–61 | `chapters/private-defense-part/private-defense-part-NNN-<slug>.md` |
| 3 | Mindwars_Part | `mindwars_part` | 62–112 | `chapters/mindwars-part/mindwars-part-NNN-<slug>.md` |
| 4 | Aftermath_Coda | `aftermath_coda` | 113–128 | `chapters/aftermath-coda/aftermath-coda-NNN-<slug>.md` |

The four movement blocks are contiguous: every chapter in a block belongs to that movement, and no movement value reappears after its block closes. Filename, directory, `ArcEntry.movement`, and the Chapter Header must satisfy the four-way agreement rule in [`file-conventions.md`](file-conventions.md).

## Provisional scale and allocation

The provisional plan is **exactly 128 Chapter Files and 140,000 Prose_Words**, inside the approved 120–135 chapter and 130,000–150,000 word ranges (Requirement 2.1). These are planning targets, not the Approved Baseline.

| Story_Movement | Chapters | Chapter count | Provisional Prose_Words | Average planning load | Structural job |
|---|---:|---:|---:|---:|---|
| Discovery_Part | 1–29 | 29 | 30,000 | ~1,034 | Wonder becomes first violation |
| Private_Defense_Part | 30–61 | 32 | 34,500 | ~1,078 | Private refusal becomes an inadequate social answer |
| Mindwars_Part | 62–112 | 51 | 59,000 | ~1,157 | Undeclared conflict, counterphase, null, and cost |
| Aftermath_Coda | 113–128 | 16 | 16,500 | ~1,031 | Public bill becomes an intimate unmet request and outward duty |
| **Total** | **1–128** | **128** | **140,000** | **~1,094** | — |

Mindwars carries more provisional words than any other movement and the Coda fewer than any Main Part, which is the planning expression of Requirements 3.7 and 3.8. Those requirements are finally verified against observed word counts in the completed manuscript, not against this table.

### Provisional POV load

Four human POVs, loads fixed by `DEC-016` clause 8 and [`pov-roster.md`](pov-roster.md).

| POV_ID | Discovery | Private Defense | Mindwars | Coda | Total |
|---|---:|---:|---:|---:|---:|
| `POV-MARA` (Anchor) | 14 | 14 | 21 | 7 | 56 |
| `POV-NIA` | 9 | 8 | 14 | 1 | 32 |
| `POV-JULIAN` | 6 | 10 | 16 | 1 | 33 |
| `POV-SAFIYA` | 0 | 0 | 0 | 7 | 7 |
| **Movement total** | **29** | **32** | **51** | **16** | **128** |

`POV-MARA` is the single Anchor and the only POV with chapters in all four movements. No fifth POV exists, and none may be added for a sender, adversary, operative, archive, simulation, model, or group mind.

### Length-class budget

| Length_Class | Prose_Word band | Planning rule |
|---|---|---|
| `normal` | 700–1,600 | At least **108** of 128 entries |
| `microchapter` | below 700 | Combined with `long-outlier`, at most **20** of 128 entries |
| `long-outlier` | 1,601–2,500 | Combined with `microchapter`, at most **20** of 128 entries |

**Hard_Chapter_Maximum is 2,500 Prose_Words.** No planned chapter may be estimated above it, and no drafted Prose Body may exceed it regardless of declared class. The Normal_Chapter_Range is 700–1,600.

The 108-entry normal floor is deliberately stricter than the global 80-percent rule, which needs 103 of 128. The margin absorbs drafted chapters that land outside their planned class without immediately putting the manuscript-global gate at risk.

Per-movement outlier ceilings, allocated roughly by chapter count:

| Story_Movement | Outlier ceiling | Normal floor |
|---|---:|---:|
| Discovery_Part | 4 | 25 |
| Private_Defense_Part | 5 | 27 |
| Mindwars_Part | 8 | 43 |
| Aftermath_Coda | 3 | 13 |
| **Total** | **20** | **108** |

These are ceilings, not quotas; a movement may use fewer. Before baseline approval, reallocating outliers between movements requires only a dated note in this section and must keep the global total at or under 20; task 5.6 audits the global figure. After baseline approval it requires an `ArcChange`.

**Dated note, 2026-09-18, `DEC-019` clause 3.** Chapter 43 moves from `normal` to `long-outlier` and receives a non-null `outlier_purpose`. Private_Defense_Part goes from 4 outliers to 5, which is exactly its ceiling; the global total goes from 18 to 19 against the ceiling of 20, and the `normal` count goes from 110 to 109 against the floor of 108. No outlier moves between movements and no other entry changes.

This note also records a correction to the arithmetic that motivated `DEC-019` clause 3. The delivered manuscript's 5 outliers in 49 chapters were compared against the global 20-outlier ceiling rather than against the 18 the plan already allocates, which made the budget look roughly 15 entries underspent when the true delivered shortfall is about 2. The plan is close to fully allocated, so clause 3 cannot be satisfied by adding many more outliers. The remaining rhythm variance has to come from inside the `normal` class, whose Normal_Chapter_Range is 700–1,600 and whose `DEC-018` clause 10 drafting target of 1,050–1,200 is the actual cause of the observed metric evenness: 41 of 44 delivered normals now sit inside a 150-word band. With the projection at roughly 143,700 Prose_Words against approved Final_Targets of 130,000–150,000, widening the clause 10 target while holding the same mean would restore variance at no cost to the total. That widening is an open obligation and is not made by this note.

Every outlier — either class — carries a non-null `outlier_purpose` naming the specific compression, interruption, revelation, aftermath, or expansion function it performs (Requirements 2.10 and 2.11). A `normal` entry carries `outlier_purpose: null`. "It felt long" and "it felt short" are not purposes.

#### `DEC-018` clause 10 — the normal-class target inside the band

The Normal_Chapter_Range of 700–1,600 is the permitted class band and is unchanged. `DEC-018` clause 10 adds a **drafting target of 1,050–1,200 Prose_Words for `normal` chapters**, with 1,125 as the planning mean, because the delivered manuscript was tracking a mean of 912 and projecting roughly 117,000 words against approved Final_Targets of 130,000–150,000.

The outline's actual distribution is 110 `normal`, 10 `microchapter`, and 8 `long-outlier`. Outliers keep their declared `outlier_purpose` compression or expansion and are never inflated to reach a total, so their contribution is computed from selected and delivered values rather than from class-band width: the ten microchapters average 500 across the seven whose values are known, for 5,000, and the eight long-outliers average 1,798.5 across the four whose values are known, for about 14,400 — roughly **19,400 Prose_Words from the 18 outliers**. The 110 normals then carry the remainder: 115,500 at the target floor for a total near 134,900, 123,750 at the midpoint for a total near 143,150, and 132,000 at the target ceiling for a total near 151,400. The operative rule is therefore that the normal-class **mean** must land between about 1,006 and 1,187 Prose_Words; 1,200 is a per-chapter ceiling for the class and not a target for the mean.

Clause 10 does not disturb the [same-POV run budget](#same-pov-run-budget). The longest run in the outline is two chapters, so the worst two-chapter normal run reaches 2,400 against the 3,600 limit; the two runs pairing a `normal` with a `long-outlier` reach 3,500 at 100–101 and 2,850 at 127–128; and a hypothetical three-chapter normal run at the target ceiling lands on 3,600 exactly rather than above it.

Clause 10 is a drafting target enforced by human Editorial_Review, not a new objective check. The objectively checkable facts remain the ones already encoded: the 700–1,600 class band, the 2,500-word Hard_Chapter_Maximum, the 108-entry normal floor, the 20-outlier cap, the 3,600-word run limit, and the 130,000–150,000 Final_Targets total. Re-budgeting the `estimated_words` values of `normal` entries into the target band is an open synchronization obligation of `ARC-CHANGE-REVISION-001`; until that is applied, the planning estimates in this document still carry their pre-`DEC-018` values.

### Same-POV run budget

`DEC-016` limits every same-POV run to three chapters and 3,600 combined Prose_Words. The complete 128-entry outline contains 111 runs; the longest is two chapters, so the chapter-count limit is never approached. The word limit still needs real numbers, because most multi-chapter runs are provably compliant from their length classes alone while some are not: chapters 100–101 pair a `normal` with a `long-outlier`, whose worst case under class bands alone is 4,100 Prose_Words, and chapters 127–128 pair the same two classes.

`estimated_words` therefore carries a planning value for all 34 entries in the seventeen multi-chapter runs. Chapters 100 and 101 are budgeted at 1,150 and 2,300, a run total of 3,450, which keeps Mara's full-cost admission at genuine outlier length while staying inside the limit. Single-chapter runs record `null`.

| Run | POV | Chapters | Planned total |
|---|---|---|---:|
| 1 | `POV-MARA` | 10–11 | 2,150 |
| 2 | `POV-JULIAN` | 14–15 | 2,050 |
| 3 | `POV-MARA` | 29–30 | 2,250 |
| 4 | `POV-JULIAN` | 49–50 | 1,570 |
| 5 | `POV-MARA` | 54–55 | 2,150 |
| 6 | `POV-JULIAN` | 69–70 | 2,250 |
| 7 | `POV-MARA` | 71–72 | 1,630 |
| 8 | `POV-NIA` | 77–78 | 2,300 |
| 9 | `POV-MARA` | 80–81 | 2,350 |
| 10 | `POV-MARA` | 84–85 | 2,250 |
| 11 | `POV-MARA` | 100–101 | 3,450 |
| 12 | `POV-SAFIYA` | 115–116 | 1,430 |
| 13 | `POV-SAFIYA` | 118–119 | 2,500 |
| 14 | `POV-MARA` | 120–121 | 2,000 |
| 15 | `POV-SAFIYA` | 122–123 | 2,050 |
| 16 | `POV-MARA` | 124–125 | 1,960 |
| 17 | `POV-MARA` | 127–128 | 2,710 |

Runs 3 and 6 cross the 29/30 and 61/62 movement boundaries and are counted like any other adjacency. The 112/113 boundary falls between two single-chapter runs, Mara at 112 and Nia at 113, so it creates no run at all. Task 5.6 audits the complete set.

---

## `ArcEntry` field contract

Every entry uses exactly these seventeen keys, once each, with no additional key and no omitted key. The record is closed to unknown fields. Field types and structural rules are normative in [`record-schemas.md`](record-schemas.md); the column below states the authoring rule specific to this outline.

| Field | Authoring rule for this outline |
|---|---|
| `chapter` | The global sequence number, 1–128. Unique, and contiguous across the complete outline (Requirement 1.3). It never resets at a movement boundary. |
| `filename` | Workspace-relative POSIX path `chapters/<movement>/<movement>-<NNN>-<slug>.md`, three-digit zero-padded sequence, lowercase hyphenated slug. Unique independently of `chapter`. |
| `movement` | Exactly one of the four enum values, matching the chapter's movement block, directory, and filename prefix (Requirement 1.5). |
| `timeline_id` | Exactly one `TimelineEntry.timeline_id` declared in [`canon-bible.md`](canon-bible.md) (Requirement 1.5). The chapter number must appear in that entry's `chapter_numbers`. See [chronology assignment](#chronology-assignment). |
| `pov_id` | Exactly one `POVProfile.pov_id` from [`pov-roster.md`](pov-roster.md) (Requirement 1.5). One labeled POV per chapter, first-person past. |
| `purpose` | One single-line sentence naming the chapter's narrative function: what changes, for whom. Not a summary of events and not a theme statement. |
| `hook` | Nonblank single line describing the intended final-beat pull (Requirements 1.4 and 2.12). Must agree textually with the Chapter Header's `hook` once the file exists. See [hook variety](#hook-variety-and-the-question-gap-limit). |
| `cross_cuts` | Either the exact string `"none"` or a nonempty duplicate-free array of `CrossCut` IDs declared in this document (Requirements 1.6 and 1.7). No other absence marker is valid. |
| `motif_events` | The set of `MotifEvent` IDs the ledger assigns to this chapter, or `[]`. See [motif placement obligations](#motif-placement-obligations). |
| `estimated_length_class` | Planning class: `normal`, `microchapter`, or `long-outlier`, inside the movement's outlier ceiling. |
| `estimated_words` | Integer planning Prose_Word estimate inside the declared class band, or `null`. **Required non-null for every entry in a same-POV run of two or more chapters**, because the 3,600-word run limit cannot be evaluated from a length class alone. `null` is permitted for a single-chapter run, which the 2,500-word Hard_Chapter_Maximum already bounds. |
| `outlier_purpose` | Non-null single line for either outlier class; `null` for `normal`. |
| `status` | `planned` for every entry written by tasks 5.2–5.5. Task 5.7 set the three nonconsecutive calibration chapters — 73, 118, and 124 — to `exploratory`; the other 125 entries, including the 1–5 opening sequence, remain `planned`. Later values track the Chapter File. |
| `calibration_selected` | `false` for every entry written by tasks 5.2–5.5. Task 5.7 set exactly eight to `true`: chapters 1, 2, 3, 4, 5, 73, 118, and 124. |
| `representative_purpose` | `null` for every entry written by tasks 5.2–5.5. Task 5.7 supplied it for the calibration chapters outside the opening sequence — 73, 118, and 124 (Requirement 1.9). It stays `null` for 1–5, which are inside the opening sequence, and for every non-calibration entry. |
| `record_horizon` | Object with exactly `through_timeline_id` and `knowledge_limit`. See [record horizon](#record-horizon). |
| `reveal_ids` | `Reveal` IDs from [`canon-bible.md`](canon-bible.md), or `[]`. See [reveal reference rules](#reveal-reference-rules). |

### Chronology assignment

Each entry names exactly one `timeline_id` — the chronology the chapter dramatizes. Several declared TimelineEntry windows overlap because scene chronology, record composition, deposit, and conditioned release are deliberately distinct. Where more than one window contains a chapter, exactly one entry is the assigned owner, and the others may be referenced only through `record_horizon.through_timeline_id` or the owning TimelineEntry's `record_chronology` — never as a second `timeline_id`.

Declared chronology windows, from [`canon-bible.md`](canon-bible.md):

| Timeline_ID | Chapter window | Movement |
|---|---|---|
| `TL-DECEMBER-RECEIVE` | 1–5 | Discovery |
| `TL-DISCOVERY-DUE-DILIGENCE` | 6–15 | Discovery |
| `TL-DISCOVERY-HANDSHAKE` | 16–20 | Discovery |
| `TL-DISCOVERY-NIA-AFTERMATH` | 21–25 | Discovery |
| `TL-DISCOVERY-DOOR-INWARD` | 26–29 | Discovery |
| `TL-PRIVATE-COPPER` | 30–35 | Private Defense |
| `TL-PRIVATE-OFFER` | 36–42 | Private Defense |
| `TL-APRIL-TERM-SHEET` | 43–49 | Private Defense |
| `TL-APRIL-RECORD-ALTERATION` | 50 | Private Defense |
| `TL-TRUST-FORMATION` | 51 | Private Defense |
| `TL-PRIVATE-RECORD-DEPOSITS` | 52–55 | Private Defense |
| `TL-PRIVATE-PROTOCOL` | 56–61 | Private Defense |
| `TL-MINDWARS-ONSET` | 62–69 | Mindwars |
| `TL-MINDWARS-COUNTERPHASE` | 70–77 | Mindwars |
| `TL-MINDWARS-SHIELD` | 78–85 | Mindwars |
| `TL-MINDWARS-TERRITORY` | 86–93 | Mindwars |
| `TL-NULL-DECISION` | 94–101 | Mindwars |
| `TL-NULL-NIGHT` | 102–108 | Mindwars |
| `TL-POSTNULL-HISTORY` | 109–112 | Mindwars |
| `TL-CODA-PUBLIC-ACCOUNTING` | 113–114 | Coda |
| `TL-CODA-APPROACH` | 115 | Coda |
| `TL-CODA-THRESHOLD` | 116–117 | Coda |
| `TL-CODA-ACCOUNT` | 118–121 | Coda |
| `TL-CODA-CONSENT` | 122–123 | Coda |
| `TL-CODA-REFUSAL` | 124–125 | Coda |
| `TL-CODA-STAYING` | 126–127 | Coda |
| `TL-CODA-OUTWARD` | 128 | Coda |
| `TL-RECORD-PRETRUST-COMPOSITION` | 1–5, 16–29 | record custody |
| `TL-RECORD-PRETRUST-DEPOSIT` | 52–55 | record custody |
| `TL-TRUST-ROLLING-DEPOSITS` | 52, 54, 62, 73, 110, 113, 118, 128 | record custody |
| `TL-TRUST-CONDITIONED-RELEASES` | 110, 113, 114 | record custody |
| `TL-PAIR-CLINICAL-BENEFIT` | 36, 37, 41 | pairing session |
| `TL-PAIR-DISPATCH-DEMONSTRATION` | 38 | pairing session |
| `TL-PAIR-MARA-NIA-CALIBRATION` | 40, 42 | pairing session |
| `TL-PAIR-MARA-NIA-COUNTERPHASE` | 73, 74, 75 | pairing session |
| `TL-PAIR-MARA-NIA-FLUENCY-LIMIT` | 77 | pairing session |
| `TL-PAIR-OPERATOR-SHIFT-VANE` | 81 | pairing session |
| `TL-PAIR-OPERATOR-TRAFFIC` | 82, 89 | pairing session |
| `TL-PAIR-OPERATOR-SHIFT-OSEI` | 84 | pairing session |
| `TL-PAIR-MARA-NIA-RECORDED-SESSION` | 88 | pairing session |
| `TL-PAIR-DISPATCH-OPERATIONS` | 91 | pairing session |
| `TL-PAIR-MARA-NIA-NULL-DECISION` | 94, 98 | pairing session |
| `TL-PAIR-SHELTER-INTAKE` | 102, 105 | pairing session |
| `TL-PAIR-NULL-NIGHT-COORDINATION` | 104 | pairing session |

The thirteen pairing-session windows were added to [`canon-bible.md`](canon-bible.md) by the 2026-09-15 amendment pass so that every declared Fluent_Pairing beat carries exactly one recorded mode. They behave like the record-custody windows: they overlap a scene window, they are **never** named as a second `timeline_id`, and an entry may reach one only through `record_horizon.through_timeline_id`. Each chapter's owner remains the scene chronology it already named, so no `ArcEntry` changed its `timeline_id` and no chapter has two owners.

Assigning a `timeline_id` here does not populate `TimelineEntry.cross_cut_ids`. Those arrays are currently empty in the Canon Bible and are filled from this document's `CrossCut` records as a synchronization obligation of task 5.6.

### Record horizon

`record_horizon` is planning-only and never appears in a Chapter Header. It contains exactly:

- `through_timeline_id` — the latest chronology point the narrator knows when composing this source account. It may reference a scene window or a record-custody window.
- `knowledge_limit` — a nonblank sentence stating what this narrator can and cannot know at composition.

No `purpose`, `hook`, or `reveal_ids` value may depend on knowledge later than its own horizon. First-person past narration does not license foreshadowing: it does not prove the narrator survives the book, stays cognitively intact, or understands the outcome. Discovery-era accounts are composed before the Civic Record Trust exists and deposited only after its post-April formation; rolling Trust deposits begin only from formation onward.

### Reveal reference rules

An entry lists a `Reveal` ID only when the chapter materially advances or releases that reveal, and only when the chapter number falls inside that reveal's declared `payoff_window`. The reveal's `reader_release_chapter` must list it.

`reader_release_chapter` must also agree with `reveal_owner_pov`, as `record-schemas.md` requires of the `Reveal` record: the release chapter is narrated by the owning POV. A reveal may be advanced by other viewpoints anywhere inside its payoff window, but the chapter recorded as its release belongs to the POV that owns it.

| Reveal_ID | Owner POV | Release chapter | Payoff window |
|---|---|---:|---|
| `REVEAL-NIA-SOURCE-CASUALTY` | `POV-NIA` | 24 | 21–25 |
| `REVEAL-BIDIRECTIONAL-ARCHITECTURE` | `POV-MARA` | 45 | 43–49 |
| `REVEAL-CASUALTY-CONSEQUENCE` | `POV-NIA` | 52 | 50–55 |
| `REVEAL-COUNTERPHASE-TRANSMITS` | `POV-MARA` | 72 | 70–77 |
| `REVEAL-AFFECTED-AREA-EXTENT` | `POV-JULIAN` | 96 | 94–101 |
| `REVEAL-SAFIYA-TUESDAY-LOSS` | `POV-SAFIYA` | 118 | 118–119 |

Three declared reveals have **no owner, no release chapter, and no payoff window** because they are never revealed:

- `REVEAL-HANDSHAKE-WANTING-ORIGIN` — whether Mara's later handshake caused Nia's wanting;
- `REVEAL-FOREIGN-SIGNAL-PROVENANCE` — who or what sent the Foreign Signal;
- `REVEAL-CODA-PROVENANCE` — provenance after the damage.

**These three IDs must never appear in any `reveal_ids` array, and no `purpose` or `hook` may resolve, confirm, or promote either origin account.** Every chapter is free to dramatize belief; none may convert belief into proof. Mara's high private conviction stays non-authoritative, Nia refuses both accounts, and Julian's professional attribution stays an inference he privately recognizes (`DEC-007`).

---

## Global invariants

These hold across the complete 128-entry outline. Each is objectively checkable from records alone, and each is what tasks 5.2–5.7 are verified against.

**Identity and sequence**

1. Exactly 128 entries. `chapter` values form one uninterrupted range from 1 through 128 with no gap, no duplicate, and no reuse.
2. `filename` is unique independently of `chapter`, follows the fixed convention, resolves under the workspace root, and matches its chapter's movement directory and prefix.
3. Each entry names exactly one `movement`, one `timeline_id`, and one `pov_id`.

**Movement structure**

4. The four movement blocks are contiguous and appear in the order Discovery_Part, Private_Defense_Part, Mindwars_Part, Aftermath_Coda, with boundaries at 29/30, 61/62, and 112/113.
5. The movement mapped to *The Radius* is labeled `aftermath_coda`. No entry, heading, or filename presents it as a fourth Main Part.

**Viewpoint**

6. No more than three consecutive entries share one `pov_id`, **and no same-POV run exceeds 3,600 combined Prose_Words.** A same-POV run is a maximal uninterrupted sequence of entries sharing one `pov_id`. Runs are counted on the global sequence, so the boundary pairs 29/30, 61/62, and 112/113 are counted like any other adjacency. Both limits bind independently: a legal three-chapter run can still violate the word limit, and a two-chapter run can violate it too. Planning evaluates the total from `estimated_words`; the finished manuscript is evaluated from each Chapter_Header's `words` value. Under `DEC-016` as amended 2026-09-13 the word limit is the operative one, because three normal chapters could reach 4,800 Prose_Words and even a two-chapter run could reach 5,000, so a chapter break must not be allowed to disguise an overlong stay in one viewpoint.
7. Per-movement POV counts equal the [provisional POV load](#provisional-pov-load) exactly: Mara 14/14/21/7, Nia 9/8/14/1, Julian 6/10/16/1, Safiya 0/0/0/7.
8. Only the four roster POV IDs appear. `POV-SAFIYA` appears only in 113–128.

**Length**

9. At least 108 entries carry `estimated_length_class: "normal"`.
10. At most 20 entries carry `microchapter` or `long-outlier` combined, within each movement's ceiling.
11. Every outlier entry carries a non-null `outlier_purpose`; every `normal` entry carries `null`.
12. No entry may be planned above the 2,500-word Hard_Chapter_Maximum.

**Purpose, hook, and horizon**

13. `purpose` and `hook` are nonblank single lines. Neither may use knowledge beyond that entry's `record_horizon`.
14. `record_horizon` contains exactly `through_timeline_id` and `knowledge_limit`; the timeline reference resolves and the limit is nonblank.

**Cross-cuts**

15. Every `CrossCut` ID in an entry's `cross_cuts` array is declared by a `CrossCut` record in this document, and that record's `chapters` and `declared_by_chapters` sets contain the referencing chapter. Reciprocity is total: a one-sided or dangling relationship is a violation, not a style choice.
16. An entry with no cross-cut relationship records the exact string `"none"`. Empty string, `[]`, `"N/A"`, and omission are all invalid.

**Motifs and reveals**

17. `motif_events` equals the set the Motif Ledger assigns to that chapter, and `[]` where the ledger assigns none.
18. `reveal_ids` contains only reveals whose payoff window includes the chapter. The three never-revealed reveals appear nowhere.

**Status and calibration**

19. Every entry as written by tasks 5.2–5.5, before task 5.7 runs, carries `status: "planned"`, `calibration_selected: false`, and `representative_purpose: null`. Task 5.7 is the only task permitted to change those three fields; nothing else in the outline may.
20. After task 5.7, exactly eight entries carry `calibration_selected: true` — chapters 1, 2, 3, 4, 5, 73, 118, and 124 — and the set equals `Baseline.calibration_chapters`. Chapters 73, 118, and 124 sit outside the opening sequence and therefore carry a non-null `representative_purpose`; chapters 1–5 sit inside it and keep `null`. The same three nonconsecutive entries carry `status: "exploratory"`; every other entry, including 1–5, still carries `status: "planned"`, `calibration_selected: false`, and `representative_purpose: null`. `exploratory` here is a planning state, not a claim that a Chapter File exists: no Chapter File exists yet for any of the eight.

**Boundaries this outline may not cross**

21. No entry resolves the Provenance Question or the origin of Nia's wanting, in any field.
22. No entry places active defender counterphase transmission outside 62–112, and no Coda entry depicts renewed Foreign Signal transmission, renewed combat, campaign, or adversary proof.
23. No entry adds a POV for the Foreign Signal or any actual, alleged, or hypothesized sender, operative, adversary, archive, simulation, model, or group mind.
24. No POV enters Safiya's home. Her Tuesday account is withheld until she owns it in 118–119.
25. No entry field carries a numeric craft score, resemblance score, style score, sentence-length target, suspense rating, or hook-force value. Craft judgment lives in [`editorial-log.md`](editorial-log.md).

---

## `CrossCut` record contract

`CrossCut` records live in this document, in [Cross-cut records](#cross-cut-records). A Cross Cut is declared only where two or more chapters genuinely share a Timeline_ID, a consequence, or a withheld disclosure (Requirement 1.6), and only where each participant contributes distinct Material_Narrative_Value.

| Field | Authoring rule |
|---|---|
| `cross_cut_id` | Unique stable ID, convention `CUT-<DESCRIPTIVE-SEGMENTS>`, uppercase with hyphen segments. |
| `chapters` | At least two unique chapter numbers, sorted ascending, all of which have entries. |
| `shared_timeline_id` | The shared `TimelineEntry`, or `null`. |
| `shared_reveal_id` | The shared `Reveal`, or `null`. Never one of the three never-revealed IDs. |
| `shared_consequence` | Nonblank when timeline and reveal are both `null`. At least one of the three is non-null. |
| `handoff_mode` | One of `sensory-match`, `causal-cut`, `contradiction-cut`, `threshold-cut`, `temporal-braid`, `delayed-return`. |
| `material_narrative_value` | Exactly one object per participating chapter, each with a nonblank `value` that is materially distinct from the others. |
| `replay_boundary` | Nonblank statement of what may repeat and where the next account begins. |
| `declared_by_chapters` | Set-equal to `chapters`. |

Reciprocity is enforced in both directions: every participating `ArcEntry.cross_cuts` array contains the ID, and no nonparticipant declares it. Repeated scene time is legitimate only when each `material_narrative_value` is distinct — the checker validates the declarations, and a human decides whether the distinction is artistically real.

A relationship may span more than two chapters. The design's cross-cut grammar supplies the six handoff modes: sensory match (waveform to lived sound, relay click to kettle, clean silence to missing word), causal cut, contradiction cut, threshold cut, temporal braid, and delayed return.

### When the obligation applies

Requirement 1.6 attaches to a shared timeline **event**, consequence, or withheld disclosure — not to co-membership in a chronology window. Most declared TimelineEntries have `chronology_kind: "interval"` and span a whole cluster, so two chapters may name the same `timeline_id` while depicting different hours and different rooms. That alone creates no obligation and no clique.

The obligation attaches when chapters depict the same moment, carry the same consequence forward, or hold two sides of one withheld disclosure. Where it attaches, it is absolute and reciprocal. Where it does not, the entries record `"none"`, and recording `"none"` is a positive statement that no such relationship exists rather than an omission.

Two consequences of that rule are fixed here:

- **Null night (102–108).** All seven chapters hold `TL-NULL-NIGHT`, one continuous compressed night. Every one of the seven participates in at least one Cross Cut, and no two `material_narrative_value` entries may cover the same action.
- **The threshold (116–117).** One arrival seen from two sides is one event and one Motif_Event. The pair carries a reciprocal `threshold-cut` whose `replay_boundary` keeps Chapter 117 from replaying Safiya's approach.

### Compressed-clock clusters

Compression is declared structurally, never asserted in prose. A compressed-clock cluster exists where several chapters share one `timeline_id` whose TimelineEntry chronology supports the compression, joined by `CrossCut` records with `handoff_mode: "temporal-braid"`.

Null night (102–108) is the book's tightest cluster: all seven chapters hold one Timeline_ID with reciprocal, non-redundant Cross Cuts. Compression is permitted only where declared chronology supports it, and **the complete manuscript is never placed inside one global twenty-four-hour frame** (Requirement 15.5). The declared chronology already forbids it: the span runs from the December reception through two years after null night.

---

## `DEC-016` original-thriller controls

`DEC-016` is binding craft and architecture authority. It is not Canon Lyric and not a Binding Canon Fact. Its structural clauses — 128 chapters, the 29/32/51/16 allocation, the 56/32/33/7 loads, the ≤3 POV run, the 108 normal floor, the 20-outlier cap, the 700–1,600 range, and the 2,500-word maximum — are already encoded as [global invariants](#global-invariants) and are objectively checkable.

Everything below is a **human Editorial_Gate**. No checker may score, rank, or threshold any of it. Findings are recorded as `EditorialFinding` and editorial `GateResult` records in [`editorial-log.md`](editorial-log.md), with representative prose evidence and a `pass` or `revision` result. There is no automated prose score, resemblance score, style score, suspense score, pacing score, hook-force value, or named-author-similarity measure anywhere in this project, and no `ArcEntry` field may be added to carry one.

| Gate criterion | Scope | What the human reviewer decides |
|---|---|---|
| Hook variety and rotation | Batch, movement | Whether chapter endings rotate across information turns, decision locks, reversals, arrivals, danger, absence, and moral remainder rather than repeating one device, and whether the question-gap limit below holds. |
| Experiment → action → result → consequence | Batch, movement | Whether each technical disclosure is staged as experiment, then action, then result, then an immediate human or institutional consequence, instead of lecture dialogue or an exposition set piece. |
| Escalation consequence | Batch, movement | Whether each material capability escalation promptly changes consent state, a relationship, evidentiary position, institutional power, or bodily risk in the same sequence. |
| Compressed-clock execution | Movement | Whether declared temporal braids read as convergence rather than repetition, and whether the book avoids a global twenty-four-hour feel. |
| Mindwars turnover and threading | Movement | Whether 62–112 carries the manuscript's fastest chapter turnover and tightest converging-thread pattern. |
| Post-112 deceleration | Movement, final batch | Whether threat-cliffhanger pressure deliberately recedes after 112 while the short rotating form remains, and whether Coda hooks become disclosures, arrivals, refusals, emotional choices, and moral remainders. |
| Originality | Batch, movement, manuscript | Whether the prose avoids recognizable imitation of Dan Brown's or Douglas E. Richards's sentence-level prose, distinctive voice, phrasing, scenes, or characters. A finding of imitation is a `revision` (Requirement 15.7). |
| Prohibited devices | Batch, movement, manuscript | Whether the work avoids repetitive artificial cliffhangers, exposition set pieces, a culprit reveal, renewed Coda spectacle, and neural communication presented as group mind. Any of these is a `revision` (Requirement 15.8). |

### Hook variety and the question-gap limit

A **question-gap hook** ends a chapter by withholding a noun, name, number, or answer that the narrator already possesses, so the pull comes from the gap rather than from consequence. `DEC-016` clause 3 treats it as the device that must not substitute for information, a decision lock, reversal, arrival, danger, absence, or moral remainder.

**No more than two adjacent chapters may end on a question-gap hook.** A third consecutive question-gap ending is a `revision` finding.

This is deliberately not an `ArcEntry` field. Classifying a hook requires reading the planned final beat and, once drafted, the prose; the `ArcEntry` record set is closed to unknown fields and carries no hook-kind key. The reviewer classifies from the `hook` text and the prose, and records the judgment in the editorial log. Authors of tasks 5.2–5.5 satisfy this control by writing varied hooks in the first place, not by tagging them.

### Movement pacing profile

| Story_Movement | Intended pacing behavior |
|---|---|
| Discovery_Part | Procedural acceleration. Wonder and verification carry early hooks; the first violation lands late. |
| Private_Defense_Part | Continued procedural acceleration through offer, specification, and record. Institutional pressure supplies reversal. |
| Mindwars_Part | Fastest chapter turnover and tightest simultaneous threading in the manuscript, peaking across null night. |
| Aftermath_Coda | Same short rotating form, deliberately decelerated. Hooks become disclosure, arrival, refusal, emotional choice, and moral remainder. |

---

## `DEC-018` chapter-shape controls

`DEC-018` is binding craft and disclosure authority added after the review of delivered Chapters 1–46. Like the `DEC-016` controls above, **every criterion here is a human Editorial_Gate** under global invariant 25 and Requirement 12.12. No checker may score, rank, or threshold any of it, no `ArcEntry` or `ChapterHeader` field may be added to carry a value for it, and findings are recorded as `EditorialFinding` and editorial `GateResult` records in [`editorial-log.md`](editorial-log.md) with representative prose evidence and a `pass` or `revision` result.

| Gate criterion | Scope | What the human reviewer decides |
|---|---|---|
| Opening does not state the thesis | Chapter, batch | Whether the first sentence begins inside action, sensation, object, or speech whose significance is not yet named, rather than stating the chapter's conclusion or summary judgment. |
| Ending does not echo the `hook` | Chapter, batch | Whether the final line is a restatement, paraphrase, or near-verbatim echo of the entry's `hook`. The `hook` is planning metadata and never appears as prose; a final line reconstructible from the header is a `revision`. |
| One live question per boundary | Chapter, batch, movement | Whether at least one question survives the chapter boundary, generated by consequence, obligation, dread, or a fixed-time event — and whether it does so without artificial withholding and inside the question-gap limit above. |
| Reluctant retrospection | Chapter, batch | Whether the retrospective frame is used to promise cost without disclosing a later fact, on the Chapter 1 model, rather than being left inert. |
| Contradiction-cuts stay unspoken | Batch, movement | Whether any narrator in a `contradiction-cut` relationship states the contradiction explicitly instead of leaving the reader to assemble it. |
| Enumerated absence rationed | Chapter, batch | Whether the construction appears more than once in a chapter, or anywhere the absence is not the chapter's subject. |
| Voice separation and rationed aphorism | Batch, movement, manuscript | Whether syntax, rhythm, paragraph shape, and what each narrator notices distinguish the viewpoints, rather than domain vocabulary alone; and whether terminal aphorism and the isolated one-sentence paragraph have become the default unit. |
| Personal cost per lead per movement | Movement | Whether each POV lead incurs at least one personal, non-abstract cost in each movement in which they hold chapters. Institutional strain and abstract guilt do not satisfy it. |
| Warmth, comfort, and humor per movement | Movement | Whether the movement contains non-professional warmth between named characters, food, rest, or physical comfort offered and accepted, and humor that is not a professional riposte — and whether any POV lead is lonelier or flatter than the supporting cast. |
| Normal-class word target | Batch, movement, manuscript | Whether `normal` chapters land in the 1,050–1,200 target band with a mean near 1,125, and whether any outlier has been inflated away from its declared `outlier_purpose`. See [clause 10 arithmetic](#dec-018-clause-10--the-normal-class-target-inside-the-band). |

The `contradiction-cut` relationships this document declares are the scope of the fifth criterion. In the delivered range they are `CUT-CONFESSION-REFUSED` at 23 and 24, `CUT-CONTAINMENT-ALREADY-LOST` at 26 and 29, `CUT-SEALED-ROOM-AND-A-LIFE` at 32 and 34, `CUT-CALIBRATION-AND-THE-UNCALIBRATED` at 40 and 42, and `CUT-CONSTRAINABLE-CLAUSE` at 44 and 45. Sixteen such relationships exist across the whole outline, and the criterion applies to every one.

---

## Motif placement obligations

[`motif-ledger.md`](motif-ledger.md) is authoritative for motif placement. `ArcEntry.motif_events` copies the ledger's assignment for that chapter; it never invents, moves, or adds an event. Every chapter not listed below carries `"motif_events": []`.

| Chapter | Motif_Event IDs | Note |
|---:|---|---|
| 13 | `MOT-CHAIN-01` | Discovery spectrum-to-bone |
| 16 | `MOT-COME-01` | Discovery "Come in" |
| 31 | `MOT-COPPER-01` | Private boundary |
| 45 | `MOT-CHAIN-02` | Private Defense wire-to-bone |
| 51 | `MOT-RECORD-01` | Record Progression event one |
| 61 | `MOT-COME-02` | Conditional and operational invitation |
| 70 | `MOT-COPPER-02` | Imperfect collective defense |
| 73 | `MOT-KNOCK-01`, `MOT-YES-01` | Consent challenge; carries `LPC-DID-I-SAY-YES` |
| 74 | `MOT-COME-03` | Mindwars invitation |
| 101 | `MOT-RADIUS-01` | Silence has a radius, stated without geometry |
| 109 | `MOT-RECORD-02` | Record Progression event two |
| 116 | `MOT-KNOCK-02` | One arrival event, Safiya's side |
| 117 | `MOT-KNOCK-02` | Same event, Mara's side — one event, two positions |
| 118 | `MOT-KETTLE-01` | Kettle event one |
| 120 | `MOT-RADIUS-02` | The affected area received as people |
| 124 | `MOT-COME-04`, `MOT-COPPER-03`, `MOT-KETTLE-02` | Truthful refusal; retained protection that cannot remedy; kettle event two |
| 127 | `MOT-CHAIN-03` | Coda voice-through-air |
| 128 | `MOT-RECORD-03`, `MOT-KNOCK-03`, `MOT-WHOSE-01` | Record Progression event three; outward threshold; carries `LPC-WHOSE-WAS-THAT` |

Three placements are easy to get wrong and are therefore stated explicitly:

- **`MOT-KNOCK-01` is ledgered in Mindwars at Chapter 73**, not in Private Defense. No Private_Defense entry carries a knock event.
- **`MOT-KNOCK-02` is one event spanning 116–117.** Both entries list it. It is not two events.
- **Mindwars counterphase is chain context, not a chain event.** There is no `MOT-CHAIN-04`. Record Progression has exactly three events. Discovery copper references are unledgered foreshadowing, not a fourth copper event. Creating any of these later requires a documented `ArcChange` synchronizing ledger, outline, and headers.

Only two Literal_Phrase_Constraints exist, both owned by the ledger: `LPC-DID-I-SAY-YES` confines `Did I say yes?` to the Mindwars movement with no fixed in-scope total, and `LPC-WHOSE-WAS-THAT` requires `Whose was that?` exactly twice inside the declared Final_Passage in Chapter 128 and nowhere else. The Final_Passage bounds are machine-readable in the ledger's `SPAN-FINAL-PASSAGE`, which opens at the `<!-- final-passage:start -->` marker in `chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md` and runs to end of prose. This outline creates no constraint and no new motif ID.

Under `DEC-017`, the Chapter 73 / null-night consent parallel receives **no** Motif_Event ID, no Literal_Phrase_Constraint, and no `Reveal` record. It is carried by shared concrete physical vocabulary between 73 and 118, stays unnamed through 123, and is named exactly once inside the existing `MOT-RECORD-03` beat in Chapter 128.

---

## Approved Baseline and Final Targets

**The author approved the recommended revised baseline in the explicit task 10.2 response, “Approve recommended baseline.”** The `Baseline` record below is therefore `approved`. Its Final_Targets are exactly **128 planned chapters** and an inclusive total range of **130,000–150,000 Prose_Words**. Both targets are within the provisional bounds, so `out_of_range_rationale` is correctly `null`.

`provisional_arc_complete` is `true` as of the [task 5.8 verification pass](#task-58-verification-pass). That field records exactly one thing: all 128 entries and every direct reference they make exist and resolve. Approval is recorded separately in `author_approval`; neither field claims that the complete Manuscript already exists.

The approval carries forward `DEC-001`: the binding novel title remains ***The Final Frontier***, while “the Mindwars” remains an in-world event rather than the cover title. It also carries forward `DEC-006`: one concise Front_Matter framing note plus rare, dramatically necessary in-story references, restrained reader-facing chapter labels, and no routine source notes, transcript apparatus, docket labels, evidence citations, or heavy archival labeling. Calibration may still justify removing or retaining an individual rare reference; it does not reopen that visibility model. Any later structural change requires a documented `ArcChange`, and changing either author decision requires author adjudication.

`calibration_chapters` records the batch fixed by the design and task 5.7: chapters 1–5 for opening momentum, voice separation, and Cross Cut clarity; 73 for counterphase consent, Mindwars tone, and Nia's authority without resolved provenance; 118 for Safiya's own voice, concrete loss, the first kettle event, describe-never-quote handling, and the `unspecified_by_author` guardrail; 124 for Mara's response, truth-based refusal, the Coda_Turn, and the Refused_Swell. Exactly these eight entries and Chapter Headers remain `exploratory` after baseline approval and cannot become approved continuity until their later movement batches reconcile and gate them. `calibration_finding_ids` records the complete task-8.7 audit trail: the original revision findings, their resolution links, and the corrective follow-up passes. `baseline_revision_pass` dispositions every listed finding exactly once. The pass found no genuine Arc_Outline implication: the two original revision findings were resolved in exploratory prose and re-reviewed by `EDITORIAL-CAL-013` and `EDITORIAL-CAL-014`, while the other findings affirm the current architecture. The same no-change disposition ledger is readable in [`arc-changes.md`](arc-changes.md). `full_suite_gate_result_id` records the task-8.27 objective evidence; together these fields satisfy the prerequisites on which the author approval below relies.

The pass preserves the corrected December rule already synchronized across the current plan and evidence: raw field acquisition is continuous, Nia experiences no gap, the apparatus has no transmit stage, and eight seconds is the receiver-owned acquisition-to-resolved-output reconstruction latency reproduced only under the same early configuration and information conditions—not a permanent physical constant, source-side delay, or hidden transmission. It also preserves every corrected prose and planning decision from the task-8.7 reread without turning those exploratory chapters into approved continuity.

`resolved_decision_refs` lists the sixteen binding, nonsuperseded author decisions the plan depends on. `DEC-013` is absent because `DEC-014` supersedes it.

### Author approval — task 10.2

- **Approved by:** Jessica Mulein
- **Approved at:** `2026-09-16T22:00:00Z`
- **Approval record:** this section and the typed `Baseline.author_approval` below
- **Explicit response:** `Approve recommended baseline`
- **Final_Targets:** exactly 128 planned chapters; inclusive total Prose_Word range 130,000–150,000
- **Out-of-range rationale:** none required; the chapter count and both word bounds are within the provisional ranges
- **Status effect:** the Baseline becomes approved, but Chapters 1–5, 73, 118, and 124 remain `exploratory` until their movement batches reconcile them

```json record=Baseline schema=1
{
  "baseline_id": "BASELINE-FINAL-FRONTIER-PROVISIONAL",
  "state": "approved",
  "provisional_arc_complete": true,
  "resolved_decision_refs": [
    "DEC-001",
    "DEC-002",
    "DEC-003",
    "DEC-004",
    "DEC-005",
    "DEC-006",
    "DEC-007",
    "DEC-008",
    "DEC-009",
    "DEC-010",
    "DEC-011",
    "DEC-012",
    "DEC-014",
    "DEC-015",
    "DEC-016",
    "DEC-017"
  ],
  "calibration_chapters": [1, 2, 3, 4, 5, 73, 118, 124],
  "minimal_checker_gate_result_id": "GATE-CALIBRATION-OBJECTIVE-001",
  "calibration_finding_ids": [
    "EDITORIAL-CAL-001",
    "EDITORIAL-CAL-002",
    "EDITORIAL-CAL-003",
    "EDITORIAL-CAL-004",
    "EDITORIAL-CAL-005",
    "EDITORIAL-CAL-006",
    "EDITORIAL-CAL-007",
    "EDITORIAL-CAL-008",
    "EDITORIAL-CAL-009",
    "EDITORIAL-CAL-010",
    "EDITORIAL-CAL-011",
    "EDITORIAL-CAL-012",
    "EDITORIAL-CAL-013",
    "EDITORIAL-CAL-014",
    "EDITORIAL-CAL-015",
    "EDITORIAL-CAL-016",
    "EDITORIAL-CAL-017",
    "EDITORIAL-CAL-018"
  ],
  "baseline_revision_pass": {
    "performed_at": "2026-09-16T21:00:00Z",
    "dispositions": [
      {
        "editorial_finding_id": "EDITORIAL-CAL-001",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Mara's represented voice already performs the planned Discovery experiment-to-consequence movement and Chapter 124 Coda_Turn, so no ArcEntry, voice guidance, or chapter assignment changes."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-002",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Nia's represented chapters already match the planned dispatch logic, evidence restraint, consent authority, and usable-self-trust trajectory, so the arc remains unchanged."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-003",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Chapter 118 validates Safiya's planned voice, agency, describe-never-quote handling, and unspecified heritage base; no planning reference requires revision."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-004",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The shared reader-instruction tic was a prose-level calibration defect, resolved across the exploratory chapters and passed by EDITORIAL-CAL-013; it changes no chapter purpose, POV assignment, Voice Brief, or arc beat."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-005",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Opening momentum and receive-only facts validate the Chapters 1-5 sequence, including continuous source time and receiver-owned reconstruction latency, so no arc change is warranted."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-006",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The opening Cross_Cuts are clear and materially nonredundant under their existing reciprocal assignments, so participants, chronology, and replay boundaries stay fixed."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-007",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Current hooks and pacing serve the planned information, decision, absence, and moral-remainder turns; no purpose, hook, or length plan changes."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-008",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Chapter 73 realizes its existing bounded-consent, fluent-pairing, and unresolved-provenance purpose without changing Nia's authority or the planned mechanism."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-009",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The copied cancellation-field phrasing was a prose-level defect, resolved in Chapter 118 and passed by EDITORIAL-CAL-014; DEC-017's sensory-family echo and delayed naming remain unchanged."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-010",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Safiya owns the loss and request while Mara's Chapter 124 refusal remains grounded in physics and truth, validating the existing Coda sequence and Coda_Turn."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-011",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Tenderness, restraint, human cost, emotional truth, and originality pass under the current architecture, so no structural or tonal planning revision is indicated."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-012",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Julian's deliberate calibration absence is correct; his Requirement 5.11 review remains due at planned Chapter 6, with no change to the batch or POV load."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-013",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The corrective follow-up confirms that Mara, Nia, and Safiya separate at sentence-making level; existing POV assignments and current Voice Briefs remain fit."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-014",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The corrected Chapter 73/118 echo carries only the planned sensory family and leaves the link unnamed, exactly preserving DEC-017."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-015",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The chronology review validates the synchronized processing-latency canon: continuous raw acquisition, configuration-dependent eight-second reconstruction, no source gap, and no transmit stage."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-016",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "Chapter 73 preserves its contemporaneous horizon, bounded authorization, local consequence, and usable self-trust without scalable doctrine, so its ArcEntry remains correct."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-017",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The Coda review validates Safiya's maternal-language continuity, Mara's truthful refusal, and the distinct kettle assignments at Chapters 118 and 124; no motif or arc changes."
      },
      {
        "editorial_finding_id": "EDITORIAL-CAL-018",
        "outcome": "no-change-rationale",
        "arc_change_id": null,
        "rationale": "The final corrective reread validates opening momentum, Cross_Cut clarity, hook variety, restraint, human cost, and emotional truth across the provisional plan."
      }
    ]
  },
  "full_suite_gate_result_id": "GATE-BASELINE-OBJECTIVE-001",
  "author_approval": {
    "approved_by": "Jessica Mulein",
    "approved_at": "2026-09-16T22:00:00Z",
    "approval_record": "planning/arc-outline.md#author-approval--task-102"
  },
  "final_targets": {
    "chapter_count": 128,
    "minimum_words": 130000,
    "maximum_words": 150000
  },
  "out_of_range_rationale": null
}
```

`provisional_arc_complete` flipped to `true` only when all 128 entries and every direct reference they make existed and resolved. Tasks 5.2 through 5.6 were its prerequisites, and task 5.8 verified the condition. The single Baseline_Revision_Pass is complete and remains the only such pass for this Baseline. Task 10.2 records the author's approval and Final_Targets without changing any ArcEntry, continuity fact, motif placement, POV assignment, Voice Brief, or exploratory Chapter_File. From this approval forward, changes come only through a documented `ArcChange` in [`arc-changes.md`](arc-changes.md).

---

## Worked `ArcEntry` template

**The block below is a template, not an entry.** It carries no `record=` type, so the parsing contract never treats it as an `ArcEntry`. Every identifier is an illustrative fixture: it reuses the `EXAMPLE` coordinates already used by [`record-schemas.md`](record-schemas.md) precisely so it cannot be mistaken for a planned chapter. Its `chapter` values, 900 and 901, sit outside the 1–128 sequence for the same reason, so neither block can collide with a real entry — the actual chapter 124 entry is a `POV-MARA` record in the [Aftermath_Coda entries](#aftermath_coda-entries--chapters-113128). Copy the shape, then write real entries into the typed fence in the movement section that owns them.

The template shows the two states a single field pair can take: an outlier with a non-null `outlier_purpose`, and the pre-5.7 calibration state where `calibration_selected` is `false` and `representative_purpose` is `null`.

```json
[
  {
    "chapter": 900,
    "filename": "chapters/aftermath-coda/aftermath-coda-900-example-normal.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-EXAMPLE-CODA-VISIT",
    "pov_id": "POV-EXAMPLE-ANCHOR",
    "purpose": "Illustrates a normal-length entry whose purpose names one change and the person it lands on.",
    "hook": "Illustrates a nonblank single-line hook that turns on a decision rather than a withheld noun.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-EXAMPLE-CODA-VISIT",
      "knowledge_limit": "Illustrates a horizon sentence stating what this narrator can and cannot know at composition."
    },
    "reveal_ids": []
  },
  {
    "chapter": 901,
    "filename": "chapters/aftermath-coda/aftermath-coda-901-example-outlier.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-EXAMPLE-CODA-VISIT",
    "pov_id": "POV-EXAMPLE-SECOND",
    "purpose": "Illustrates a cross-cut partner whose purpose adds consequence instead of replaying the prior scene.",
    "hook": "Illustrates a hook that ends on a moral remainder the next chapter must answer for.",
    "cross_cuts": [
      "CUT-EXAMPLE-THRESHOLD"
    ],
    "motif_events": [
      "MOT-EXAMPLE-THRESHOLD-01"
    ],
    "estimated_length_class": "microchapter",
    "outlier_purpose": "Illustrates a required outlier purpose: compression to a single interrupted decision.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-EXAMPLE-CODA-VISIT",
      "knowledge_limit": "Illustrates a second narrator's narrower horizon at the same chronology point."
    },
    "reveal_ids": []
  }
]
```

Note what the template does not do. It does not carry a hook-kind key, a word estimate, a pacing note, or any craft score, because the record is closed to unknown fields and craft is an Editorial_Gate. It does not name a real Timeline_ID, POV_ID, Motif_Event ID, or Cross Cut ID, so nothing in it can resolve against a real record.

---

## Chapter entries

The four sections below are the only places `ArcEntry` records may appear. Each names the task that owns it, the invariants it must satisfy, and the cluster architecture it expands. The cluster tables come from the design's *Detailed Sequence and Beat Architecture*; an owning task may refine chapter boundaries inside its movement but may not invent a different causal spine without a documented `ArcChange`.

Each section's **Entries** subsection currently contains a prose statement of absence. The owning task replaces that statement with one typed `json record=ArcEntry schema=1` fence containing its chapters as a JSON array in ascending order.

### Discovery_Part entries — chapters 1–29

Owner: **task 5.2.** Allocation: 29 chapters, 30,000 provisional Prose_Words, Mara 14 / Nia 9 / Julian 6, outlier ceiling 4.

| Range | Cluster | POV emphasis | Timeline_ID |
|---|---|---|---|
| 1–5 | Noise floor | Mara / Nia / Mara / Nia / Mara | `TL-DECEMBER-RECEIVE` |
| 6–10 | A stranger's morning | Julian / Nia / Mara / Julian / Mara | `TL-DISCOVERY-DUE-DILIGENCE` |
| 11–15 | The field | Mara / Nia / Mara / Julian / Julian | `TL-DISCOVERY-DUE-DILIGENCE` |
| 16–20 | Open invitation | Mara / Nia / Mara / Nia / Mara | `TL-DISCOVERY-HANDSHAKE` |
| 21–25 | Case zero refuses the name | Nia / Julian / Mara / Nia / Mara | `TL-DISCOVERY-NIA-AFTERMATH` |
| 26–29 | The door runs inward | Julian / Mara / Nia / Mara | `TL-DISCOVERY-DOOR-INWARD` |

Movement invariants beyond the global set:

- The December source-side morning is continuous. Under the early apparatus configuration, requested fidelity, context window, and information load used in chapters 1–5, acquisition-to-resolved-output reconstruction latency is reproducibly eight seconds on Mara's receive-only side; Nia experiences no gap. Reprocessing the same raw sample with the same settings reproduces the result, while reduced context or processing degrades or destroys coherence. Eight seconds is not a universal physical constant, and later hardware, algorithms, fidelity choices, noise, confidence requirements, complexity, or information volume may change it.
- The December apparatus has **no transmit stage**. It identifies and locks Nia's person-specific channel/address. The temporary bench transmit path and the later handshake/wanting event belong to 16–20 and carry their own chronology entry, `TL-DISCOVERY-HANDSHAKE`.
- `DEC-002`: Nia holds both roles and the shared identity may be fixed. No entry may resolve whether Mara's later handshake caused the wanting.
- `DEC-012`/`DEC-015`: no Discovery entry uses `ESP` or `Electronic Speech Pairings` as an established term, and no later back-label implies December transmitted.
- Motifs due: `MOT-CHAIN-01` at 13, `MOT-COME-01` at 16. Reveal release: `REVEAL-NIA-SOURCE-CASUALTY` is advanced at 21 and released by Mara's necessarily explicit verification in 23; Nia owns the Chapter 24 refusal and interpretation. `ARC-CHANGE-DISCOVERY-001` corrects the prior Chapter 24 release record because delaying Mara's already verified knowledge would be artificial withholding.
- Composition sits inside `TL-RECORD-PRETRUST-COMPOSITION` for 1–5 and 16–29; the Civic Record Trust does not exist yet.

#### Entries — chapters 1–29

**Active `ArcEntry` records for chapters 1–29: 29.** Written by task 5.2 and approved through the task 12.7 Discovery movement gate. POV load Mara 14 / Nia 9 / Julian 6, longest POV run 2, four outliers (13, 16, 17, 24) against a 25-entry normal floor, `MOT-CHAIN-01` at 13 and `MOT-COME-01` at 16, and `REVEAL-NIA-SOURCE-CASUALTY` advanced at 21, released in Mara's Chapter 23 verification, and answered by Nia's refusal at 24 inside its 21–25 window. Eight entries record `"none"`: 5, 6, 9, 10, 15, 20, 22, and 25.

```json record=ArcEntry schema=1
[
  {
    "chapter": 1,
    "filename": "chapters/discovery-part/discovery-part-001-noise-floor.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "pov_id": "POV-MARA",
    "purpose": "Mara finds repeating structure beneath the array's known noise floor and stops treating her own instrument as the explanation.",
    "hook": "The feature she has spent years calling noise repeats on a schedule, and the schedule is not the array's.",
    "cross_cuts": [
      "CUT-NOISE-FLOOR-HANDOFF"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": true,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DECEMBER-RECEIVE",
      "knowledge_limit": "Mara knows only what the receive-only apparatus logged in December; she has no source identity, no transmit stage, and no later chronology, and she composes this before the Civic Record Trust exists."
    },
    "reveal_ids": []
  },
  {
    "chapter": 2,
    "filename": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "pov_id": "POV-NIA",
    "purpose": "Nia lives an unbroken ordinary December morning at full length, fixing the continuous source side the book never interrupts.",
    "hook": "Her morning closes into an ordinary shift, and the only thing out of place is a sound she cannot say why she remembers.",
    "cross_cuts": [
      "CUT-NOISE-FLOOR-HANDOFF"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": true,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DECEMBER-RECEIVE",
      "knowledge_limit": "Nia recounts a morning she had no reason to think remarkable; she does not know she was received, experiences no gap, and knows nothing of Northline Array or of anyone listening."
    },
    "reveal_ids": []
  },
  {
    "chapter": 3,
    "filename": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "pov_id": "POV-MARA",
    "purpose": "Mara's first verification fails, and the failure locates the reproducible eight-second acquisition-to-resolved-output latency in her configured reconstruction rather than in whatever she is receiving.",
    "hook": "The check she built to kill the result kills the wrong thing, and the eight seconds survive it as hers.",
    "cross_cuts": [
      "CUT-RECONSTRUCTION-LATENCY"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": true,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DECEMBER-RECEIVE",
      "knowledge_limit": "Mara knows the eight-second latency belongs to acquisition-to-resolved-output reconstruction under the tested configuration, that the same raw sample and settings reproduce it, that inadequate context or processing degrades coherence, and that the apparatus cannot transmit; she cannot yet name a person, a place, or a mechanism, and she does not know what later hardware or algorithms may do."
    },
    "reveal_ids": []
  },
  {
    "chapter": 4,
    "filename": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "pov_id": "POV-NIA",
    "purpose": "Nia's morning runs continuous through the same interval, fixing that the source side has no discontinuity at all.",
    "hook": "Her clock, her road call, and her console at ten to seven agree with one another, and the twenty minutes between them hold nothing she would ever have thought to report.",
    "cross_cuts": [
      "CUT-RECONSTRUCTION-LATENCY"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": true,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DECEMBER-RECEIVE",
      "knowledge_limit": "Nia knows her own unbroken sequence of alarm, road call, and console; she has no access to any receiver, any offset, or any observer, and nothing in her account can speak to reception timing."
    },
    "reveal_ids": []
  },
  {
    "chapter": 5,
    "filename": "chapters/discovery-part/discovery-part-005-not-a-message.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "pov_id": "POV-MARA",
    "purpose": "Mara establishes that the reception carries lived experience rather than a message, which turns a signal problem into a living person she has no permission to hear.",
    "hook": "What she is receiving is addressed to no one, which means someone is simply being overheard.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": true,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DECEMBER-RECEIVE",
      "knowledge_limit": "Mara knows the content is experiential and unaddressed; she does not know whose it is, cannot transmit, and has no later result or outcome to reason from."
    },
    "reveal_ids": []
  },
  {
    "chapter": 6,
    "filename": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian audits a funding disclosure and establishes on the record that Mara's receiver has no transmit stage, fixing the boundary every later claim is measured against.",
    "hook": "The disclosure is clean, and the cleanest line in it is the one nobody asked him to check.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Julian knows the disclosure, the hardware description, and the institute's appetite; he has seen no data, no source identity, and no commercial specification."
    },
    "reveal_ids": []
  },
  {
    "chapter": 7,
    "filename": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-NIA",
    "purpose": "Nia's working life stays continuous and concrete, and one unremarkable detail of it belongs to her competence rather than to anyone's experiment.",
    "hook": "Nothing in the day asks to be remembered, and she remembers it anyway.",
    "cross_cuts": [
      "CUT-ORDINARY-DETAIL-MATCH"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Nia knows her own shift and the detail she kept; she does not know she is under verification, has met no one from the array, and still notices no discontinuity."
    },
    "reveal_ids": []
  },
  {
    "chapter": 8,
    "filename": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-MARA",
    "purpose": "Mara repeats the reception, finds the pattern maps onto neural timing, and withholds a provisional source identity from the institute until she can verify it.",
    "hook": "She writes the hypothesis in her log and leaves the space beside it deliberately empty.",
    "cross_cuts": [
      "CUT-ORDINARY-DETAIL-MATCH"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Mara knows the reception repeats and maps onto neural timing and that her identification is provisional; she has no confirmation, no consent, and no contact with the person."
    },
    "reveal_ids": []
  },
  {
    "chapter": 9,
    "filename": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian watches institutional appetite assemble around an unpublished result and finds that his own procedural competence is what makes the appetite efficient.",
    "hook": "The institute's appetite arrives before the result does and already knows what it is worth.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Julian knows the institute's interest and the shape of an unpublished claim; he has not seen the data, the source, or any term sheet."
    },
    "reveal_ids": []
  },
  {
    "chapter": 10,
    "filename": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-MARA",
    "purpose": "Mara accepts that she is listening to a person rather than a place and finds she has no procedure for asking permission of someone she cannot identify.",
    "hook": "There is no form for what she is doing, and the absence of a form is not permission.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1050,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Mara knows she is receiving a person and that no consent procedure exists; she has no verified identity, no transmit path, and no institutional cover."
    },
    "reveal_ids": []
  },
  {
    "chapter": 11,
    "filename": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-MARA",
    "purpose": "Mara demonstrates that small frequency changes track shifts in attention and states the mind-as-field hypothesis for the first time.",
    "hook": "The band moves when the stranger's attention moves, which makes the field a place instead of a figure of speech.",
    "cross_cuts": [
      "CUT-ATTENTION-AND-THE-CALL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Mara knows attention and frequency covary in her recordings; she has no person-specific lock yet, no write capability, and no account of what the field is for."
    },
    "reveal_ids": []
  },
  {
    "chapter": 12,
    "filename": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-NIA",
    "purpose": "Nia works a hard call end to end, and the concentrated attention that carries it is shown as labour and privacy rather than as data.",
    "hook": "She gives the call everything she has, and the only record of that effort is a timestamp.",
    "cross_cuts": [
      "CUT-ATTENTION-AND-THE-CALL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Nia knows the call, the map in her head, and her own fatigue; she has no knowledge of any recording, any hypothesis, or any observer."
    },
    "reveal_ids": []
  },
  {
    "chapter": 13,
    "filename": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-MARA",
    "purpose": "Mara turns the field hypothesis into a repeatable person-specific channel the receive-only apparatus can identify and lock, which converts a stranger into an address.",
    "hook": "The spectrum resolves into something with a body, and the address is still there when she goes back for it.",
    "cross_cuts": [
      "CUT-PERSON-SPECIFIC-RIGHTS"
    ],
    "motif_events": [
      "MOT-CHAIN-01"
    ],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion: the person-specific proof needs experiment, failed control, result, and the immediate recognition that a person has become an address to land in one unbroken sequence.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Mara knows the channel is person-specific and repeatable and that her apparatus can only receive; she has built no transmit path, made no contact, and asked for no consent."
    },
    "reveal_ids": []
  },
  {
    "chapter": 14,
    "filename": "chapters/discovery-part/discovery-part-014-rights-before-names.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian establishes that person-specific reception creates immediate consent and liability exposure, moving the problem out of physics while stopping is still possible.",
    "hook": "He drafts the warning, reads it back, and understands that sending it makes him the one who knew.",
    "cross_cuts": [
      "CUT-PERSON-SPECIFIC-RIGHTS"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1000,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Julian knows the result is person-specific and that the receiver cannot transmit; he does not know who the person is and has no evidence of any write."
    },
    "reveal_ids": []
  },
  {
    "chapter": 15,
    "filename": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian traces the first contact between the institute and the nascent Open Channel Consortium and establishes that the finding will not stay inside a laboratory.",
    "hook": "Somebody alive was always going to find this channel, and the only open question is who will be holding it when they do.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1050,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
      "knowledge_limit": "Julian knows who has begun talking to whom and what they want; he has no term sheet, no page-nine specification, and no knowledge of any transmission."
    },
    "reveal_ids": []
  },
  {
    "chapter": 16,
    "filename": "chapters/discovery-part/discovery-part-016-come-in.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "pov_id": "POV-MARA",
    "purpose": "Mara adds a temporary bench transmit path to the receive-only setup and sends one content-free handshake through the address December identified, calling it knocking rather than entering.",
    "hook": "She sends nothing but the fact of herself, and the difference between knocking and entering is one she decides alone.",
    "cross_cuts": [
      "CUT-HANDSHAKE-AND-TRIAGE"
    ],
    "motif_events": [
      "MOT-COME-01"
    ],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression: the send is one irreversible act, and cutting at the act denies the chapter room to argue itself into justification.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-HANDSHAKE",
      "knowledge_limit": "Mara knows she built a temporary transmit path and sent a content-free handshake through a known address; she does not know whether anything arrived, and she asked no one."
    },
    "reveal_ids": []
  },
  {
    "chapter": 17,
    "filename": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "pov_id": "POV-NIA",
    "purpose": "Nia takes two calls with one available advanced unit and routes against ordinary practice because a certainty arrives that she cannot distinguish from her own judgment, and one person dies.",
    "hook": "She was sure, she routed against practice, and she cannot find the moment the sureness started.",
    "cross_cuts": [
      "CUT-HANDSHAKE-AND-TRIAGE"
    ],
    "motif_events": [],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion: two simultaneous calls, one available advanced unit, the arriving certainty, the routing, and the single documented outcome must land inside one continuous shift.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-HANDSHAKE",
      "knowledge_limit": "Nia knows what she wanted, what she did, and what happened; she has no knowledge of Northline Array, of any transmission, or of any log review, and nothing verbal arrived to trace."
    },
    "reveal_ids": []
  },
  {
    "chapter": 18,
    "filename": "chapters/discovery-part/discovery-part-018-clean-silence.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "pov_id": "POV-MARA",
    "purpose": "Mara waits for an answering signal, logs clean silence, and has to decide what to do with a transmit path she can no longer call theoretical.",
    "hook": "Nothing comes back, and she cannot tell whether that means nothing happened.",
    "cross_cuts": [
      "CUT-UNANSWERED-SILENCE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-HANDSHAKE",
      "knowledge_limit": "Mara knows the handshake left the bench and that no return signal followed; she knows nothing of any effect, any person's day, or any outcome."
    },
    "reveal_ids": []
  },
  {
    "chapter": 19,
    "filename": "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "pov_id": "POV-NIA",
    "purpose": "Nia spends the hours after the call trying to source the certainty she acted on, and finds no memory, habit, or reason that produced it.",
    "hook": "She retraces the whole shift twice and cannot find the place the certainty entered it.",
    "cross_cuts": [
      "CUT-UNANSWERED-SILENCE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-HANDSHAKE",
      "knowledge_limit": "Nia knows the shape of her own certainty and that she cannot account for it; she has no candidate explanation available to her and no contact with anyone who does."
    },
    "reveal_ids": []
  },
  {
    "chapter": 20,
    "filename": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "pov_id": "POV-MARA",
    "purpose": "Mara hears of a documented routing death in the county her reception maps to, cannot rule out her own handshake, and begins carrying a conviction she has no evidence for.",
    "hook": "She has a belief with nothing under it, and she notices how much she wants it to be about her.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-HANDSHAKE",
      "knowledge_limit": "Mara knows her own act, its timing, and a county-level report of one death; she has not verified who her source is, and she has nothing linking the two beyond her own fear."
    },
    "reveal_ids": []
  },
  {
    "chapter": 21,
    "filename": "chapters/discovery-part/discovery-part-021-reconstruction.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "pov_id": "POV-NIA",
    "purpose": "Nia reconstructs the routing decision in full and establishes that no memory of hers generated the certainty, which makes lost self-trust the injury rather than the death alone.",
    "hook": "The reconstruction is complete and still does not contain the moment she became sure.",
    "cross_cuts": [
      "CUT-SOURCE-AND-CASUALTY-JOINED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
      "knowledge_limit": "Nia knows her decision, its outcome, and that she cannot source her own certainty; she does not know she was ever received, has had no dispatch log review, and has met no one from the array."
    },
    "reveal_ids": [
      "REVEAL-NIA-SOURCE-CASUALTY"
    ]
  },
  {
    "chapter": 22,
    "filename": "chapters/discovery-part/discovery-part-022-fundable.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian turns institute and consortium contact into a fundable proposal and records that the work now moves on money rather than on findings.",
    "hook": "The proposal is finished before the science is, and it is the proposal that has a schedule.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
      "knowledge_limit": "Julian knows the commercial trajectory and his own drafting role; he knows nothing of any casualty, any handshake, or any source identity."
    },
    "reveal_ids": []
  },
  {
    "chapter": 23,
    "filename": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "pov_id": "POV-MARA",
    "purpose": "Mara verifies the person-specific match, reaches Nia, learns that the woman whose morning she received is the woman in the documented routing death, and tries to turn her private conviction into a confession.",
    "hook": "The match holds, the two accounts are one woman, and the first thing Mara does with that is talk about herself.",
    "cross_cuts": [
      "CUT-SOURCE-AND-CASUALTY-JOINED",
      "CUT-CONFESSION-REFUSED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
      "knowledge_limit": "Mara knows the verified source match and the documented outcome; she has no evidence that her handshake reached Nia, no standing to claim it did, and no log review."
    },
    "reveal_ids": [
      "REVEAL-NIA-SOURCE-CASUALTY"
    ]
  },
  {
    "chapter": 24,
    "filename": "chapters/discovery-part/discovery-part-024-not-case-zero.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "pov_id": "POV-NIA",
    "purpose": "Nia refuses both unsupported origin accounts, refuses Mara's confession as a claim on her injury, and refuses the name case zero before it can be made official.",
    "hook": "She hands Mara the difference between receiving a signal and losing confidence in your own yes, and hands her nothing else.",
    "cross_cuts": [
      "CUT-CONFESSION-REFUSED"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression: the refusal is one sustained act of speech, and ending on it denies the scene an explanatory aftermath or a softening exchange.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
      "knowledge_limit": "Nia now knows she was the received source and the documented casualty; she knows neither origin account is supported, has no log review, and has no absolution to give."
    },
    "reveal_ids": [
      "REVEAL-NIA-SOURCE-CASUALTY"
    ]
  },
  {
    "chapter": 25,
    "filename": "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "pov_id": "POV-MARA",
    "purpose": "Mara is left holding a conviction she cannot enter anywhere and a refusal she has to obey, and she stops trying to make Nia's injury into her own account.",
    "hook": "She goes back to the bench with nothing settled and one instruction she did not choose.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
      "knowledge_limit": "Mara knows the verified identity, Nia's refusal, and the limits of her own belief; she has no proof of causation and no permission to speak for anyone but herself."
    },
    "reveal_ids": []
  },
  {
    "chapter": 26,
    "filename": "chapters/discovery-part/discovery-part-026-already-outside.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian finds that external interest has already assembled around the result before any public announcement, which removes containment from the list of available choices.",
    "hook": "Three parties already know what he has told no one, and none of them heard it from him.",
    "cross_cuts": [
      "CUT-CONTAINMENT-ALREADY-LOST"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
      "knowledge_limit": "Julian knows who is circling and what they want; he does not know the source's identity, the bench handshake, or any later specification."
    },
    "reveal_ids": []
  },
  {
    "chapter": 27,
    "filename": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "pov_id": "POV-MARA",
    "purpose": "Mara confirms that the apparatus can address a named person as well as receive one, which makes the channel a door rather than a window.",
    "hook": "It can find a person more precisely than it can find a place, and the door runs inward.",
    "cross_cuts": [
      "CUT-ADDRESSABLE-AND-TESTED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
      "knowledge_limit": "Mara knows addressing works on a temporary path and that the write is uncalibrated; she has no origin for anything that arrived in Nia and no architecture beyond her own bench."
    },
    "reveal_ids": []
  },
  {
    "chapter": 28,
    "filename": "chapters/discovery-part/discovery-part-028-named-second.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "pov_id": "POV-NIA",
    "purpose": "Nia agrees to a bounded controlled test on her own terms and establishes that she can identify an arrival only after she has already acted on it.",
    "hook": "She names the arrival correctly, and she names it second.",
    "cross_cuts": [
      "CUT-ADDRESSABLE-AND-TESTED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
      "knowledge_limit": "Nia knows what she agreed to, what she felt, and the order in which she noticed it; she has no instrument access and still no origin for the earlier wanting."
    },
    "reveal_ids": []
  },
  {
    "chapter": 29,
    "filename": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
    "movement": "discovery_part",
    "timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "pov_id": "POV-MARA",
    "purpose": "Mara closes the lab around a problem that is already outside it, turning wonder into a private defense problem and ending the movement on an uninvited crossing.",
    "hook": "She locks a door the channel has never needed, and the thing she wanted to explore has already come the other way.",
    "cross_cuts": [
      "CUT-CONTAINMENT-ALREADY-LOST"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
      "knowledge_limit": "Mara knows the result is addressable and that she can no longer contain it; she has no offer, no specification, no origin account, and she composes this before the Civic Record Trust exists."
    },
    "reveal_ids": []
  }
]
```

### Private_Defense_Part entries — chapters 30–61

Owner: **task 5.3.** Allocation: 32 chapters, 34,500 provisional Prose_Words, Mara 14 / Nia 8 / Julian 10, outlier ceiling 5.

| Range | Cluster | POV emphasis | Timeline_ID |
|---|---|---|---|
| 30–35 | Copper and quiet | Mara / Nia / Mara / Julian / Nia / Mara | `TL-PRIVATE-COPPER` |
| 36–42 | The benevolent offer | Julian / Mara / Nia / Julian / Mara / Julian / Nia | `TL-PRIVATE-OFFER` |
| 43–49 | April, page nine | Mara / Julian / Mara / Julian / Nia / Mara / Julian | `TL-APRIL-TERM-SHEET` |
| 50–55 | Put it in the record | Julian / Mara / Nia / Julian / Mara / Mara | `TL-APRIL-RECORD-ALTERATION` (50), `TL-TRUST-FORMATION` (51), `TL-PRIVATE-RECORD-DEPOSITS` (52–55) |
| 56–61 | The handle inside | Nia / Mara / Julian / Mara / Nia / Mara | `TL-PRIVATE-PROTOCOL` |

Movement invariants beyond the global set:

- The 50–55 cluster is where overlapping chronology windows must be disambiguated. Each chapter names exactly one owner; `TL-RECORD-PRETRUST-DEPOSIT` (52–55) and `TL-TRUST-ROLLING-DEPOSITS` (52, 54) may be referenced only through `record_horizon`.
- Trust formation follows Julian observing alteration of the April negotiation record. Pre-Trust composition precedes later deposit; rolling deposits begin only after formation.
- `Electronic Speech Pairings` may be coined here at the earliest, through Julian or institutional/public language, and stays a disputed simplification — rare in Mara's technical speech, resisted by Nia.
- Mandatory Fluent_Pairing beats in **36–42** (freely chosen benefit, beginning Pair_Calibration) and **56–61** (sustained on-page conversation, Deliberate_Send_Act per contribution, pause/revocation stopping transport, one consent-protocol failure followed by repair, ordinary-speech fallback). Requirement 15.1.
- Consent_State_Metadata and Transport_Metadata are mandatory and semantically opaque; Content_Recording initializes off; a Pairing_Transcript exists only with separate explicit mutual recording consent.
- Motifs due: `MOT-COPPER-01` at 31, `MOT-CHAIN-02` at 45, `MOT-RECORD-01` at 51, `MOT-COME-02` at 61. No knock event in this movement.
- Reveal releases: `REVEAL-BIDIRECTIONAL-ARCHITECTURE` at 45, window 43–49; `REVEAL-CASUALTY-CONSEQUENCE` at 52, window 50–55. Page nine confirms architectural write capability; it is never evidence that Mara's December rig transmitted.

#### Entries — chapters 30–61

**Active `ArcEntry` records for chapters 30–61: 32.** Written by task 5.3. POV load Mara 14 / Nia 8 / Julian 10, longest POV run 2 counting across the 29/30 boundary, four outliers (45, 50, 56, 61) against a 27-entry normal floor, `MOT-COPPER-01` at 31, `MOT-CHAIN-02` at 45, `MOT-RECORD-01` at 51, and `MOT-COME-02` at 61, `REVEAL-BIDIRECTIONAL-ARCHITECTURE` advanced at 44, released at 45, and completed at 46 inside its 43–49 window, and `REVEAL-CASUALTY-CONSEQUENCE` released at 52, its owning POV's chapter, and further advanced at 53 inside its 50–55 window. Chapters 50, 51, and 52–55 each name exactly one of the overlapping record chronologies; `TL-RECORD-PRETRUST-DEPOSIT` appears only as chapter 54's `record_horizon`, and `TL-TRUST-ROLLING-DEPOSITS` is never named as a `timeline_id`. Six entries record `"none"`: 37, 39, 41, 49, 55, and 59.

The selected fluent pair identities are Mara and Nia, whose joint calibration begins at 40 and reaches sustained fluency at 56–61, recorded as `TL-PAIR-MARA-NIA-CALIBRATION` and then `TL-PRIVATE-PROTOCOL`. Every other pairing in the movement is carried by named non-viewpoint supporting participants inside an existing POV chapter: **Ada Ferris** (`CHAR-005`) and her daughter **Lena Ferris** (`CHAR-006`) hold the pairing Julian watches at 36, the bench session Mara measures at 37, and the working passage at 41, all under `TL-PAIR-CLINICAL-BENEFIT`; the dispatchers **Tomas Reyner** (`CHAR-007`) and **Cora Baird** (`CHAR-008`) hold the demonstration Nia watches at 38 under `TL-PAIR-DISPATCH-DEMONSTRATION`. The Ferris pair recurs rather than being replaced by a third demonstration pair: the benefit Julian first sees as clinical returns at 41 as ordinary paid work, where Ada's language and Lena's expressive speech carry a passage neither could carry alone. Julian observes and holds records and never pairs, which matches his roster position. The six supporting Character IDs create no POV, no Voice Brief, and no chapter; no operative, sender, or adversary POV is created, and the 14/8/10 load is unchanged.

```json record=ArcEntry schema=1
[
  {
    "chapter": 30,
    "filename": "chapters/private-defense-part/private-defense-part-030-something-came-in.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-MARA",
    "purpose": "Something arrives in Mara that she did not invite and cannot attribute, and the woman who opened the channel becomes the first name on her own list of people who need protecting.",
    "hook": "She turns back to the notebook that found the field and begins drawing a cage in it, a few pages after the door.",
    "cross_cuts": [
      "CUT-ARRIVAL-AND-THE-ROOM"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Mara knows only that something reached her without being asked and left no words, no address she can trace, and no sender; she cannot rule out her own mind, has no offer and no specification, and composes this before the Civic Record Trust exists."
    },
    "reveal_ids": []
  },
  {
    "chapter": 31,
    "filename": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-NIA",
    "purpose": "Nia stands inside the first measured quiet and learns what it is worth, and in the same minute learns that every ordinary room she has ever slept in was permeable.",
    "hook": "The relief is the best thing she has felt in months, and it is also a measurement of how open every other room has always been.",
    "cross_cuts": [
      "CUT-ARRIVAL-AND-THE-ROOM"
    ],
    "motif_events": [
      "MOT-COPPER-01"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Nia knows what the shielded room does to her own experience and nothing about how it was built or what it cost; she still has no origin for the certainty that arrived in her, and no trust exists yet to hold her account."
    },
    "reveal_ids": []
  },
  {
    "chapter": 32,
    "filename": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-MARA",
    "purpose": "Mara solves the seam and door problem by refusing to build a sealed box, fixing the doctrine that a room without a door is not private but gone.",
    "hook": "She specifies a handle instead of a wall, and puts it on the inside where she cannot reach it.",
    "cross_cuts": [
      "CUT-SEALED-ROOM-AND-A-LIFE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Mara knows the measured attenuation of mesh, seams, and a closed door, and that shielding is local; she does not know what the room costs the person who has to live inside it, and she has no legal or social answer to anything."
    },
    "reveal_ids": []
  },
  {
    "chapter": 33,
    "filename": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian separates reception, transmission, and consent into three legally distinct acts, then finds the Open Channel Consortium has already written assent into its service defaults.",
    "hook": "His distinction is sound, and the enrollment form he is handed has already answered it on everyone's behalf.",
    "cross_cuts": [
      "CUT-CONSENT-AS-DEFAULT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Julian knows the consortium's draft terms, the shape of its default enrollment, and his own three-part distinction; he has read no interface specification, holds no commercial offer, and has custody of nothing."
    },
    "reveal_ids": []
  },
  {
    "chapter": 34,
    "filename": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-NIA",
    "purpose": "Nia audits what she can and cannot do inside a sealed room and establishes that the copper answer protects her by removing the work that makes her herself.",
    "hook": "She can be safe or she can take the call, and the room is very clear that she cannot do both.",
    "cross_cuts": [
      "CUT-SEALED-ROOM-AND-A-LIFE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Nia knows exactly which parts of her working life the room takes and what quiet is worth to her; she knows nothing of any commercial proposal and cannot say whether the room would have stopped what already reached her."
    },
    "reveal_ids": []
  },
  {
    "chapter": 35,
    "filename": "chapters/private-defense-part/private-defense-part-035-a-private-no.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-COPPER",
    "pov_id": "POV-MARA",
    "purpose": "Mara accepts that copper gives one person a private no and cannot give anyone a public one, which is the gap the consortium's approach walks straight into.",
    "hook": "A car she does not recognize is at the Northline Array gate before she has finished admitting the room is not an answer.",
    "cross_cuts": [
      "CUT-CONSENT-AS-DEFAULT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-COPPER",
      "knowledge_limit": "Mara knows the room works, does not scale, and that Julian's distinction has already met a default; she does not know what the visitors want, has seen no term sheet, and composes this before the Civic Record Trust exists."
    },
    "reveal_ids": []
  },
  {
    "chapter": 36,
    "filename": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian watches an authorized pairing carry deliberate speech between Ada Ferris, who has lost expressive speech, and her living daughter Lena, and hears the Open Channel Consortium name the whole capability Electronic Speech Pairings in the same hour.",
    "hook": "The benefit in front of him is real, and the phrase they have chosen for it is already doing work the mechanism does not support.",
    "cross_cuts": [
      "CUT-DEMONSTRATION-AND-THE-FORM"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Julian knows what one calibrated pair did in front of him, that both participants consented and could stop, and how the consortium describes it publicly; he has no interface specification and no way to test whether the new name covers more than the pairing he saw."
    },
    "reveal_ids": []
  },
  {
    "chapter": 37,
    "filename": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-MARA",
    "purpose": "Mara tests the Ferris pair's protocol against her own field model and confirms the send gate holds, so unoffered thought stays private and the capability in front of her is not the one she feared.",
    "hook": "Everything she can measure says the pairing is honest, and she catches herself wanting that to settle a question it cannot reach.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Mara knows what she measured at Ada and Lena Ferris's bench: two living people, joint calibration unique to them, and a deliberate act behind every contribution; she has not seen the deployment architecture and knows nothing about what a network would be permitted to do."
    },
    "reveal_ids": []
  },
  {
    "chapter": 38,
    "filename": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-NIA",
    "purpose": "Nia sees Tomas Reyner and Cora Baird work one bad incident paired, better than two radios could, and then reads the enrollment form that bundles her consent to pair with a default to record.",
    "hook": "The demonstration is the best argument anyone has made to her, and it is printed on the same page as the box she would have to un-tick.",
    "cross_cuts": [
      "CUT-DEMONSTRATION-AND-THE-FORM"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Nia knows what Reyner and Baird did on one incident and exactly how the enrollment form is worded; she cannot compare either to what happened to her, because nothing that happened to her involved consent, calibration, or a form."
    },
    "reveal_ids": []
  },
  {
    "chapter": 39,
    "filename": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian traces how a genuine clinical benefit is being converted into a saleable platform and decides the consent boundary can be made contractual.",
    "hook": "He agrees to carry a term sheet, and what persuades him is not the money but the sentence he believes he can write into it.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Julian knows the consortium's commercial plan, its enrollment defaults, and his own drafting instincts; he has never seen the interface specification and believes, without having checked, that a write path is a feature that can be contracted away."
    },
    "reveal_ids": []
  },
  {
    "chapter": 40,
    "filename": "chapters/private-defense-part/private-defense-part-040-first-calibration.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-MARA",
    "purpose": "Mara and Nia begin their own joint calibration, and Mara discovers that offering one deliberate sentence is effortful, refusable, and nothing like what she did on the bench in the winter.",
    "hook": "The first thing that crosses between them is a sentence Nia decides to hand over, and Mara has to sit still with how different that is.",
    "cross_cuts": [
      "CUT-CALIBRATION-AND-THE-UNCALIBRATED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Mara knows what her own pair-specific calibration required, that consent-state and transport metadata are kept, and that content recording is off and neither of them has asked to change it; the contrast tells her nothing about what reached Nia in the winter, and she knows it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 41,
    "filename": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian watches Ada and Lena Ferris work as paid interpreters, pairing through a passage neither could carry alone, and writes down the exact benefit the consortium is entitled to claim from it.",
    "hook": "He records what the pairing genuinely does in one line, and then records the four larger claims the brochure builds on top of it.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Julian knows what the two living calibrated interpreters accomplished in front of him and what the consortium's material asserts; he does not know how the deployed network is built, and he has no basis yet to doubt the distance between a demonstration and a product."
    },
    "reveal_ids": []
  },
  {
    "chapter": 42,
    "filename": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-OFFER",
    "pov_id": "POV-NIA",
    "purpose": "Nia refuses the consortium's term and its broad-form enrollment, and establishes that a calibrated conversation proves by contrast that what arrived in her was never speech and still has no traceable source.",
    "hook": "She can now describe precisely what a consented sentence feels like, which is how she knows the thing that took her judgment was not one.",
    "cross_cuts": [
      "CUT-CALIBRATION-AND-THE-UNCALIBRATED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-OFFER",
      "knowledge_limit": "Nia knows what a deliberate offered contribution feels like from inside, and refuses both accounts of where her earlier certainty came from; the comparison gives her a vocabulary and no origin, and she declines to let one institutional name cover both."
    },
    "reveal_ids": []
  },
  {
    "chapter": 43,
    "filename": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-MARA",
    "purpose": "Representatives arrive in April with a term sheet and a pen, and Mara records honestly how much of the promised good she believed before she had read anything.",
    "hook": "They tell her nobody on earth would be a stranger again, and the worst part of the afternoon is that she wants it to be true.",
    "cross_cuts": [
      "CUT-PROMISE-AND-THE-CASE"
    ],
    "motif_events": [],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion: the April offer is the movement's central temptation and has to be dramatized as one continuous negotiation, so that the clinical case, the funding pressure, and counsel's operability trap land in real time on Mara rather than inside narrated summary.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Mara knows the offer as it was presented and her own appetite for it; she has not opened the interface specification, does not know whose case the pitch rests on, and composes this before the Civic Record Trust exists."
    },
    "reveal_ids": []
  },
  {
    "chapter": 44,
    "filename": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian negotiates what he believes is a binding limit on write capability and secures the assurances that make the deal defensible to himself.",
    "hook": "He gets the language he asked for, initials the page, and the specification he has not read is lying on the table in front of him.",
    "cross_cuts": [
      "CUT-CONSTRAINABLE-CLAUSE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Julian knows the negotiated terms, the assurances given across the table, and that a write path exists as a clause; he does not yet know whether the capability is a setting or a structure, and nothing he has been shown answers that."
    },
    "reveal_ids": [
      "REVEAL-BIDIRECTIONAL-ARCHITECTURE"
    ]
  },
  {
    "chapter": 45,
    "filename": "chapters/private-defense-part/private-defense-part-045-page-nine.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-MARA",
    "purpose": "Mara reads page nine of the interface specification, finds the line transmit enable, and the wire she built to hold something out becomes a wire that runs both directions.",
    "hook": "One printed line makes the assurance on the table worthless, and she has not put the page down yet.",
    "cross_cuts": [
      "CUT-CONSTRAINABLE-CLAUSE",
      "CUT-ARCHITECTURE-NOT-OPTION"
    ],
    "motif_events": [
      "MOT-CHAIN-02"
    ],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression to the single act of reading one line, so the reversal lands in about the time it takes to read it.",
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Mara knows what the specification prints and what write-capable architecture would permit; she does not know whether the line can be struck, and it says nothing about December, which had no transmit stage, or about what reached Nia."
    },
    "reveal_ids": [
      "REVEAL-BIDIRECTIONAL-ARCHITECTURE"
    ]
  },
  {
    "chapter": 46,
    "filename": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian traces transmit enable back through the hardware description and establishes that the write path is architectural rather than optional, so there is no clause to strike.",
    "hook": "The protection he negotiated turns out to be a careful sentence about a thing that cannot be switched off.",
    "cross_cuts": [
      "CUT-ARCHITECTURE-NOT-OPTION"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "revised",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Julian knows the specification, the hardware description, and that his negotiated limit describes a setting the architecture does not have; he does not know who will deploy it, and none of it speaks to the origin of anything that happened in the winter."
    },
    "reveal_ids": [
      "REVEAL-BIDIRECTIONAL-ARCHITECTURE"
    ]
  },
  {
    "chapter": 47,
    "filename": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-NIA",
    "purpose": "Nia finds her own incident inside the deployment justification and establishes that her injury has been used to argue for the thing that produced it, without anyone asking her.",
    "hook": "She is an appendix, and the appendix is the reason the program is considered urgent.",
    "cross_cuts": [
      "CUT-PROMISE-AND-THE-CASE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Nia knows how her incident is characterized in the consortium's material and that no one asked her; she does not know how the architecture works, and the document's account of who caused her certainty is an assertion she refuses."
    },
    "reveal_ids": []
  },
  {
    "chapter": 48,
    "filename": "chapters/private-defense-part/private-defense-part-048-the-refusal.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-MARA",
    "purpose": "Mara refuses the offer in the room, in exact language, naming the specific line and the specific reason so the refusal cannot later be read as reluctance.",
    "hook": "She says no in words she chooses very carefully, and the minute-taker writes considerably fewer of them down.",
    "cross_cuts": [
      "CUT-REFUSAL-AND-THE-MINUTES"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Mara knows what she said, why she said it, and that refusing costs her the funded path she has been on; she does not know what the record of the meeting will say, and no independent custody exists to hold it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 49,
    "filename": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian files the negotiation, admits to himself that he has been representing a position he no longer holds, and leaves the institutional record to the people who own the system.",
    "hook": "He signs the file off believing the disagreement is preserved inside it.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1050,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-TERM-SHEET",
      "knowledge_limit": "Julian knows what was said in the room and what he submitted; he has not compared his submission to the circulated minutes and has no reason yet to think the two differ."
    },
    "reveal_ids": []
  },
  {
    "chapter": 50,
    "filename": "chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-APRIL-RECORD-ALTERATION",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian reads the circulated minutes, finds Mara's refusal softened and the page-nine line summarized out, and his objection to a deal becomes a problem about custody.",
    "hook": "One sentence he watched her say is now a sentence about her general concerns.",
    "cross_cuts": [
      "CUT-REFUSAL-AND-THE-MINUTES"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": 520,
    "outlier_purpose": "Compression to the discovery of a single altered paragraph, so the alteration is the whole chapter and nothing dilutes it.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-APRIL-RECORD-ALTERATION",
      "knowledge_limit": "Julian knows what the minutes say and what he heard in the room; he cannot prove who softened it or whether it was deliberate, and no independent archive yet exists to hold the difference."
    },
    "reveal_ids": []
  },
  {
    "chapter": 51,
    "filename": "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-TRUST-FORMATION",
    "pov_id": "POV-MARA",
    "purpose": "Mara insists that transmit enable and her refusal be preserved in their exact words rather than summarized, and Julian answers by founding the Civic Record Trust with her insistence as its first deposit.",
    "hook": "Her demand becomes an institution inside a week, and she is not certain that counts as winning.",
    "cross_cuts": [
      "CUT-PRESERVED-AND-TRANSFERRED"
    ],
    "motif_events": [
      "MOT-RECORD-01"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-FORMATION",
      "knowledge_limit": "Mara knows what she demanded, what the softened minutes did to it, and that a custodial trust now exists with witness-controlled conditions; she does not know whether custody protects anything, and she has been told plainly that provenance is not truth."
    },
    "reveal_ids": []
  },
  {
    "chapter": 52,
    "filename": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "pov_id": "POV-NIA",
    "purpose": "Nia deposits her own first-person account under embargo conditions she writes herself, and requires the timestamped dispatch record to be deposited beside it.",
    "hook": "She hands over the one document that could convict her and specifies exactly who may open it and when.",
    "cross_cuts": [
      "CUT-DEPOSIT-AND-THE-TIMESTAMPS"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
      "knowledge_limit": "Nia composes this as one of the first rolling witness deposits accepted after formation and knows only her own account, her own conditions, and that the logs exist; she has not been told what the timestamps establish, and she still refuses both accounts of where her certainty came from."
    },
    "reveal_ids": [
      "REVEAL-CASUALTY-CONSEQUENCE"
    ]
  },
  {
    "chapter": 53,
    "filename": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "pov_id": "POV-JULIAN",
    "purpose": "The deposited timestamps establish that the death was already unsurvivable before Nia routed the unit, and Julian enters the adversary attribution because it is the only account an institution can accept.",
    "hook": "The record clears her of the outcome, says nothing about whose certainty it was, and he watches the relief fail to arrive.",
    "cross_cuts": [
      "CUT-DEPOSIT-AND-THE-TIMESTAMPS"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
      "knowledge_limit": "Julian knows what the timestamps establish about the outcome and that they are silent on authorship; he privately knows the attribution he enters is an inference rather than proof, custody cannot correct it into fact, and Nia has refused it along with the other account."
    },
    "reveal_ids": [
      "REVEAL-CASUALTY-CONSEQUENCE"
    ]
  },
  {
    "chapter": 54,
    "filename": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "pov_id": "POV-MARA",
    "purpose": "Mara transfers the Discovery-era lab logs and voice memoranda into custody with their original dates and provenance intact, establishing that the sources are older than the archive that now holds them.",
    "hook": "The oldest thing she deposits is a recording of her own voice being delighted, and she leaves it in.",
    "cross_cuts": [
      "CUT-PRESERVED-AND-TRANSFERRED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "knowledge_limit": "Mara knows the composition dates of records she made before any trust existed and what a deposit does and does not warrant; provenance is preserved, truth is not certified, and nothing in the transfer speaks to what reached Nia."
    },
    "reveal_ids": []
  },
  {
    "chapter": 55,
    "filename": "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "pov_id": "POV-MARA",
    "purpose": "Institutional pressure moves the work to a parallel emergency program, and Mara learns that her refusal has cost her the instruments she needs to keep testing anything at all.",
    "hook": "Her badge still opens the building and no longer opens the room with the array in it.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1050,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
      "knowledge_limit": "Mara knows which instruments she has lost and which program now holds them; she does not know what the parallel program intends to build and has no visibility into it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 56,
    "filename": "chapters/private-defense-part/private-defense-part-056-ask-first.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-NIA",
    "purpose": "Nia authors the working protocol and carries the first sustained fluent conversation with Mara, in which every contribution crosses only behind a deliberate send act and one pause stops transport mid-exchange.",
    "hook": "She pauses in the middle of a sentence she was sending, the channel stops where she stopped it, and the rest of the sentence stays hers.",
    "cross_cuts": [
      "CUT-PROTOCOL-AND-THE-STALE-STATE"
    ],
    "motif_events": [],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion to hold the movement's first sustained protocol conversation at full length, including current consent state, send gating, visible acknowledgment, and a pause that stops transport.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Nia knows her own consent state, what she chose to offer, and that consent-state and transport metadata are kept while content recording stays off and unrequested; she cannot know what Mara did not offer, and no transcript exists of anything either of them said."
    },
    "reveal_ids": []
  },
  {
    "chapter": 57,
    "filename": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-MARA",
    "purpose": "A stale, overbroad consent state lets one contribution cross that Nia had not currently authorized, and Mara has to accept that the protocol failed on the exact principle it exists to protect.",
    "hook": "Revocation stops the channel in the same second, and there is nothing left to examine, which is both the failure and the only part working correctly.",
    "cross_cuts": [
      "CUT-PROTOCOL-AND-THE-STALE-STATE",
      "CUT-FAILURE-WITHOUT-CONTENT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Mara knows the session's consent state was older and broader than the act it permitted and that transport stopped immediately on revocation; she cannot recover what crossed, and nothing about the failure speaks to the winter."
    },
    "reveal_ids": []
  },
  {
    "chapter": 58,
    "filename": "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian records the failure from consent-state and transport metadata alone, resigns his consortium representation, and secures the deposits under a repaired rule that separates pairing, sending, and recording consent.",
    "hook": "He can prove exactly when the channel should have closed and can never prove what went through it, and he writes the rule out of that gap.",
    "cross_cuts": [
      "CUT-FAILURE-WITHOUT-CONTENT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Julian knows session timing, consent state, and integrity events, and knows that metadata is semantically opaque; content recording was never enabled, so no transcript exists, and he holds nothing that could reconstruct what crossed."
    },
    "reveal_ids": []
  },
  {
    "chapter": 59,
    "filename": "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-MARA",
    "purpose": "Clipping and latency degrade a later session, and the repaired protocol surfaces the integrity error, requires confirmation and a retry, and drops the pair back to ordinary spoken speech instead of guessing.",
    "hook": "The channel offers her a sentence it is not sure of, and she answers it with her mouth.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Mara knows the measured latency, the clipped contribution, and that the protocol refused to complete it; she cannot know what the degraded fragment was meant to be, and the fallback is spoken words in a shared room."
    },
    "reveal_ids": []
  },
  {
    "chapter": 60,
    "filename": "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-NIA",
    "purpose": "Nia demonstrates that fluency grants no access to unoffered thought, and establishes that copper rooms are spreading at the same rate as reports of arrivals nobody invited.",
    "hook": "She holds a whole argument back while talking easily, then reads the third report this month from someone with no room to stand in.",
    "cross_cuts": [
      "CUT-ENCLOSURE-AND-THE-PUBLIC"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Nia knows what she kept and what she offered, and knows the reports she has read secondhand; she cannot verify who or what stands behind any of them, and she will not treat a pattern as proof of a sender."
    },
    "reveal_ids": []
  },
  {
    "chapter": 61,
    "filename": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md",
    "movement": "private_defense_part",
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "pov_id": "POV-MARA",
    "purpose": "Mara turns the invitation into an operating rule of asking, taking the current answer, leaving the handle inside, and stopping when the answer changes, while a synchronized incident shows in the same day that private rooms and one-to-one pairs cannot defend public life.",
    "hook": "The rule is finished and correct, and it protects everyone who has a room, which is the smaller half of the people it needs to protect.",
    "cross_cuts": [
      "CUT-ENCLOSURE-AND-THE-PUBLIC"
    ],
    "motif_events": [
      "MOT-COME-02"
    ],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion to close the movement on both halves of its result: a complete conditional invitation and the synchronized incident proving the private answer does not scale.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-PRIVATE-PROTOCOL",
      "knowledge_limit": "Mara knows the protocol works between two consenting calibrated people and knows what happened in several places at once that day; she cannot say who caused it, has no defense that reaches past a shielded room, and does not know what the parallel program is building."
    },
    "reveal_ids": []
  }
]
```

### Mindwars_Part entries — chapters 62–112

Owner: **task 5.4.** Allocation: 51 chapters, 59,000 provisional Prose_Words, Mara 21 / Nia 14 / Julian 16, outlier ceiling 8. Longest movement by words, fastest turnover, tightest threading.

| Range | Cluster | POV emphasis | Timeline_ID |
|---|---|---|---|
| 62–69 | No first shot | Nia / Mara / Julian / Nia / Mara / Julian / Mara / Julian | `TL-MINDWARS-ONSET` |
| 70–77 | Mirror of the signal | Julian / Mara / Mara / Nia / Mara / Nia / Julian / Nia | `TL-MINDWARS-COUNTERPHASE` |
| 78–85 | A shield can enter | Nia / Julian / Mara / Mara / Julian / Nia / Mara / Mara | `TL-MINDWARS-SHIELD` |
| 86–93 | Territory | Julian / Mara / Nia / Julian / Mara / Nia / Julian / Mara | `TL-MINDWARS-TERRITORY` |
| 94–101 | The affected area in the model | Nia / Mara / Julian / Mara / Nia / Julian / Mara / Mara | `TL-NULL-DECISION` |
| 102–108 | Null night | Nia / Mara / Julian / Nia / Mara / Julian / Mara | `TL-NULL-NIGHT` |
| 109–112 | The history of quiet | Julian / Nia / Julian / Mara | `TL-POSTNULL-HISTORY` |

Movement invariants beyond the global set:

- **All seven null-night entries (102–108) carry the single `timeline_id` `TL-NULL-NIGHT`** and are joined by reciprocal, non-redundant Cross Cuts. This is the book's tightest compressed-clock cluster. No POV enters Safiya's home.
- 86–93 earns the title's binding reversal from `DEC-011`: inherited maps point outward to space, but the human mind proves to be the frontier, people the shore and territory, humanity the crossed rather than the crosser. The Mindwars reveal this; they are not an alternate title or the book's whole meaning.
- Chapter 73 is where the authorization question is asked and answered, carries `MOT-KNOCK-01` and `MOT-YES-01`, carries a Fluent_Pairing beat in which Nia and Mara coordinate her conditions over their own consented channel one deliberately sent contribution at a time, and establishes the concrete physical vocabulary for a cancellation field experienced from inside. The channel and the field are opposites in the room — two people, addressed, consented, revocable, carrying only what is offered, against one unaddressed field that subtracts — and no character remarks on the contrast. Under `DEC-017`, **no entry purpose or hook in 62–112 may have Mara, Nia, or Julian state the parallel** between that consented bounded cancellation and the later area-scale null. The silence runs through Chapter 123 and is characterization, not withheld information.
- Mandatory Fluent_Pairing beats in **70–77** (73, 74, 75, 77), **78–93** (81, 82, 88, 89, 91), and **94–108** (94, 98, 102, 104, 105). Every session belongs to an existing Mara, Nia, or Julian chapter; named non-viewpoint supporting participants and deposited records carry the rest. Requirement 15.1.
- Traffic-analysis discoveries in 78–93 expose only Consent_State_Metadata and Transport_Metadata patterns, never unrecorded semantic content (Requirement 15.4). No group mind, hive mind, mass mind reading, transferred calibration, or provenance proof anywhere.
- Null extent uses the canonical wording **an affected area canonically described as three counties wide**. No geometric radius is derived, no county is named, and the country stays unnamed.
- Active defender counterphase transmission and rhetorical collective declaration are confined to this movement.
- 109–112 completes `DEC-007`: Nia stops needing the wanting's origin and regains usable self-trust without deciding causation, forgiving Mara, or validating Julian's archive. Both origin accounts stay `unverified`. Under `DEC-005`, conditioned provenance-preserving Trust releases begin contesting official summaries with no unified inquiry, no complete-holdings disclosure, and no correction of the first-casualty attribution.
- **`DEC-018` planning obligation — uncounted private civilian loss, 109–112.** The class of loss the null produced in ordinary private life must be made vivid inside Chapters 109–114 **before** Safiya's Chapter 118 account. The Mindwars half of that obligation falls on 109–112, where Julian holds 109 and 111 and Nia holds 110: the history of quiet is also the first place where losses that no instrument recorded and no institution counted arrive as specific people rather than as a category. Strict boundaries: this is done **without Safiya's POV**, which still begins at 115; without entering Safiya's home, which global invariant 24 already forbids; without naming, describing, or foreshadowing her particular loss; and without pre-empting `REVEAL-SAFIYA-TUESDAY-LOSS`, which still releases at 118 inside its unchanged 118–119 window and stays owned by `POV-SAFIYA`. The people whose losses appear here are other civilians, none of whom is Safiya, connected to her by nothing but the same field. Under the `DEC-018` supporting canon in [`canon-bible.md`](canon-bible.md) a private two-person language layer is already an established class of thing that can be lost, so these chapters may draw on the class without inventing it and without connecting Ada and Lena Ferris to anyone in the Coda. This is a drafting obligation carried by this section, not an `ArcEntry` field, and it creates no `Reveal`, `Motif_Event`, `CrossCut`, or `Literal_Phrase_Constraint`.
- Motifs due: `MOT-COPPER-02` at 70, `MOT-KNOCK-01` and `MOT-YES-01` at 73, `MOT-COME-03` at 74, `MOT-RADIUS-01` at 101, `MOT-RECORD-02` at 109. Counterphase is chain context only — no `MOT-CHAIN-04`.
- Reveal releases: `REVEAL-COUNTERPHASE-TRANSMITS` at 72, window 70–77; `REVEAL-AFFECTED-AREA-EXTENT` at 96, window 94–101.

#### Entries — chapters 62–112

**Active `ArcEntry` records for chapters 62–112: 51.** Written by task 5.4. POV load Mara 21 / Nia 14 / Julian 16, longest POV run 2 counting across the 61/62 boundary, eight outliers (72, 103, 105, and 107 compressed; 73, 90, 101, and 108 expanded) against a 43-entry normal floor, `MOT-COPPER-02` at 70, `MOT-KNOCK-01` and `MOT-YES-01` at 73, `MOT-COME-03` at 74, `MOT-RADIUS-01` at 101, and `MOT-RECORD-02` at 109, `REVEAL-COUNTERPHASE-TRANSMITS` advanced at 71, released at 72, and completed at 73 inside its 70–77 window, and `REVEAL-AFFECTED-AREA-EXTENT` advanced at 95, released at 96, and completed at 101 inside its 94–101 window. All seven null-night entries name `TL-NULL-NIGHT` and each participates in exactly two of that cluster's seven Cross Cuts. `TL-TRUST-ROLLING-DEPOSITS` appears only as the `record_horizon` of chapters 62 and 73 and `TL-TRUST-CONDITIONED-RELEASES` only as the `record_horizon` of chapter 110; neither is ever named as a `timeline_id`. Four entries record `"none"`: 66, 85, 100, and 112.

The fluent pair carried forward from Private_Defense is Mara and Nia, whose channel coordinates the consented bounded test at 73, 74, and 75, meets its operational limit at 77, supplies the movement's one recorded session at 88 under separate explicit mutual consent switched off again afterward, and holds through the decision sequence at 94 and 98. Every other pairing belongs to named non-viewpoint supporting participants inside an existing POV chapter: the protective-network operators **Idris Vane** (`CHAR-009`) and **Rhea Osei** (`CHAR-010`), separately calibrated with Mara at 81 and 84 and calibrated with each other on the channel whose traffic Julian reads at 82 and whose recording state he disputes at 89; the dispatcher **Tomas Reyner** (`CHAR-007`) partnered with Nia at 91; and Reyner with **Cora Baird** (`CHAR-008`) volunteering paired at Nia's consent shelter at 102 and 105. Mara's separate calibration with each operator is the mechanism's own limit made visible: coverage grows only as fast as consenting pairs, which is the accounting Chapter 84 performs. No calibration is inherited, transferred, or extended to a third participant, Julian holds records and never pairs, and no operative, sender, adversary, archive, or simulation POV is created.

Each session is dramatized inside the cluster chronology its own chapter owns, and each is separately classified in [`canon-bible.md`](canon-bible.md) as a `mode: PAIR` entry overlapping that window — `TL-PAIR-MARA-NIA-COUNTERPHASE`, `TL-PAIR-MARA-NIA-FLUENCY-LIMIT`, `TL-PAIR-OPERATOR-SHIFT-VANE`, `TL-PAIR-OPERATOR-TRAFFIC`, `TL-PAIR-OPERATOR-SHIFT-OSEI`, `TL-PAIR-MARA-NIA-RECORDED-SESSION`, `TL-PAIR-DISPATCH-OPERATIONS`, `TL-PAIR-MARA-NIA-NULL-DECISION`, `TL-PAIR-SHELTER-INTAKE`, and `TL-PAIR-NULL-NIGHT-COORDINATION`. None of them is ever a second `timeline_id` here: every entry in 62–112 still names exactly one owning scene chronology. Where a paired channel coordinates a cancellation — 73–75 and 104 — the cancellation keeps its own `mode: CANCEL` record and the channel keeps its own, because one event carries one mode.

Under `DEC-017` no `purpose`, `hook`, or `knowledge_limit` in this block has Mara, Nia, or Julian connect the consented bounded cancellation of Chapter 73 to the area-scale null of 102–108. Chapter 73 carries the concrete inside-the-field vocabulary and the question asked and answered; Chapter 108 carries the same operation with nobody to ask and no question anywhere in it. No Cross Cut joins 73 to any null-night chapter, and no Motif_Event, Literal_Phrase_Constraint, or `Reveal` is created for the parallel.

```json record=ArcEntry schema=1
[
  {
    "chapter": 62,
    "filename": "chapters/mindwars-part/mindwars-part-062-not-only-me.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-NIA",
    "purpose": "Nia reads the first reports of arrivals in strangers, recognizes her own winter inside them, and writes her own account into custody on her own conditions rather than let a summary speak for her.",
    "hook": "She attaches her conditions to the deposit, and the reports have already proved the one thing she never wanted proved, that she was not the only one.",
    "cross_cuts": [
      "CUT-HER-ACCOUNT-AND-THEIR-FILE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
      "knowledge_limit": "Nia knows her own experience, the scattered reports she has read, and the conditions she attaches to her deposit; she has no count, no pattern, and no sender, and she still refuses both accounts of where her certainty came from."
    },
    "reveal_ids": []
  },
  {
    "chapter": 63,
    "filename": "chapters/mindwars-part/mindwars-part-063-name-a-flag.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-MARA",
    "purpose": "Mara is asked to name an attacker and refuses to convert her measurements into public certainty, which is the one thing an emergency actually wants from a scientist.",
    "hook": "She gives them the physics and declines the flag, and the room decides she is being difficult rather than accurate.",
    "cross_cuts": [
      "CUT-A-FLAG-AND-A-CATEGORY"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Mara knows what her instruments show about addressed nonsemantic writes and nothing at all about who sends them; her private conviction about her own later handshake stays out of the room, and no measurement she holds supports it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 64,
    "filename": "chapters/mindwars-part/mindwars-part-064-an-infrastructure-problem.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian watches emergency authorities open a file that treats mental autonomy as infrastructure, and finds the file will accept only one account of who is doing this.",
    "hook": "The form has a field for the adversary and no field for uncertainty, and he fills it in anyway.",
    "cross_cuts": [
      "CUT-HER-ACCOUNT-AND-THEIR-FILE",
      "CUT-DEMONSTRATION-CASE-REFUSED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Julian knows how the emergency classification is written and which account it will hold; he privately knows the attribution he enters is inference rather than proof, and he has no evidence about any sender."
    },
    "reveal_ids": []
  },
  {
    "chapter": 65,
    "filename": "chapters/mindwars-part/mindwars-part-065-not-a-demonstration.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-NIA",
    "purpose": "The emergency program asks Nia to stand as its demonstration case, and her refusal costs her the standing that cooperating would have bought.",
    "hook": "They want the case and not the person, so she keeps the person and loses the access.",
    "cross_cuts": [
      "CUT-DEMONSTRATION-CASE-REFUSED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Nia knows what the program is asking of her and what refusing costs; she does not know what it has measured, and she will not let either origin account be presented as settled on her behalf."
    },
    "reveal_ids": []
  },
  {
    "chapter": 66,
    "filename": "chapters/mindwars-part/mindwars-part-066-no-border-no-demand.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-MARA",
    "purpose": "Mara compares arrivals across unrelated people for a shared border, language, or demand, and establishes that the events carry addressed nonsemantic pressure and nothing anyone can answer.",
    "hook": "Every arrival has an address and not one of them has a sentence, so there is nobody to negotiate with and nothing to negotiate about.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Mara knows the arrivals are addressed writes limited to salience, urgency, certainty, and wanting, and knows addressing is a property of the event rather than evidence about its origin; she has no sender, no border, and no message."
    },
    "reveal_ids": []
  },
  {
    "chapter": 67,
    "filename": "chapters/mindwars-part/mindwars-part-067-a-category-with-a-budget.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-JULIAN",
    "purpose": "The classification hardens into a funded policy category assembled out of accounts like Nia's, and Julian learns that a category with a budget is harder to correct than a mistake.",
    "hook": "The category passes with a line item attached, and the people it was built out of are cited in it without having been asked.",
    "cross_cuts": [
      "CUT-A-FLAG-AND-A-CATEGORY"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Julian knows the funded category, its citations, and its exact wording; he cannot say who is causing the arrivals, and the attribution inside the category remains an inference he entered rather than a finding anyone made."
    },
    "reveal_ids": []
  },
  {
    "chapter": 68,
    "filename": "chapters/mindwars-part/mindwars-part-068-a-property-of-the-event.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-MARA",
    "purpose": "Mara runs the experiment that could have produced a sender signature, gets nothing, and the second request for a flag arrives as an instruction instead of a question.",
    "hook": "The addressing is real and tells her nothing about who is doing the addressing, and the next request does not have a question mark in it.",
    "cross_cuts": [
      "CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Mara knows the experiment's negative result and what it forecloses; she has no provenance, no carrier signature, and no way to distinguish one origin from another, and she has been told what her next answer is expected to be."
    },
    "reveal_ids": []
  },
  {
    "chapter": 69,
    "filename": "chapters/mindwars-part/mindwars-part-069-nobody-says-the-word.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-ONSET",
    "pov_id": "POV-JULIAN",
    "purpose": "Doctrine is issued without a declaration, and Julian records a war being fought under a category name because the record has no other name available.",
    "hook": "He files the doctrine under the only heading the system offers, and in the room where it is signed nobody says the word war.",
    "cross_cuts": [
      "CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-ONSET",
      "knowledge_limit": "Julian knows the issued doctrine, the absence of any declaration, and the vocabulary available to him; no stable name for the conflict exists yet in the rooms he works in, and no sender has been established."
    },
    "reveal_ids": []
  },
  {
    "chapter": 70,
    "filename": "chapters/mindwars-part/mindwars-part-070-copper-for-everybody.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian audits collective copper as public policy and establishes that it buys real defensive time by sealing people away from the public life it was meant to protect.",
    "hook": "The shielding works, the waiting rooms are quiet, and the quiet is where everyone now has to live.",
    "cross_cuts": [
      "CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE"
    ],
    "motif_events": [
      "MOT-COPPER-02"
    ],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Julian knows the enclosure programs, their attenuation claims, and what they cost the people inside them; he knows of no active defense, and nothing in the enclosure record speaks to origin."
    },
    "reveal_ids": []
  },
  {
    "chapter": 71,
    "filename": "chapters/mindwars-part/mindwars-part-071-an-inverted-copy.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-MARA",
    "purpose": "Mara builds an inverted copy of a captured pattern, cancels it inside a measured volume, and turns defense from enclosure into something that can be aimed at a space rather than held around a person.",
    "hook": "The pattern goes to nothing inside the volume, and nothing is exactly what comes back out of it.",
    "cross_cuts": [
      "CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Mara knows the counterwave cancels a captured pattern inside a bounded volume and that the result is removal rather than insertion; she has not yet worked out what the emission requires of the space between the emitter and the pattern, and the pattern supplies no provenance."
    },
    "reveal_ids": [
      "REVEAL-COUNTERPHASE-TRANSMITS"
    ]
  },
  {
    "chapter": 72,
    "filename": "chapters/mindwars-part/mindwars-part-072-the-defense-transmits.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-MARA",
    "purpose": "Mara states the result she cannot design around: to cancel a pattern inside a person's field the counterwave has to be transmitted through minds, so the defense is the same kind of act as the attack.",
    "hook": "It works because it transmits, which means there is no version of it that stays outside anybody.",
    "cross_cuts": [
      "CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": 480,
    "outlier_purpose": "Compression to the single result and its immediate ethical consequence, so the reversal lands in the time it takes her to finish the sentence.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Mara knows that counterphase cancellation carries no address, inserts nothing, and must be transmitted through minds; she does not know what it does to a person who has agreed to it, and it identifies no sender."
    },
    "reveal_ids": [
      "REVEAL-COUNTERPHASE-TRANSMITS"
    ]
  },
  {
    "chapter": 73,
    "filename": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-NIA",
    "purpose": "Nia forces the working defense apart from its authorization, sets the terms on which she will be inside a cancellation field at all, answers aloud for herself, coordinates those conditions with Mara over the consented paired channel one deliberately sent contribution at a time, and learns from the inside exactly what the field does to a person.",
    "hook": "She says yes to one bounded field on her own conditions, and then finds out what her own head sounds like while it is running.",
    "cross_cuts": [
      "CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION",
      "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT"
    ],
    "motif_events": [
      "MOT-KNOCK-01",
      "MOT-YES-01"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "exploratory",
    "calibration_selected": true,
    "representative_purpose": "Tests counterphase consent, the Mindwars tonal expansion, and Nia's ability to exercise authorization authority without a resolved provenance (`DEC-007`).",
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Nia knows what she was asked, the four conditions she originated, the spoken time-bound yes Halloran transcribed and received, what the bounded field felt like in her body, the familiar phrase she could not access afterward, and that the paired channel carried only deliberate sends while its metadata held timing and permission rather than thought; she does not know whether the cancellation operation can be aimed, widened, or undone, and neither this local run nor its records speak to future deployments or to where her earlier certainty came from."
    },
    "reveal_ids": [
      "REVEAL-COUNTERPHASE-TRANSMITS"
    ]
  },
  {
    "chapter": 74,
    "filename": "chapters/mindwars-part/mindwars-part-074-only-on-the-answer.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-MARA",
    "purpose": "Mara runs the consented bounded-local field-volume test only on Nia's current answer, coordinating it over the fluent paired channel where every contribution has to be deliberately sent; it succeeds, then Nia's next deliberate send fails at a familiar phrase and her immediate report identifies the gap.",
    "hook": "The pattern is gone, the room is quiet, and Nia reports aloud that a familiar phrase she could use before the test is no longer there.",
    "cross_cuts": [
      "CUT-ENTRY-ON-A-CURRENT-ANSWER"
    ],
    "motif_events": [
      "MOT-COME-03"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Mara knows the test's measured success, the consent state it ran under, Nia's failed deliberate send, and Nia's immediate report that she can no longer access a familiar phrase; Mara never receives the missing phrase or any unoffered thought, knows the field inserted nothing and cannot be run backward, and cannot say what else it removed or from whom."
    },
    "reveal_ids": []
  },
  {
    "chapter": 75,
    "filename": "chapters/mindwars-part/mindwars-part-075-timing-and-no-content.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-NIA",
    "purpose": "Nia holds her concrete gap in access to a familiar phrase, the session's consent-state and transport metadata, and the integrity log against one another, and establishes that none of them can be promoted into evidence about origin or into a standing permission.",
    "hook": "Three records agree on when everything happened, and not one of them contains a single thing that was thought.",
    "cross_cuts": [
      "CUT-ENTRY-ON-A-CURRENT-ANSWER"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Nia knows the timings, the consent states, the integrity events, and her own concrete gap in access to a familiar phrase; content recording was never enabled, so no transcript exists, and the metadata is semantically opaque and silent about causes."
    },
    "reveal_ids": []
  },
  {
    "chapter": 76,
    "filename": "chapters/mindwars-part/mindwars-part-076-current-local-revocable.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian drafts the trial-consent instrument out of Nia's stated conditions and finds a scaled version already circulating that keeps the wording and drops the conditions.",
    "hook": "His instrument requires a current answer from a named person, and the draft on the next desk requires neither.",
    "cross_cuts": [
      "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT",
      "CUT-PROTOCOL-ON-PAPER-AND-IN-USE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Julian knows the conditions Nia set, the instrument he wrote from them, and the scaled draft he has seen; he does not know whether the scaled version will be authorized, and consent to a field remains distinct from consent to record content."
    },
    "reveal_ids": []
  },
  {
    "chapter": 77,
    "filename": "chapters/mindwars-part/mindwars-part-077-fluency-is-not-permission.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "pov_id": "POV-NIA",
    "purpose": "Nia runs a fluent paired channel while an incoming pattern is active, and a pause, a latency fault, and a fallback to spoken voice prove the consent state is operational rather than ceremonial.",
    "hook": "The channel is easy and she stops it mid-sentence anyway, because easy is not the same as allowed.",
    "cross_cuts": [
      "CUT-PROTOCOL-ON-PAPER-AND-IN-USE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-COUNTERPHASE",
      "knowledge_limit": "Nia knows what she chose to send, when she paused, and that transport stopped where she stopped it; she cannot know what her partner did not offer, and fluency has given her access to nothing unoffered."
    },
    "reveal_ids": []
  },
  {
    "chapter": 78,
    "filename": "chapters/mindwars-part/mindwars-part-078-protection-nobody-asked-for.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-NIA",
    "purpose": "Officials propose automatic protective transmission for whole populations, and Nia establishes that protection nobody was asked about is the same act as the thing it defends against.",
    "hook": "They call it a shield because it points the other way, and she makes them say out loud who they intend to ask.",
    "cross_cuts": [
      "CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Nia knows the proposal's wording and what it does not require of anyone; she does not know whether it will be adopted, and she will not describe anybody else's exposure as consent."
    },
    "reveal_ids": []
  },
  {
    "chapter": 79,
    "filename": "chapters/mindwars-part/mindwars-part-079-the-capability-we-condemned.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian sets the page-nine record beside the automatic-protection proposal and shows defenders requesting the capability they condemned, while refusing to let the resemblance be read as evidence about who sent anything.",
    "hook": "The same architecture, the same sentence, a different letterhead, and none of it says where the signal came from.",
    "cross_cuts": [
      "CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Julian knows what page nine printed, what the defender proposal asks for, and that the resemblance is architectural; the comparison establishes no provenance, and a party's capability is not evidence that the party transmitted."
    },
    "reveal_ids": []
  },
  {
    "chapter": 80,
    "filename": "chapters/mindwars-part/mindwars-part-080-the-first-we.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-MARA",
    "purpose": "Mara argues the first protective network into existence and begins speaking for a public in the first person plural, which is the register the work now demands of her.",
    "hook": "She hears herself say we in a room full of strangers and does not correct it.",
    "cross_cuts": [
      "CUT-THE-WE-AND-THE-SINGLE-ANSWER"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Mara knows what the network can hold, what it costs to run, and whose consent it currently rests on; she does not know how far it can be extended, and she is speaking for people she has never met."
    },
    "reveal_ids": []
  },
  {
    "chapter": 81,
    "filename": "chapters/mindwars-part/mindwars-part-081-two-living-people-at-a-time.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-MARA",
    "purpose": "The protective network is worked under time pressure with Mara and Idris Vane's fluent pairing as its coordination layer, and one deliberate pause and one drop to ordinary voice change what happens to people on the ground.",
    "hook": "The channel hands her back her own mouth at the worst possible second, and the fallback is what saves the block.",
    "cross_cuts": [
      "CUT-SESSION-AND-ITS-TRAFFIC"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1200,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Mara knows her session with Vane by its timing, what she deliberately sent, and where the protocol refused to complete; the channel carried two living people at a time and nothing that was not offered, and none of it identifies a sender."
    },
    "reveal_ids": []
  },
  {
    "chapter": 82,
    "filename": "chapters/mindwars-part/mindwars-part-082-timing-traffic-and-nothing.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian reads the night back out of Vane and Osei's consent-state and transport metadata, establishes that the pattern supports a policy claim and no evidentiary one, and watches the institutional shorthand for the whole capability harden into one term.",
    "hook": "He can prove who was paired with whom and for how long and cannot prove one word, and the briefing calls all of it Electronic Speech Pairings anyway.",
    "cross_cuts": [
      "CUT-SESSION-AND-ITS-TRAFFIC"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Julian knows session timing, pauses, integrity events, and pairing traffic, and knows the metadata is semantically opaque; no content was recorded, so no transcript exists, and the traffic pattern establishes nothing about meaning or origin."
    },
    "reveal_ids": []
  },
  {
    "chapter": 83,
    "filename": "chapters/mindwars-part/mindwars-part-083-chosen-risk.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-NIA",
    "purpose": "Nia takes one bounded counterphase session she chooses for herself, revocable while it runs, and fixes the difference between risk a person accepts and protection applied to her.",
    "hook": "She keeps her hand on the revocation the whole time and never uses it, and the not using is the part that is hers.",
    "cross_cuts": [
      "CUT-THE-WE-AND-THE-SINGLE-ANSWER",
      "CUT-POCKET-AND-THE-STREET"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Nia knows the session she agreed to, its bounds, and that she could have stopped it at any second; she cannot speak for anyone else's exposure, and the session tells her nothing about origins."
    },
    "reveal_ids": []
  },
  {
    "chapter": 84,
    "filename": "chapters/mindwars-part/mindwars-part-084-inside-the-pocket.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-MARA",
    "purpose": "The network holds a handful of local pockets on a second channel Mara had to calibrate separately with Rhea Osei, and Mara does the accounting that shows the defense reaches the people who could be asked and nobody else.",
    "hook": "Two streets apart, one block gets a protected night and the other gets the same night without it.",
    "cross_cuts": [
      "CUT-POCKET-AND-THE-STREET"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Mara knows how many pockets the network holds, what each consumes in operators and consent, and who is outside them; she does not know how to widen coverage without exceeding the consent it rests on."
    },
    "reveal_ids": []
  },
  {
    "chapter": 85,
    "filename": "chapters/mindwars-part/mindwars-part-085-single-answers-do-not-scale.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-SHIELD",
    "pov_id": "POV-MARA",
    "purpose": "Mara reaches the limit of a defense assembled out of individual answers and one-to-one channels, and states the arithmetic that makes the next proposal inevitable.",
    "hook": "A defense made of single yeses covers exactly as many people as have been asked, and the count is not rising fast enough.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-SHIELD",
      "knowledge_limit": "Mara knows the coverage arithmetic, the operator limit, and the pace of the arrivals; she has no wider mechanism, no authorization for one, and no model of what a wider field would do."
    },
    "reveal_ids": []
  },
  {
    "chapter": 86,
    "filename": "chapters/mindwars-part/mindwars-part-086-theories-with-believers.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian catalogues the archive's competing origin theories with each one attributed to the person who holds it, and refuses the institutional request to rank them into a finding.",
    "hook": "Six accounts, six believers, no evidence, and a request to put one of them at the top of the page.",
    "cross_cuts": [
      "CUT-THEORIES-AND-THE-UNPARSED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Julian knows which people hold which theories and what each one rests on; none is confirmed, the record contains no authenticated sender, and his own filed attribution remains an inference."
    },
    "reveal_ids": []
  },
  {
    "chapter": 87,
    "filename": "chapters/mindwars-part/mindwars-part-087-not-a-language.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-MARA",
    "purpose": "Half the intercepts fail to parse as any spoken language, and Mara's analytic frame collapses because she has been hunting a message inside something that was only ever structure aimed at people.",
    "hook": "There is nothing to translate, which is worse than a code, because a code would mean somebody wanted to be understood.",
    "cross_cuts": [
      "CUT-THEORIES-AND-THE-UNPARSED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Mara knows the parse failures and what they rule out; she cannot infer intent, identity, or origin from unparseable structure, and the arrivals remain nonsemantic pressure with an address on them."
    },
    "reveal_ids": []
  },
  {
    "chapter": 88,
    "filename": "chapters/mindwars-part/mindwars-part-088-recorded-once-on-purpose.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-NIA",
    "purpose": "Nia and Mara enable content recording once, by separate explicit mutual consent, for a single investigative session, and the resulting transcript proves exactly what was carried and immediately becomes something other people want.",
    "hook": "The transcript is four minutes long and completely true, and by evening two institutions have asked her for it.",
    "cross_cuts": [
      "CUT-RECORDED-AND-UNRECORDED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Nia knows what she and Mara agreed to record, what the transcript contains, and that it covers only that session's deliberately sent contributions; it proves no intent, no memory, and no origin, and recording is off again unless both of them turn it on."
    },
    "reveal_ids": []
  },
  {
    "chapter": 89,
    "filename": "chapters/mindwars-part/mindwars-part-089-a-disputed-recording-state.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-JULIAN",
    "purpose": "A disputed recording state on Vane and Osei's channel stops an operation mid-decision, and Julian holds the line that a transcript covers one recorded session while metadata covers timing and nothing else.",
    "hook": "The operation waits while two people establish whether anybody had agreed to keep it, and the waiting costs something real.",
    "cross_cuts": [
      "CUT-RECORDED-AND-UNRECORDED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Julian knows the consent states in dispute, the integrity flags, and what a recorded session does and does not cover; he cannot recover unrecorded content and will not let a traffic pattern be entered as meaning."
    },
    "reveal_ids": []
  },
  {
    "chapter": 90,
    "filename": "chapters/mindwars-part/mindwars-part-090-the-shore-was-us.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-MARA",
    "purpose": "Mara turns the inherited map around and reaches the reversal the whole event has been demonstrating: the frontier was never the distance outward, human minds are the ground being crossed, and people are the shore rather than the explorers.",
    "hook": "Every map she was raised on points away from the planet, and the only territory anyone has actually entered is the inside of a person's head.",
    "cross_cuts": [
      "CUT-THE-SHORE-AND-THE-BELIEVERS"
    ],
    "motif_events": [],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion to earn the reversal in full: the inherited outward maps, the measurements that contradict them, and the position of being the crossed rather than the crosser, without letting it become a thesis about the war.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Mara knows the measurements, the parse failures, and her own position inside the event; the reversal describes where people are standing and supplies no sender, no motive, and no provenance."
    },
    "reveal_ids": []
  },
  {
    "chapter": 91,
    "filename": "chapters/mindwars-part/mindwars-part-091-integrity-fault.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-NIA",
    "purpose": "An integrity fault clips a contribution from Tomas Reyner at the worst moment of a live operation, the protocol refuses to complete it, and Nia's fallback to ordinary voice costs a measurable amount of somebody's safety.",
    "hook": "The channel offers her half a sentence it is not sure of, she refuses the half, and shouting works but not fast enough.",
    "cross_cuts": [
      "CUT-FALLBACK-AND-THE-BREACH-MODEL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Nia knows the clipped contribution, the integrity flag, and what the delay cost; she cannot know what the fragment was meant to be, and no log will reconstruct it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 92,
    "filename": "chapters/mindwars-part/mindwars-part-092-ranked-by-belief.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-JULIAN",
    "purpose": "The archive's theories are ranked under institutional pressure and Julian records the ranking as belief rather than finding, while the first-casualty attribution sets into something no later correction can reach.",
    "hook": "He writes believed by beside every line, and the summary that quotes him drops those two words.",
    "cross_cuts": [
      "CUT-THE-SHORE-AND-THE-BELIEVERS"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Julian knows the ranking, its basis in belief, and the wording he used; custody warrants provenance and not truth, and the first-casualty attribution he entered stays an inference he cannot correct into fact."
    },
    "reveal_ids": []
  },
  {
    "chapter": 93,
    "filename": "chapters/mindwars-part/mindwars-part-093-one-synchronized-night.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "pov_id": "POV-MARA",
    "purpose": "The network holds its pockets while Mara's model predicts one synchronized event past the capacity of copper, operators, and one-to-one channels, which turns the defense question from coverage into scale.",
    "hook": "The model puts the whole thing on a single night, and every defense she has is built one room and one answer at a time.",
    "cross_cuts": [
      "CUT-FALLBACK-AND-THE-BREACH-MODEL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-MINDWARS-TERRITORY",
      "knowledge_limit": "Mara knows the model's prediction, its confidence, and the capacity of every defense she holds; she does not know what a wider field would remove, and she has no authorization to find out."
    },
    "reveal_ids": []
  },
  {
    "chapter": 94,
    "filename": "chapters/mindwars-part/mindwars-part-094-enrolled-by-default.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-NIA",
    "purpose": "Institutional pressure moves to default pairing enrollment, centralized metadata, and standing continuity assumptions, and Nia names each one as a claim that reaches past a current local answer.",
    "hook": "Their word for it is enrollment and hers is default, and she refuses to let her own session logs be the template.",
    "cross_cuts": [
      "CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Nia knows what the enrollment proposal assumes and what her own consent state actually permits; calibration remains hers and her partner's alone and cannot be handed to anyone, and she does not know whether the proposal will pass."
    },
    "reveal_ids": []
  },
  {
    "chapter": 95,
    "filename": "chapters/mindwars-part/mindwars-part-095-the-only-defense-in-the-model.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-MARA",
    "purpose": "Mara's model returns one defense likely to stop a synchronized event, a single broad unaddressed field, together with the prediction that it will subtract from people it cannot identify beforehand.",
    "hook": "The model gives her one answer that works and cannot give her the name of a single person it will take something from.",
    "cross_cuts": [
      "CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Mara knows the model predicts both silence and subtraction and that it cannot identify which faculties, memories, or people are vulnerable; nothing the field removes has an additive inverse, and no authorization exists yet."
    },
    "reveal_ids": [
      "REVEAL-AFFECTED-AREA-EXTENT"
    ]
  },
  {
    "chapter": 96,
    "filename": "chapters/mindwars-part/mindwars-part-096-three-counties-wide.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-JULIAN",
    "purpose": "Official summaries call the field's civilian effects negligible, and Julian finds the working annex that describes the affected area as three counties wide.",
    "hook": "The summary says negligible in one clause, and the annex beneath it describes an affected area three counties wide.",
    "cross_cuts": [
      "CUT-NEGLIGIBLE-AND-THE-EXTENT",
      "CUT-THE-EXTENT-RETURNED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Julian knows the summary's wording and the annex's description of the affected area as three counties wide; the description is an extent rather than a geometry, it names no county, and it carries no casualty inventory."
    },
    "reveal_ids": [
      "REVEAL-AFFECTED-AREA-EXTENT"
    ]
  },
  {
    "chapter": 97,
    "filename": "chapters/mindwars-part/mindwars-part-097-it-will-not-take-a-list.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-MARA",
    "purpose": "Mara tries to aim, bound, and enumerate the field's effects, and establishes the properties that make the decision unbearable: nothing predictable before, nothing enumerable during, nothing fully mapped after, and nothing that can be put back.",
    "hook": "She spends the night trying to hand the field a list of names, and it will not take one.",
    "cross_cuts": [
      "CUT-NEGLIGIBLE-AND-THE-EXTENT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Mara knows the field carries no address, inserts nothing, and cannot be reversed by any mode she has; she cannot predict, enumerate, or afterwards fully map who it affects, and cancelling a pattern yields nothing about where the pattern came from."
    },
    "reveal_ids": []
  },
  {
    "chapter": 98,
    "filename": "chapters/mindwars-part/mindwars-part-098-nobody-can-be-asked.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-NIA",
    "purpose": "Nia refuses the manufactured unanimity the decision wants and establishes that neither a pair's consent nor a recorded transcript can answer for everyone inside the affected area.",
    "hook": "They ask her to say the affected area agrees, and she tells them exactly how many people she is entitled to answer for.",
    "cross_cuts": [
      "CUT-NOBODY-TO-ASK"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Nia knows what consent she can give and for whom, and knows how long real consent takes to collect; she does not know whether the field will be authorized without it, and no transcript or metadata can supply another person's answer."
    },
    "reveal_ids": []
  },
  {
    "chapter": 99,
    "filename": "chapters/mindwars-part/mindwars-part-099-authorized-not-consented.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian writes the emergency authorization and makes its exact character permanent in the record: an institutional instrument standing where individual consent cannot be obtained, and never a substitute for it.",
    "hook": "He writes authorized in the box and refuses to let the word consented appear anywhere on the page.",
    "cross_cuts": [
      "CUT-NOBODY-TO-ASK"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Julian knows which body authorized the field, under which instrument, and what the instrument does not claim; no individual consent was collected from the affected area, and the authorization establishes nothing about origin."
    },
    "reveal_ids": []
  },
  {
    "chapter": 100,
    "filename": "chapters/mindwars-part/mindwars-part-100-my-name-in-the-operator-field.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-MARA",
    "purpose": "Mara takes the emission herself instead of assigning it, which fixes responsibility on one named person before anything is switched on.",
    "hook": "She puts her own name in the operator field, and the argument about who is responsible ends in one line of a form.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Mara knows the authorization, the model, and what she is choosing to be responsible for; she does not know what the field will take, from whom, or whether the predicted silence will arrive at all."
    },
    "reveal_ids": []
  },
  {
    "chapter": 101,
    "filename": "chapters/mindwars-part/mindwars-part-101-silence-has-a-radius.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-DECISION",
    "pov_id": "POV-MARA",
    "purpose": "The decision is spent at full cost in Mara's own words: the defense will work, its reach is the same reach that will take things from civilians across an affected area three counties wide, and she says so before it runs rather than after.",
    "hook": "She admits on the record that the silence she is about to make has a reach, and that people she will never meet are inside it.",
    "cross_cuts": [
      "CUT-THE-EXTENT-RETURNED"
    ],
    "motif_events": [
      "MOT-RADIUS-01"
    ],
    "estimated_length_class": "long-outlier",
    "estimated_words": 2300,
    "outlier_purpose": "Expansion to spend the decision at full cost in one place: the modeled benefit, the admitted civilian reach of a defensive silence, and the refusal to convert the canonical extent into a comforting figure.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-DECISION",
      "knowledge_limit": "Mara knows the model, the authorization, and the canonical description of the affected area as three counties wide; the extent is not a geometry she can compute, she cannot name anyone inside it, and nothing has been emitted yet."
    },
    "reveal_ids": [
      "REVEAL-AFFECTED-AREA-EXTENT"
    ]
  },
  {
    "chapter": 102,
    "filename": "chapters/mindwars-part/mindwars-part-102-a-room-with-a-door.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-NIA",
    "purpose": "As the arrivals peak, Nia runs a consent shelter where every entry is one person's own current answer, works it with Reyner and Baird paired on intake beside her, and keeps a written list of who came in.",
    "hook": "The peak is loud enough that people arrive already certain of things they never decided, and she asks each of them at the door anyway.",
    "cross_cuts": [
      "CUT-PEAK-AND-THE-PHASE",
      "CUT-WHO-CAME-IN"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Nia knows who came through her door, what each of them agreed to, and how the night sounds from inside the shelter; she does not know what the defense is doing outside it and cannot account for anyone who never arrived."
    },
    "reveal_ids": []
  },
  {
    "chapter": 103,
    "filename": "chapters/mindwars-part/mindwars-part-103-into-phase.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-MARA",
    "purpose": "Mara reads the same peak as a measurable phase, matches it, and starts the emission.",
    "hook": "She holds the two patterns against each other until they cancel, and then she does not stop.",
    "cross_cuts": [
      "CUT-PEAK-AND-THE-PHASE",
      "CUT-FIELD-AND-THE-INSTRUMENT"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression to the single act of matching phase and starting the field, so the operation begins in about the time it takes to do it.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Mara knows the incoming phase, the counterphase she is emitting, and that the field carries no address; she cannot see what it is subtracting, from whom, or how far it has already reached."
    },
    "reveal_ids": []
  },
  {
    "chapter": 104,
    "filename": "chapters/mindwars-part/mindwars-part-104-timestamped-while-it-runs.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian timestamps the authorization, its scope, and the consent state of every coordinating channel while the field is running, Mara and Vane's included, so the night will have a custody record nobody can soften later.",
    "hook": "He writes down the exact minute a page of paper began removing things from people, and the page does not contain one name.",
    "cross_cuts": [
      "CUT-FIELD-AND-THE-INSTRUMENT",
      "CUT-A-PAGE-AND-A-DOORWAY"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Julian knows the authorization's exact scope, the minute the field started, and the consent state of each coordinating channel; the instrument names no affected person, no content is recorded, and he cannot know what is being removed."
    },
    "reveal_ids": []
  },
  {
    "chapter": 105,
    "filename": "chapters/mindwars-part/mindwars-part-105-one-answer-at-the-door.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-NIA",
    "purpose": "One arrival at the shelter door is in no condition to answer for herself, Reyner and Baird hold the intake channel behind Nia without carrying anything about the woman on the step, and Nia has thirty seconds to decide what that permits her to do.",
    "hook": "She cannot get a current answer out of the woman on the step, so she stands in the doorway with her and does not carry her in.",
    "cross_cuts": [
      "CUT-A-PAGE-AND-A-DOORWAY",
      "CUT-THE-LOCK-AND-THE-UNSHELTERED"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression to a single interruption inside the night, so one person's unobtainable answer arrives at the pace it actually arrives.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Nia knows what she can and cannot obtain from the person in front of her and what her own rule requires of her; she does not know what is happening across the rest of the area, and she will not answer for anyone who cannot answer."
    },
    "reveal_ids": []
  },
  {
    "chapter": 106,
    "filename": "chapters/mindwars-part/mindwars-part-106-quieter-in-here.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-MARA",
    "purpose": "The lock holds across everyone the field reaches, and Mara notices her own inner speech has gone measurably thinner while she is still holding it.",
    "hook": "She reaches for the phrase she checks her own work with, finds a flat place where it used to be, and keeps her hand on the emitter.",
    "cross_cuts": [
      "CUT-THE-LOCK-AND-THE-UNSHELTERED",
      "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Mara knows the lock is holding, knows what she can no longer reach in her own inner speech, and knows the field inserted nothing; she cannot enumerate who else it has reached and cannot undo any of it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 107,
    "filename": "chapters/mindwars-part/mindwars-part-107-clean-silence.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-JULIAN",
    "purpose": "The carrier stops, and Julian records a clean silence that contains no surrender, no counterparty, and no sender.",
    "hook": "The trace goes flat at a minute he can name, and he writes down that nobody said anything, because nobody ever did.",
    "cross_cuts": [
      "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG",
      "CUT-SILENCE-WITHOUT-A-COUNTERPARTY"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": null,
    "outlier_purpose": "Compression to the instant the carrier stops, so the silence arrives without commentary and the custody entry is the only thing in the room.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Julian knows the exact time the carrier stopped and that nothing accompanied it; there is no surrender, counterparty, or authenticated sender, and the stop resolves no provenance."
    },
    "reveal_ids": []
  },
  {
    "chapter": 108,
    "filename": "chapters/mindwars-part/mindwars-part-108-what-it-took.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-NULL-NIGHT",
    "pov_id": "POV-MARA",
    "purpose": "Mara shuts the field down into a silence covering an affected area three counties wide, and the first reports arrive of things it removed from people no list will ever hold.",
    "hook": "The defense worked, the reports start before morning, and there is no procedure anywhere for putting any of it back.",
    "cross_cuts": [
      "CUT-SILENCE-WITHOUT-A-COUNTERPARTY",
      "CUT-WHO-CAME-IN"
    ],
    "motif_events": [],
    "estimated_length_class": "long-outlier",
    "estimated_words": null,
    "outlier_purpose": "Expansion to hold the operational end of the night and the beginning of its cost in one place, including the canonical extent and the absent inverse, without resolving what was lost.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-NULL-NIGHT",
      "knowledge_limit": "Mara knows the field ran across an affected area canonically described as three counties wide, knows the incoming patterns stopped, and knows the first reports of loss; the affected set cannot be enumerated, nothing removed can be restored, and no report tells her who sent anything."
    },
    "reveal_ids": []
  },
  {
    "chapter": 109,
    "filename": "chapters/mindwars-part/mindwars-part-109-into-the-history.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-POSTNULL-HISTORY",
    "pov_id": "POV-JULIAN",
    "purpose": "Authorities announce a success with no surrender and no counterparty, and Julian enters the consent dispute and the uncounted civilian uncertainty into the history the event is now named by.",
    "hook": "The announcement runs one paragraph with no absences in it, so he files the absences into the history under a heading of their own.",
    "cross_cuts": [
      "CUT-HISTORY-AND-THE-WORD-SAVED",
      "CUT-DEPOSITED-AND-SUMMARIZED"
    ],
    "motif_events": [
      "MOT-RECORD-02"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-POSTNULL-HISTORY",
      "knowledge_limit": "Julian knows the announcement, the authorization trail, the consent dispute, and that the civilian losses are uncounted; there is no counterparty and no authenticated sender, and the attribution he entered earlier remains an inference custody cannot correct."
    },
    "reveal_ids": []
  },
  {
    "chapter": 110,
    "filename": "chapters/mindwars-part/mindwars-part-110-not-the-word-saved.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-POSTNULL-HISTORY",
    "pov_id": "POV-NIA",
    "purpose": "Nia refuses saved as a complete description of what happened to the area, and takes a live decision on her own judgment without first settling where her old certainty began.",
    "hook": "She makes the call, stands behind it, and stops requiring an origin before she is allowed to trust herself.",
    "cross_cuts": [
      "CUT-HISTORY-AND-THE-WORD-SAVED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-CONDITIONED-RELEASES",
      "knowledge_limit": "Nia knows the official summary, the first conditioned release beside it, and her own judgment on the call she has just made; both accounts of her earlier certainty remain unverified, and nothing she has done forgives anyone or endorses any archive."
    },
    "reveal_ids": []
  },
  {
    "chapter": 111,
    "filename": "chapters/mindwars-part/mindwars-part-111-provenance-not-truth.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-POSTNULL-HISTORY",
    "pov_id": "POV-JULIAN",
    "purpose": "Official summaries begin smoothing inference into fact while the first conditioned, provenance-preserving releases go out to compete with them, and Julian establishes that nobody is going to adjudicate between the two.",
    "hook": "Two accounts of the same night are public, both are properly sourced, and there is no body anywhere whose job it is to decide.",
    "cross_cuts": [
      "CUT-DEPOSITED-AND-SUMMARIZED"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-POSTNULL-HISTORY",
      "knowledge_limit": "Julian knows what the summaries assert, what the conditioned releases contain, and that embargoes hold while complete holdings stay closed; custody warrants provenance rather than truth, and the first-casualty attribution stands uncorrected."
    },
    "reveal_ids": []
  },
  {
    "chapter": 112,
    "filename": "chapters/mindwars-part/mindwars-part-112-the-line-held.md",
    "movement": "mindwars_part",
    "timeline_id": "TL-POSTNULL-HISTORY",
    "pov_id": "POV-MARA",
    "purpose": "Mara shuts down active counterphase for good, withdraws behind the copper she kept, and closes the war on a held line and an accounting nobody has started.",
    "hook": "The last thing she does as a defender is disconnect the emitter, and the silence she is left standing in is the one she made.",
    "cross_cuts": "none",
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-POSTNULL-HISTORY",
      "knowledge_limit": "Mara knows the emitter is down, knows the line held, and knows reports of loss are still arriving without a count; she cannot restore anything the field removed and has no accounting to offer anyone who asks."
    },
    "reveal_ids": []
  }
]
```

### Aftermath_Coda entries — chapters 113–128

Owner: **task 5.5.** Allocation: 16 chapters, 16,500 provisional Prose_Words, Mara 7 / Nia 1 / Julian 1 / Safiya 7, outlier ceiling 3. Shortest movement by words.

| Chapter | POV | Timeline_ID | Beat |
|---:|---|---|---|
| 113 | `POV-NIA` | `TL-CODA-PUBLIC-ACCOUNTING` | Civilian-loss intake inside the contested archive |
| 114 | `POV-JULIAN` | `TL-CODA-PUBLIC-ACCOUNTING` | Conditioned release; Safiya's documented request found |
| 115 | `POV-SAFIYA` | `TL-CODA-APPROACH` | Travel through the affected area, rehearsing facts |
| 116 | `POV-SAFIYA` | `TL-CODA-THRESHOLD` | Three unhurried knocks and waiting |
| 117 | `POV-MARA` | `TL-CODA-THRESHOLD` | The same threshold from the other side |
| 118 | `POV-SAFIYA` | `TL-CODA-ACCOUNT` | Tuesday, the kettle, the exact loss |
| 119 | `POV-SAFIYA` | `TL-CODA-ACCOUNT` | The precise shape of the absence |
| 120 | `POV-MARA` | `TL-CODA-ACCOUNT` | The affected area received as people |
| 121 | `POV-MARA` | `TL-CODA-ACCOUNT` | Reflexes noticed and set down one at a time |
| 122 | `POV-SAFIYA` | `TL-CODA-CONSENT` | Valid, sober, repeated, freely chosen consent |
| 123 | `POV-SAFIYA` | `TL-CODA-CONSENT` | Consent held steady; the hidden hope admitted |
| 124 | `POV-MARA` | `TL-CODA-REFUSAL` | Truth-based refusal; relay off before the kettle; Coda_Turn |
| 125 | `POV-MARA` | `TL-CODA-REFUSAL` | Attention narrowed to water, chairs, breath |
| 126 | `POV-SAFIYA` | `TL-CODA-STAYING` | No restoration, no absolution, and the choice to stay |
| 127 | `POV-MARA` | `TL-CODA-STAYING` | Ordinary voice through air, in both directions |
| 128 | `POV-MARA` | `TL-CODA-OUTWARD` | Entry against herself, outward threshold obligation |

Movement invariants beyond the global set:

- `DEC-005`'s contested archive continues: an ongoing conditioned Trust release competes with official summaries without opening complete holdings and without adjudication.
- `heritage_base: unspecified_by_author` is preserved everywhere. No entry infers real-world particulars from Safiya's name or the unspecified base. Her account is described, never quoted into invented particulars.
- The 116–117 knocks are **one** Motif_Event seen from two positions, joined by a reciprocal threshold Cross Cut whose replay boundary keeps 117 from replaying Safiya's journey.
- Under `DEC-015`/`DEC-016` the neural channel recedes after 112. Pairing, Pairing_Transcripts, archives, simulations, models, and reconstructions cannot supply Safiya's dead second participant or her missing corpus, and cannot turn her Chapter 124 request into truthful restoration. Ordinary spoken voice, listening, presence, and refusal carry the ending.
- Deceleration is deliberate: hooks come from disclosure, arrival, refusal, emotional choice, and moral remainder. No Foreign_Signal return, counterphase, renewed combat, campaign, spectacle, or adversary proof.
- Under `DEC-017`, Chapter 118 reuses the Chapter 73 cancellation-field vocabulary with no authorization question anywhere near it — the absence of the question is the echo, Safiya does not know about Chapter 73, and no narrator supplies the link. The parallel stays unnamed through 123 and is named exactly once in Chapter 128, inside the existing `MOT-RECORD-03` entry against herself: the protocol she was held to was one room wide, and she then ran the same mechanism across an area canonically described as three counties wide with no one to ask. It stays dry self-indictment, resolves no provenance, absolves nothing, validates no archive, and does not reinterpret Safiya's consent.
- Motifs due: `MOT-KNOCK-02` at 116 and 117; `MOT-KETTLE-01` at 118; `MOT-RADIUS-02` at 120; `MOT-COME-04`, `MOT-COPPER-03`, and `MOT-KETTLE-02` at 124; `MOT-CHAIN-03` at 127; `MOT-RECORD-03`, `MOT-KNOCK-03`, and `MOT-WHOSE-01` at 128.
- Reveal release: `REVEAL-SAFIYA-TUESDAY-LOSS` at 118, window 118–119. `REVEAL-CODA-PROVENANCE` is never revealed and appears in no entry.
- **`DEC-018` planning obligation — uncounted private civilian loss, 113–114.** These two chapters carry the Coda half of the obligation that begins at 109. Chapter 113 is Nia at the civilian-loss intake desk and Chapter 114 is Julian issuing a conditioned release, which makes them the last and best places to establish, in specific people, that the null took things from private life that no instrument recorded and no institution counted. The class must be vivid here **before** Chapter 118, so that Safiya's account lands on prepared ground instead of introducing the category and the grief together. Boundaries, all strict: no Safiya POV before 115; no chapter enters her home; her particular loss is not named, described, paraphrased, or foreshadowed; `REVEAL-SAFIYA-TUESDAY-LOSS` still releases at 118 inside its unchanged 118–119 window with `POV-SAFIYA` as owner; and the civilians whose losses appear at 113 and 114 are other people, unconnected to Safiya and to each other except by the same field. Her documented request is found at 114 as an intake record; finding a request is not learning what she lost. Under the `DEC-018` supporting canon in [`canon-bible.md`](canon-bible.md) the private two-person language layer is already an established class, and neither Ada nor Lena Ferris may be connected to the Coda. This is a drafting obligation carried by this section, not an `ArcEntry` field, and it creates no `Reveal`, `Motif_Event`, `CrossCut`, or `Literal_Phrase_Constraint`.
- Chapters 118 and 124 are Calibration Batch members; task 5.7 supplies their representative purposes.

#### Entries — chapters 113–128

**Active `ArcEntry` records for chapters 113–128: 16.** Written by task 5.5. POV load Mara 7 / Nia 1 / Julian 1 / Safiya 7, longest POV run 2, three outliers (116, 125, 128) against a 13-entry normal floor, the ledger's motif set at 116, 117, 118, 120, 124, 127, and 128, and `REVEAL-SAFIYA-TUESDAY-LOSS` released at 118 and completed at 119 inside its 118–119 window. No entry records `"none"`: the Coda is one continuous causal chain from the intake desk to a new door, so every chapter shares a moment, a consequence, or a disclosure with at least one other.

Two authoring notes belong with the entries. First, chapters 113, 114, 118, and 128 sit inside record-custody windows as well as their own scene windows; each names its scene chronology as `timeline_id` and reaches the custody window only through `record_horizon.through_timeline_id` — 118 and 128 to `TL-TRUST-ROLLING-DEPOSITS` as chapters 62 and 73 already do, and 113 and 114 to `TL-TRUST-CONDITIONED-RELEASES` as chapter 110 already does. Second, the `DEC-017` parallel gets no `CrossCut` record. Declaring one would oblige Chapter 73's entry to reference it and would name in planning what the manuscript may name only once, in Chapter 128; the parallel therefore travels on the shared physical vocabulary of 73 and 118 and on nothing structural. Chapter 118's `purpose`, `hook`, and `knowledge_limit` deliberately contain no word for permission, and Chapter 118 carries the reuse obligation as a drafting instruction from this section rather than as a field.

```json record=ArcEntry schema=1
[
  {
    "chapter": 113,
    "filename": "chapters/aftermath-coda/aftermath-coda-113-what-went-out.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-PUBLIC-ACCOUNTING",
    "pov_id": "POV-NIA",
    "purpose": "Two years on, Nia works the Trust's civilian-loss intake and adds by hand the category the forms do not carry, so a subtraction can be stated by the person it happened to instead of being filed as something that arrived.",
    "hook": "The form has a line for what came in and no line at all for what went out, so she rules one in the margin and starts filling it.",
    "cross_cuts": [
      "CUT-INTAKE-AND-RELEASE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-CONDITIONED-RELEASES",
      "knowledge_limit": "Nia knows two post-null years of intake calls, which losses the official categories hold and which they cannot, and which ones the conditioned releases surface beside those summaries; she has no count for the affected area, no claimant's file in front of her, and she still does not know where her own certainty began."
    },
    "reveal_ids": []
  },
  {
    "chapter": 114,
    "filename": "chapters/aftermath-coda/aftermath-coda-114-a-documented-request.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-PUBLIC-ACCOUNTING",
    "pov_id": "POV-JULIAN",
    "purpose": "Julian prepares the next witness-conditioned release and finds one documented request inside it — never intruded upon, eleven miles from Northline Array, a maternal language missing since the null — and hands the claimant the address instead of giving the defender a week to prepare.",
    "hook": "He could warn Mara and let her have an answer ready, and instead he sends Safiya the address and leaves the day to her.",
    "cross_cuts": [
      "CUT-INTAKE-AND-RELEASE",
      "CUT-ADDRESS-AND-THE-ROAD"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-CONDITIONED-RELEASES",
      "knowledge_limit": "Julian knows what this release may lawfully carry, what the request says, and that custody warrants provenance rather than truth; he cannot verify the account, cannot open complete holdings, has no adjudicator to send it to, and does not know what the claimant will do with an address."
    },
    "reveal_ids": []
  },
  {
    "chapter": 115,
    "filename": "chapters/aftermath-coda/aftermath-coda-115-the-road-in.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-APPROACH",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya crosses the affected area toward the address on a day she chose, rehearsing her own facts rather than a case, and decides to arrive as herself rather than as the spokesperson for the uncounted losses she passes on the way.",
    "hook": "By the last stretch she has put down everything she was practising about everyone else and kept only what happened to her.",
    "cross_cuts": [
      "CUT-ADDRESS-AND-THE-ROAD"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 950,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-APPROACH",
      "knowledge_limit": "Safiya knows her own Tuesday, her own loss, the address she was given, and the losses strangers described to her on the way; she has met nobody at the far end of the journey, does not know what she will be told, and holds no mandate to speak for anyone but herself."
    },
    "reveal_ids": []
  },
  {
    "chapter": 116,
    "filename": "chapters/aftermath-coda/aftermath-coda-116-three-knocks.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-THRESHOLD",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya reaches the copper-retained house and performs the defenders' own threshold protocol exactly: three unhurried knocks, hands down, and waiting.",
    "hook": "She knocks three times and waits, and doing it correctly turns out to promise her nothing at all.",
    "cross_cuts": [
      "CUT-THREE-KNOCKS-BOTH-SIDES"
    ],
    "motif_events": [
      "MOT-KNOCK-02"
    ],
    "estimated_length_class": "microchapter",
    "estimated_words": 480,
    "outlier_purpose": "Compression to the single compliant arrival, so the knock and the waiting take about as long to read as they take to perform and no interior argument fills the gap.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-THRESHOLD",
      "knowledge_limit": "Safiya knows the protocol she is following and that she has followed it correctly; she does not know whether the door opens, who is behind it, or what following a rule is worth to the person who wrote it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 117,
    "filename": "chapters/aftermath-coda/aftermath-coda-117-the-inside-of-the-door.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-THRESHOLD",
    "pov_id": "POV-MARA",
    "purpose": "From inside the same door Mara recognizes the protocol as the one she taught the world, watches her own paralysis and self-mythology arrive ahead of her, and opens it anyway.",
    "hook": "The knock is the one she wrote, and she is already standing behind her own door before she understands that it has been aimed at her.",
    "cross_cuts": [
      "CUT-THREE-KNOCKS-BOTH-SIDES",
      "CUT-KNOCK-TAUGHT-AND-OWED"
    ],
    "motif_events": [
      "MOT-KNOCK-02"
    ],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-THRESHOLD",
      "knowledge_limit": "Mara knows the knock, knows the protocol is hers, and knows the null's civilian losses were never counted; she does not know who is outside, what they lost, or what they have come to ask her for."
    },
    "reveal_ids": []
  },
  {
    "chapter": 118,
    "filename": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-ACCOUNT",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya addresses Mara directly and gives her own account in her own words: a Tuesday, the kettle on, eleven miles from the array, nothing foreign arriving, and the private layer she had only with her mother no longer where she left it.",
    "hook": "She describes what the quiet did inside her own head while the kettle went on heating, and she reaches the end of it without being interrupted or corrected.",
    "cross_cuts": [
      "CUT-TUESDAY-AND-THE-SHAPE"
    ],
    "motif_events": [
      "MOT-KETTLE-01"
    ],
    "estimated_length_class": "normal",
    "estimated_words": 1400,
    "outlier_purpose": null,
    "status": "exploratory",
    "calibration_selected": true,
    "representative_purpose": "Tests Safiya's own voice, the material specificity of her loss, the first kettle event, describe-never-quote handling, and the `unspecified_by_author` guardrail.",
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
      "knowledge_limit": "Safiya knows her own Tuesday in her own body — the kettle, the eleven miles, that nothing foreign arrived, and the moment the private two-person layer stopped being where she had left it; she knows no instrument, no procedure, and no defender's reasoning, and she knows no corpus of that layer survives for anyone to work from."
    },
    "reveal_ids": [
      "REVEAL-SAFIYA-TUESDAY-LOSS"
    ]
  },
  {
    "chapter": 119,
    "filename": "chapters/aftermath-coda/aftermath-coda-119-a-clean-lexical-space.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-ACCOUNT",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya specifies the exact shape of the absence — which words still arrive, which will not descend, and what a clean lexical space feels like from inside — and keeps the account hers by refusing to let it be summarized.",
    "hook": "She reaches for a word she used every day of her childhood and finds the place where it should descend perfectly empty and perfectly ordinary.",
    "cross_cuts": [
      "CUT-TUESDAY-AND-THE-SHAPE",
      "CUT-ACCOUNT-AND-THE-PEOPLE-IN-IT"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1100,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-ACCOUNT",
      "knowledge_limit": "Safiya knows precisely which words still arrive and which will not, and knows the difference from the inside; she can demonstrate the absence to nobody, has no record of the layer to point at, and does not know what her account will be worth to the person hearing it."
    },
    "reveal_ids": [
      "REVEAL-SAFIYA-TUESDAY-LOSS"
    ]
  },
  {
    "chapter": 120,
    "filename": "chapters/aftermath-coda/aftermath-coda-120-three-counties-of-people.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-ACCOUNT",
    "pov_id": "POV-MARA",
    "purpose": "Mara receives the canonical extent as people for the first time: an affected area three counties wide stops being a description of reach and becomes an account owed by the person who fired it.",
    "hook": "She has been saying the silence has a radius for two years, and this is the first time somebody from inside it has told her what it took.",
    "cross_cuts": [
      "CUT-ACCOUNT-AND-THE-PEOPLE-IN-IT"
    ],
    "motif_events": [
      "MOT-RADIUS-02"
    ],
    "estimated_length_class": "normal",
    "estimated_words": 1150,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-ACCOUNT",
      "knowledge_limit": "Mara knows the canonical description of the affected area as three counties wide and now knows one account from inside it; the extent is not a geometry she can compute, she can still name nobody else within it, and nothing she knows can put the account right."
    },
    "reveal_ids": []
  },
  {
    "chapter": 121,
    "filename": "chapters/aftermath-coda/aftermath-coda-121-setting-the-reflexes-down.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-ACCOUNT",
    "pov_id": "POV-MARA",
    "purpose": "Mara catalogues her own reflexes — invoke the number saved, explain the mechanism, turn the room into doctrine — and sets each one down without asking to be reassured for doing it.",
    "hook": "She puts down the last of the three things she walked into the room holding and finds she has nothing prepared and nothing to ask for.",
    "cross_cuts": [
      "CUT-REFLEXES-AND-THE-REQUEST"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 850,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-ACCOUNT",
      "knowledge_limit": "Mara knows her own habits of explanation and what each of them would do to this room; she does not yet know what she is about to be asked for, and she has nothing available that would answer it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 122,
    "filename": "chapters/aftermath-coda/aftermath-coda-122-the-request.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-CONSENT",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya asks Mara to use the retained transmitter to put something back, and gives affirmative, sober, specific, repeated consent so that permission stops being the question in the room.",
    "hook": "She gives her answer before she is asked for it, gives it again, and the one objection Mara had ready is gone.",
    "cross_cuts": [
      "CUT-REFLEXES-AND-THE-REQUEST"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1000,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-CONSENT",
      "knowledge_limit": "Safiya knows what she is asking for, that the transmitter was kept, and that her answer is hers to give and hers to withdraw; she does not know whether Mara will act on it, and she knows a yes settles permission and nothing else."
    },
    "reveal_ids": []
  },
  {
    "chapter": 123,
    "filename": "chapters/aftermath-coda/aftermath-coda-123-the-hope-she-hid.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-CONSENT",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya holds the consent steady against Mara's ethics, refuses to let a refusal become a lecture about consent, and admits the hope she had been hiding, that even a counterfeit might feel merciful.",
    "hook": "She says the thing she has never let herself say aloud, that she would take a false one, and she does not take it back.",
    "cross_cuts": [
      "CUT-VALID-YES-AND-TRUTHFUL-NO"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": 1050,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-CONSENT",
      "knowledge_limit": "Safiya knows she has been hiding both the hope that a counterfeit might feel merciful and the fear that ethics will become a way of avoiding her; she has not been answered yet and does not know which of the two is coming."
    },
    "reveal_ids": []
  },
  {
    "chapter": 124,
    "filename": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-REFUSAL",
    "pov_id": "POV-MARA",
    "purpose": "Mara affirms that the consent is genuine and refuses anyway, because she possesses neither Safiya's mother nor any source of the erased layer and the operation has no reverse, then switches the relay off and fills the kettle.",
    "hook": "The relay clicks off under her hand, and what she has left to offer is water, a chair, and her own voice.",
    "cross_cuts": [
      "CUT-VALID-YES-AND-TRUTHFUL-NO"
    ],
    "motif_events": [
      "MOT-COME-04",
      "MOT-COPPER-03",
      "MOT-KETTLE-02"
    ],
    "estimated_length_class": "normal",
    "estimated_words": 1400,
    "outlier_purpose": null,
    "status": "exploratory",
    "calibration_selected": true,
    "representative_purpose": "Tests Mara's response to Safiya, the truth-based refusal, the Coda_Turn, and the Refused_Swell.",
    "record_horizon": {
      "through_timeline_id": "TL-CODA-REFUSAL",
      "knowledge_limit": "Mara knows the consent is valid, knows she holds neither Safiya's mother nor any source of the erased layer, and knows the operation has no reverse; she cannot know how a fabricated arrival would present itself to Safiya, which is part of why she will not send one."
    },
    "reveal_ids": []
  },
  {
    "chapter": 125,
    "filename": "chapters/aftermath-coda/aftermath-coda-125-water-chairs-breath.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-REFUSAL",
    "pov_id": "POV-MARA",
    "purpose": "After the turn Mara's attention narrows to water, chairs, breath, and the other person in the room, and she offers no doctrine, no request for absolution, and no second proposal dressed as help.",
    "hook": "She catches herself starting to explain the mechanism one more time and puts two cups on the table instead.",
    "cross_cuts": [
      "CUT-NOTHING-BACK-AND-STAYING"
    ],
    "motif_events": [],
    "estimated_length_class": "microchapter",
    "estimated_words": 560,
    "outlier_purpose": "Compression to the first minutes after the refusal, so the narrowing from doctrine to room tone runs at the length of the act rather than the length of an argument.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-REFUSAL",
      "knowledge_limit": "Mara knows she has refused and that nothing available to her next is remedy; she does not know whether Safiya will stay, and she has no second proposal that would not be the first one again."
    },
    "reveal_ids": []
  },
  {
    "chapter": 126,
    "filename": "chapters/aftermath-coda/aftermath-coda-126-not-repair.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-STAYING",
    "pov_id": "POV-SAFIYA",
    "purpose": "Safiya receives no restoration, pronounces no absolution, decides for herself what presence she will accept without calling it repair, and stays.",
    "hook": "She takes her coat off, which is a decision and not a forgiveness, and she says which one it is out loud.",
    "cross_cuts": [
      "CUT-NOTHING-BACK-AND-STAYING",
      "CUT-VOICE-ACROSS-THE-TABLE"
    ],
    "motif_events": [],
    "estimated_length_class": "normal",
    "estimated_words": null,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-STAYING",
      "knowledge_limit": "Safiya knows she has been refused, knows the refusal was truthful, and knows the loss is permanent; she has granted no absolution and does not know what the evening becomes once she decides to stay in it."
    },
    "reveal_ids": []
  },
  {
    "chapter": 127,
    "filename": "chapters/aftermath-coda/aftermath-coda-127-voice-through-air.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-STAYING",
    "pov_id": "POV-MARA",
    "purpose": "Mara listens while Safiya tells her mother's remembered life, and ordinary spoken voice crosses ordinary air into a consenting ear in both directions with no instrument anywhere in it.",
    "hook": "Two people talk across a table until one in the morning, and it is real, and it gives nothing back.",
    "cross_cuts": [
      "CUT-VOICE-ACROSS-THE-TABLE"
    ],
    "motif_events": [
      "MOT-CHAIN-03"
    ],
    "estimated_length_class": "normal",
    "estimated_words": 1060,
    "outlier_purpose": null,
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-CODA-STAYING",
      "knowledge_limit": "Mara knows she is being told about a woman she never met and that ordinary speech is the whole of what crosses the room; she can verify none of it, keep none of it, and knows that listening restores nothing."
    },
    "reveal_ids": []
  },
  {
    "chapter": 128,
    "filename": "chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md",
    "movement": "aftermath_coda",
    "timeline_id": "TL-CODA-OUTWARD",
    "pov_id": "POV-MARA",
    "purpose": "Mara writes the third Record Progression event as an entry against herself, states once and dryly that the protocol she was held to was one room wide while she ran the same mechanism across an affected area three counties wide with nobody to ask, and accepts an unfinished duty to go to the communities she had held as a reach.",
    "hook": "She stands at a stranger's door inside the affected area, knocks, waits, and is left holding a question about provenance that nobody is going to answer for her.",
    "cross_cuts": [
      "CUT-KNOCK-TAUGHT-AND-OWED"
    ],
    "motif_events": [
      "MOT-RECORD-03",
      "MOT-KNOCK-03",
      "MOT-WHOSE-01"
    ],
    "estimated_length_class": "long-outlier",
    "estimated_words": 1650,
    "outlier_purpose": "Expansion to hold the terminal accounting in one place: the entry against herself, the single permitted dry statement of the one-room protocol against the three-county mechanism, the outward obligation, and the Final Passage that leaves provenance unresolved.",
    "status": "planned",
    "calibration_selected": false,
    "representative_purpose": null,
    "record_horizon": {
      "through_timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
      "knowledge_limit": "Mara knows what she authorized, how far it reached, and what one person inside that reach lost; she does not know how many others there are, whether the next door opens, or whose the damaged material was, and she has no provenance answer to deposit."
    },
    "reveal_ids": []
  }
]
```

---

## Cross-cut records

**Active `CrossCut` records: 65 — 11 in Discovery_Part, 14 in Private_Defense_Part, 30 in Mindwars_Part, and 10 in Aftermath_Coda.**

Tasks 5.2 through 5.5 add `CrossCut` records here as typed `json record=CrossCut schema=1` fences, one fence per movement, each holding its records as a JSON array ordered by first participating chapter. A relationship spanning a movement boundary belongs to the fence of the later movement, and both participants' entries must reference it. Task 5.6 audits reciprocity, distinct Material_Narrative_Value, and replay boundaries across the complete set, and synchronizes the resulting IDs into `TimelineEntry.cross_cut_ids` in [`canon-bible.md`](canon-bible.md).

### Discovery_Part cross-cuts — chapters 1–29

Eleven records, ordered by first participating chapter. Each rests on a shared moment, a shared consequence, or a shared missing fact rather than on co-membership in a chronology interval; chapters 5, 6, 9, 10, 15, 20, 22, and 25 record `"none"` because no such relationship exists for them.

Two of these carry a standing continuity load and are worth naming here. `CUT-RECONSTRUCTION-LATENCY` is where the reproducible eight-second acquisition-to-resolved-output latency is pinned to Mara's configured receiving apparatus and the source-side morning is pinned as continuous, so neither can drift later or become a universal physical constant. `CUT-HANDSHAKE-AND-TRIAGE` braids the content-free send against the triage decision and is deliberately a `temporal-braid` rather than a `causal-cut`: the declaration fixes order and address and asserts no causation, because `REVEAL-HANDSHAKE-WANTING-ORIGIN` has no owner and no release window.

```json record=CrossCut schema=1
[
  {
    "cross_cut_id": "CUT-NOISE-FLOOR-HANDOFF",
    "chapters": [
      1,
      2
    ],
    "shared_timeline_id": "TL-DECEMBER-RECEIVE",
    "shared_reveal_id": null,
    "shared_consequence": "One waveform feature in the receiver and one ordinary sound in a lived morning are the same event observed from two ends.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 1,
        "value": "Mara establishes the instrument, the noise floor, and the repeating structure with no source person available to her."
      },
      {
        "chapter": 2,
        "value": "Nia supplies the continuous lived morning at full length, with no observer, no offset, and no reason to think the morning is data."
      }
    ],
    "replay_boundary": "Chapter 2 opens on the matched ordinary sound inside Nia's own morning and never replays Mara's measurement or names her.",
    "declared_by_chapters": [
      1,
      2
    ]
  },
  {
    "cross_cut_id": "CUT-RECONSTRUCTION-LATENCY",
    "chapters": [
      3,
      4
    ],
    "shared_timeline_id": "TL-DECEMBER-RECEIVE",
    "shared_reveal_id": null,
    "shared_consequence": "Under the tested early configuration, the raw field is acquired and timestamped continuously and resolves into legible experience eight seconds later on Mara's side, while Nia's source-side morning remains continuous.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 3,
        "value": "Mara's controls and repeat processing locate the reproducible latency between raw acquisition and resolved output under a particular context, fidelity, information load, and processing configuration rather than in the source."
      },
      {
        "chapter": 4,
        "value": "Nia's alarm, shower, 6:31 road call, and console at ten to seven run unbroken through the same interval, so she has no gap or delay to notice or report."
      }
    ],
    "replay_boundary": "Chapter 4 resumes Nia's morning forward from her own clock and depicts no receiver, no offset, and no measurement.",
    "declared_by_chapters": [
      3,
      4
    ]
  },
  {
    "cross_cut_id": "CUT-ORDINARY-DETAIL-MATCH",
    "chapters": [
      7,
      8
    ],
    "shared_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "shared_reveal_id": null,
    "shared_consequence": "One unremarkable detail from a working shift becomes the criterion by which a stranger tests source matching, without the person's knowledge or consent.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 7,
        "value": "Nia's shift stays continuous and concrete, and the detail belongs to her ordinary competence rather than to anyone's experiment."
      },
      {
        "chapter": 8,
        "value": "Mara turns that same detail into a matching test and then withholds the provisional identity it produces."
      }
    ],
    "replay_boundary": "Chapter 8 begins at the log entry where the detail is used and does not re-narrate Nia's shift or her interior.",
    "declared_by_chapters": [
      7,
      8
    ]
  },
  {
    "cross_cut_id": "CUT-ATTENTION-AND-THE-CALL",
    "chapters": [
      11,
      12
    ],
    "shared_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "shared_reveal_id": null,
    "shared_consequence": "One interval of a dispatcher's concentrated attention is simultaneously the strongest evidence for the mind-as-field hypothesis and the most private thing she has.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 11,
        "value": "Mara demonstrates that small frequency changes track attention and states the field hypothesis for the first time."
      },
      {
        "chapter": 12,
        "value": "Nia works the call that produced that attention end to end, from inside, where it is labour rather than signal."
      }
    ],
    "replay_boundary": "Chapter 12 runs the call in Nia's own time and never repeats Mara's readings, terminology, or conclusions.",
    "declared_by_chapters": [
      11,
      12
    ]
  },
  {
    "cross_cut_id": "CUT-PERSON-SPECIFIC-RIGHTS",
    "chapters": [
      13,
      14
    ],
    "shared_timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "shared_reveal_id": null,
    "shared_consequence": "Proving the channel is person-specific converts a physics result into immediate consent and liability exposure before anyone has named the person.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 13,
        "value": "Mara's repeatable person-specific lock is the technical act that creates the exposure."
      },
      {
        "chapter": 14,
        "value": "Julian bears the result as a rights problem he can describe precisely and cannot report without becoming the person who knew."
      }
    ],
    "replay_boundary": "Chapter 14 opens after the result has reached him in summary and never re-stages the bench proof.",
    "declared_by_chapters": [
      13,
      14
    ]
  },
  {
    "cross_cut_id": "CUT-HANDSHAKE-AND-TRIAGE",
    "chapters": [
      16,
      17
    ],
    "shared_timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "shared_reveal_id": null,
    "shared_consequence": "One interval holds a deliberate content-free send through a known address and a triage decision made under an arriving certainty; the record fixes order and address and establishes no causal link between them.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 16,
        "value": "Mara's side is a single decided act on a temporary bench path, with no consent asked and nothing verbal to trace."
      },
      {
        "chapter": 17,
        "value": "Nia's side is two calls, one available advanced unit, a certainty she cannot distinguish from her own judgment, and one documented death."
      }
    ],
    "replay_boundary": "Chapter 17 begins inside Nia's own shift and shows no bench, no relay, and no confirmation that the two events are connected; neither chapter may present the braid as evidence of cause.",
    "declared_by_chapters": [
      16,
      17
    ]
  },
  {
    "cross_cut_id": "CUT-UNANSWERED-SILENCE",
    "chapters": [
      18,
      19
    ],
    "shared_timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "shared_reveal_id": null,
    "shared_consequence": "The same missing fact sits on both ends, no answering signal on the instrument and no locatable origin in the person, and neither absence can be read as evidence about the other.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 18,
        "value": "Mara records clean silence after the send and has to decide what to do with a transmit path she can no longer call theoretical."
      },
      {
        "chapter": 19,
        "value": "Nia retraces the shift and finds no memory, habit, or reason that produced the certainty she acted on."
      }
    ],
    "replay_boundary": "Chapter 19 begins in the hours after the call and carries none of Mara's instrument context; the shared absence is a match of texture, never a shared piece of knowledge.",
    "declared_by_chapters": [
      18,
      19
    ]
  },
  {
    "cross_cut_id": "CUT-SOURCE-AND-CASUALTY-JOINED",
    "chapters": [
      21,
      23
    ],
    "shared_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "shared_reveal_id": "REVEAL-NIA-SOURCE-CASUALTY",
    "shared_consequence": "The casualty account and the verified source match turn out to name one woman, and the joining settles identity without settling authorship.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 21,
        "value": "Nia holds the casualty half from inside, as a complete reconstruction that still contains no origin for her certainty."
      },
      {
        "chapter": 23,
        "value": "Mara returns to the same woman from the source half, carrying a verified person-specific match that now has a documented death attached to it."
      }
    ],
    "replay_boundary": "Chapter 23 begins from Mara's verification and never narrates Nia's interior reconstruction or her shift; the return supplies identity only and closes no causal question.",
    "declared_by_chapters": [
      21,
      23
    ]
  },
  {
    "cross_cut_id": "CUT-CONFESSION-REFUSED",
    "chapters": [
      23,
      24
    ],
    "shared_timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "shared_reveal_id": "REVEAL-NIA-SOURCE-CASUALTY",
    "shared_consequence": "One encounter produces two incompatible accounts of what it was for: a confession Mara needs to make and an appropriation Nia refuses to accept.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 23,
        "value": "Mara's account treats Nia as confirmation and turns a private conviction into a claim she has no evidence for."
      },
      {
        "chapter": 24,
        "value": "Nia's account refuses both unsupported origins, refuses the name case zero, and separates receiving a signal from losing confidence in her own yes, without absolving anyone."
      }
    ],
    "replay_boundary": "Chapter 24 opens after Mara has already spoken and does not replay her arrival or her framing of the match; neither account is given confirming authority over the other.",
    "declared_by_chapters": [
      23,
      24
    ]
  },
  {
    "cross_cut_id": "CUT-CONTAINMENT-ALREADY-LOST",
    "chapters": [
      26,
      29
    ],
    "shared_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "shared_reveal_id": null,
    "shared_consequence": "The result is outside the laboratory before any announcement, so the movement's closing act of containment is already void when it is performed.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 26,
        "value": "Julian establishes that external parties already know, and that none of them learned it from the people who did the work."
      },
      {
        "chapter": 29,
        "value": "Mara closes the lab still believing containment is a choice, and the movement ends in the gap between her act and Julian's information."
      }
    ],
    "replay_boundary": "Chapter 29 never depicts Julian's meetings or repeats his findings; the contradiction is available to the reader and to neither narrator.",
    "declared_by_chapters": [
      26,
      29
    ]
  },
  {
    "cross_cut_id": "CUT-ADDRESSABLE-AND-TESTED",
    "chapters": [
      27,
      28
    ],
    "shared_timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "shared_reveal_id": null,
    "shared_consequence": "Confirmed addressability is tested at once on a consenting person, and the test establishes that an arrival can be named only after it has been acted on.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 27,
        "value": "Mara establishes that the apparatus can address a named person more precisely than it can address a place."
      },
      {
        "chapter": 28,
        "value": "Nia sets the terms of the bounded test and supplies the finding no instrument can, which is the ordering of noticing relative to acting."
      }
    ],
    "replay_boundary": "Chapter 28 begins inside Nia's own test on her own terms and does not restate Mara's bench result or her instrument reasoning.",
    "declared_by_chapters": [
      27,
      28
    ]
  }
]
```

### Private_Defense_Part cross-cuts — chapters 30–61

Fourteen records, ordered by first participating chapter. Each rests on a shared moment, a shared consequence, or a shared withheld fact rather than on co-membership in a chronology interval; chapters 37, 39, 41, 49, 55, and 59 record `"none"` because no such relationship exists for them. Chapters 45 and 57 each participate in two relationships, which is where the movement's two reversals sit.

Three carry a standing continuity load and are worth naming here. `CUT-CALIBRATION-AND-THE-UNCALIBRATED` is deliberately a `contradiction-cut` and not a `causal-cut`: knowing what a consented calibrated contribution feels like gives Nia a vocabulary for her injury and no evidence about its source, so the declaration asserts contrast and never origin. `CUT-ARCHITECTURE-NOT-OPTION` fixes page nine as proof that the proposed network is write-capable by architecture and nothing more, and its replay boundary forbids either participant from reading it back onto the receive-only December apparatus. `CUT-FAILURE-WITHOUT-CONTENT` fixes the evidence boundary in the form the rest of the book depends on: the consent-protocol failure produces a complete operational record and no semantic one, and Chapter 58 may not supply content the protocol did not carry.

```json record=CrossCut schema=1
[
  {
    "cross_cut_id": "CUT-ARRIVAL-AND-THE-ROOM",
    "chapters": [
      30,
      31
    ],
    "shared_timeline_id": "TL-PRIVATE-COPPER",
    "shared_reveal_id": null,
    "shared_consequence": "One untraceable arrival in one mind is the whole reason a shielded room exists, and the room's first measured quiet is where a second person learns what that arrival costs everyone.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 30,
        "value": "Mara supplies the arrival itself, wordless and unattributable, including her inability to rule out her own mind as its source."
      },
      {
        "chapter": 31,
        "value": "Nia supplies what the resulting quiet is worth from inside it, and the finding that every ordinary room she has lived in was always permeable."
      }
    ],
    "replay_boundary": "Chapter 31 opens inside the finished room on Nia's own first minute of quiet and never re-narrates Mara's arrival, her notebook, or her reasoning.",
    "declared_by_chapters": [
      30,
      31
    ]
  },
  {
    "cross_cut_id": "CUT-SEALED-ROOM-AND-A-LIFE",
    "chapters": [
      32,
      34
    ],
    "shared_timeline_id": "TL-PRIVATE-COPPER",
    "shared_reveal_id": null,
    "shared_consequence": "The design decision that keeps the room a room rather than a sealed box is the same decision that makes the room unusable for the work one of them cannot stop doing.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 32,
        "value": "Mara establishes the doctrine that a room without a door is not private but gone, and puts the handle where only the occupant controls it."
      },
      {
        "chapter": 34,
        "value": "Nia audits the same room as a place to live and establishes what it removes from a working life, which no attenuation figure describes."
      }
    ],
    "replay_boundary": "Chapter 34 begins with Nia already inside on an ordinary day and repeats none of Mara's specification, measurements, or doctrine.",
    "declared_by_chapters": [
      32,
      34
    ]
  },
  {
    "cross_cut_id": "CUT-CONSENT-AS-DEFAULT",
    "chapters": [
      33,
      35
    ],
    "shared_timeline_id": "TL-PRIVATE-COPPER",
    "shared_reveal_id": null,
    "shared_consequence": "A precise legal distinction and a working private boundary reach the same wall: both are individual answers to something already written into a service default.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 33,
        "value": "Julian supplies the legal separation of reception, transmission, and consent, and the discovery that enrollment already treats assent as a default."
      },
      {
        "chapter": 35,
        "value": "Mara supplies the physical limit: copper gives one person a private no and no one a public one, which is the opening the approach walks through."
      }
    ],
    "replay_boundary": "Chapter 35 opens on Mara's own accounting of what the room cannot do and never restates Julian's distinction or re-narrates his meeting.",
    "declared_by_chapters": [
      33,
      35
    ]
  },
  {
    "cross_cut_id": "CUT-DEMONSTRATION-AND-THE-FORM",
    "chapters": [
      36,
      38
    ],
    "shared_timeline_id": "TL-PRIVATE-OFFER",
    "shared_reveal_id": null,
    "shared_consequence": "The demonstrated benefit is genuine and is sold on the same document that bundles consent to pair with a default to record.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 36,
        "value": "Julian supplies the clinical pairing between two living consenting people and the hour in which the consortium names the whole capability Electronic Speech Pairings."
      },
      {
        "chapter": 38,
        "value": "Nia supplies the emergency case where paired dispatchers outperform radios, and the exact wording of the enrollment form handed to her afterward."
      }
    ],
    "replay_boundary": "Chapter 38 begins on Nia's own incident inside her own service and repeats neither the clinical demonstration nor the naming.",
    "declared_by_chapters": [
      36,
      38
    ]
  },
  {
    "cross_cut_id": "CUT-CALIBRATION-AND-THE-UNCALIBRATED",
    "chapters": [
      40,
      42
    ],
    "shared_timeline_id": "TL-PRIVATE-OFFER",
    "shared_reveal_id": null,
    "shared_consequence": "Learning exactly what a consented calibrated contribution feels like gives both of them a vocabulary for what happened to Nia in the winter and no evidence whatever about where it came from.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 40,
        "value": "Mara supplies the effort, refusability, and deliberateness of her own first sends, from the side that once transmitted without asking."
      },
      {
        "chapter": 42,
        "value": "Nia supplies the comparison from inside: this is speech, that was not, and the difference names the injury without identifying any source for it."
      }
    ],
    "replay_boundary": "Chapter 42 opens after the calibration sessions with Nia's own conclusions and never re-narrates Mara's sends or her reaction; neither chapter may present the contrast as evidence of origin.",
    "declared_by_chapters": [
      40,
      42
    ]
  },
  {
    "cross_cut_id": "CUT-PROMISE-AND-THE-CASE",
    "chapters": [
      43,
      47
    ],
    "shared_timeline_id": "TL-APRIL-TERM-SHEET",
    "shared_reveal_id": null,
    "shared_consequence": "The promise that persuades the room in April is underwritten by an injury the injured person was never asked about.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 43,
        "value": "Mara supplies the pitch as it was delivered and an honest measure of how much of it she wanted to be true."
      },
      {
        "chapter": 47,
        "value": "Nia supplies the appendix where her own incident is the urgency argument, and her refusal of the document's account of who caused it."
      }
    ],
    "replay_boundary": "Chapter 47 begins with the deployment material already in Nia's hands and never replays the April meeting or Mara's interior.",
    "declared_by_chapters": [
      43,
      47
    ]
  },
  {
    "cross_cut_id": "CUT-CONSTRAINABLE-CLAUSE",
    "chapters": [
      44,
      45
    ],
    "shared_timeline_id": "TL-APRIL-TERM-SHEET",
    "shared_reveal_id": "REVEAL-BIDIRECTIONAL-ARCHITECTURE",
    "shared_consequence": "A negotiated limit on write capability and a printed line enabling it sit in the same set of documents within the same hour.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 44,
        "value": "Julian supplies the assurances he obtained, the language he drafted, and his belief that the write path is a setting somebody chose."
      },
      {
        "chapter": 45,
        "value": "Mara supplies the specification page that makes the drafted limit describe something the architecture does not have."
      }
    ],
    "replay_boundary": "Chapter 45 opens with the specification already in Mara's hands and does not replay the negotiation or Julian's drafting.",
    "declared_by_chapters": [
      44,
      45
    ]
  },
  {
    "cross_cut_id": "CUT-ARCHITECTURE-NOT-OPTION",
    "chapters": [
      45,
      46
    ],
    "shared_timeline_id": "TL-APRIL-TERM-SHEET",
    "shared_reveal_id": "REVEAL-BIDIRECTIONAL-ARCHITECTURE",
    "shared_consequence": "Write capability is confirmed as structural rather than optional, which removes the remedy without proving anything about December or about what reached Nia.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 45,
        "value": "Mara supplies the discovery itself: one line, read once, that turns her own wire into something with two directions."
      },
      {
        "chapter": 46,
        "value": "Julian supplies the tracing that shows there is no clause to strike, and the professional consequence of having promised otherwise."
      }
    ],
    "replay_boundary": "Chapter 46 begins from the hardware description rather than from Mara's reading, and neither chapter may treat page nine as evidence about the December apparatus.",
    "declared_by_chapters": [
      45,
      46
    ]
  },
  {
    "cross_cut_id": "CUT-REFUSAL-AND-THE-MINUTES",
    "chapters": [
      48,
      50
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "A refusal given in exact words becomes a summary of general concerns, and the gap between the two is what makes independent custody necessary.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 48,
        "value": "Mara supplies the refusal as she chose to give it, specific to one line and one reason, at a cost she names aloud."
      },
      {
        "chapter": 50,
        "value": "Julian supplies the circulated version, where that specificity is gone and no one can be shown to have removed it."
      }
    ],
    "replay_boundary": "Chapter 50 opens on the document rather than the meeting and reproduces the room only as the minutes now describe it.",
    "declared_by_chapters": [
      48,
      50
    ]
  },
  {
    "cross_cut_id": "CUT-PRESERVED-AND-TRANSFERRED",
    "chapters": [
      51,
      54
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "The insistence that exact words survive institutional summary and the later arrival of records older than the archive are two halves of one custody claim: provenance can be preserved and truth cannot be certified.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 51,
        "value": "Mara supplies the demand that transmit enable and her refusal be kept verbatim, at the moment a custodial trust is founded to keep them."
      },
      {
        "chapter": 54,
        "value": "Mara supplies the later transfer of pre-Trust logs and voice memoranda with original dates intact, which establishes that composition preceded custody."
      }
    ],
    "replay_boundary": "Chapter 54 begins weeks later at the transfer itself and does not replay the founding, the softened minutes, or the demand; the return adds composition chronology and closes no question about content.",
    "declared_by_chapters": [
      51,
      54
    ]
  },
  {
    "cross_cut_id": "CUT-DEPOSIT-AND-THE-TIMESTAMPS",
    "chapters": [
      52,
      53
    ],
    "shared_timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "shared_reveal_id": "REVEAL-CASUALTY-CONSEQUENCE",
    "shared_consequence": "The document Nia deposits in order to test herself clears her of the outcome and stays silent on authorship, so the exoneration changes the file and not the injury.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 52,
        "value": "Nia supplies the decision to deposit the one record that could convict her, and the conditions she writes to control who may read it and when."
      },
      {
        "chapter": 53,
        "value": "Julian supplies what the timestamps establish, the attribution he must enter to make the file institutionally usable, and the relief he watches fail to arrive."
      }
    ],
    "replay_boundary": "Chapter 53 opens with the logs already in custody and never re-narrates Nia's deposit, her conditions, or her interior; neither chapter may convert the cleared outcome into an account of where the certainty came from.",
    "declared_by_chapters": [
      52,
      53
    ]
  },
  {
    "cross_cut_id": "CUT-PROTOCOL-AND-THE-STALE-STATE",
    "chapters": [
      56,
      57
    ],
    "shared_timeline_id": "TL-PRIVATE-PROTOCOL",
    "shared_reveal_id": null,
    "shared_consequence": "One channel carries a fully consented conversation and later carries one contribution the recipient had not currently authorized, so the protocol's success and its failure share a mechanism.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 56,
        "value": "Nia supplies the working case from inside: deliberate sends, visible acknowledgment, and a pause that stops transport exactly where she stopped it."
      },
      {
        "chapter": 57,
        "value": "Mara supplies the failure case: a consent state older and broader than the act it permitted, and an immediate stop that leaves nothing to inspect."
      }
    ],
    "replay_boundary": "Chapter 57 begins inside the failed session and does not replay the successful conversation or restate what was sent during it.",
    "declared_by_chapters": [
      56,
      57
    ]
  },
  {
    "cross_cut_id": "CUT-FAILURE-WITHOUT-CONTENT",
    "chapters": [
      57,
      58
    ],
    "shared_timeline_id": "TL-PRIVATE-PROTOCOL",
    "shared_reveal_id": null,
    "shared_consequence": "One protocol failure produces a complete operational record and no semantic one, which is what forces pairing consent, sending consent, and recording consent apart.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 57,
        "value": "Mara supplies the failure as it was lived and the fact that revocation left nothing recoverable to argue about."
      },
      {
        "chapter": 58,
        "value": "Julian supplies the same event as custody sees it, timing and consent state and integrity flags with no content, and the repaired rule written out of that gap."
      }
    ],
    "replay_boundary": "Chapter 58 works only from the metadata record and may not narrate the session, name what crossed, or supply content the protocol did not carry.",
    "declared_by_chapters": [
      57,
      58
    ]
  },
  {
    "cross_cut_id": "CUT-ENCLOSURE-AND-THE-PUBLIC",
    "chapters": [
      60,
      61
    ],
    "shared_timeline_id": "TL-PRIVATE-PROTOCOL",
    "shared_reveal_id": null,
    "shared_consequence": "A complete and ethically valid private answer is finished in the same days a synchronized public incident shows the answer reaches no one who has no room.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 60,
        "value": "Nia supplies the proof that fluency grants no access to unoffered thought, and the accumulating reports from people with nowhere to shield."
      },
      {
        "chapter": 61,
        "value": "Mara supplies the finished conditional rule and the incident occurring in several places at once, which no private boundary answers."
      }
    ],
    "replay_boundary": "Chapter 61 opens on Mara's own drafting and on the incident as it reaches her, and does not replay Nia's demonstration or the reports she read.",
    "declared_by_chapters": [
      60,
      61
    ]
  }
]
```

### Mindwars_Part cross-cuts — chapters 62–112

Thirty records, ordered by first participating chapter, then by second. This is the movement with the manuscript's tightest converging-thread pattern, so most chapters carry a relationship; chapters 66, 85, 100, and 112 record `"none"` because no shared moment, consequence, or withheld disclosure exists for them. Chapters 64, 73, 76, 83, 96, 109, and all seven null-night chapters participate in two relationships each, which is where the movement's reversals and its compressed night sit.

Null night is the book's tightest compressed-clock cluster and its seven records form a closed ring: `CUT-PEAK-AND-THE-PHASE`, `CUT-FIELD-AND-THE-INSTRUMENT`, `CUT-A-PAGE-AND-A-DOORWAY`, `CUT-THE-LOCK-AND-THE-UNSHELTERED`, `CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG`, `CUT-SILENCE-WITHOUT-A-COUNTERPARTY`, and `CUT-WHO-CAME-IN` join 102–108 in sequence and close 108 back to 102. Three carry `handoff_mode: "temporal-braid"` because the declared `TL-NULL-NIGHT` chronology supports genuine simultaneity there; the rest convert simultaneity into consequence so the night reads as convergence rather than repetition. Every `material_narrative_value` covers a different action, and Nia's shelter, Julian's custody record, and Mara's emitter never re-narrate one another.

Four others carry a standing continuity load. `CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION` fixes the order that matters most in this movement: the finding that cancellation must be transmitted through minds comes first, and the authorization question follows from the physics rather than the reverse. `CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE` is deliberately a `causal-cut` about adoption and not about origin, and its replay boundary forbids either participant from reading the resemblance as evidence that the consortium sent anything. `CUT-THE-SHORE-AND-THE-BELIEVERS` holds the title's reversal against the institutional ranking of sender theories without letting either become the other, so the reversal stays a statement about human position and never a provenance claim. `CUT-DEPOSITED-AND-SUMMARIZED` opens `DEC-005`'s public contest and declares its own limit: two properly sourced accounts, no adjudicating body, and no correction of the first-casualty attribution.

```json record=CrossCut schema=1
[
  {
    "cross_cut_id": "CUT-HER-ACCOUNT-AND-THEIR-FILE",
    "chapters": [
      62,
      64
    ],
    "shared_timeline_id": "TL-MINDWARS-ONSET",
    "shared_reveal_id": null,
    "shared_consequence": "An account deposited on stated conditions enters a system that will accept only one account of who is doing this, so the conditions survive in custody while the file records a certainty nobody has.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 62,
        "value": "Nia supplies the account itself, written into custody on her own attached conditions after reports about strangers show her her own winter from the outside."
      },
      {
        "chapter": 64,
        "value": "Julian supplies the intake that has a field for the adversary and no field for uncertainty, and the inference he enters into it while privately knowing it is one."
      }
    ],
    "replay_boundary": "Chapter 64 begins at the opened file and does not replay the deposit or quote Nia's account, and neither chapter may treat the filed attribution as evidence about origin or promote either account of the origin of her wanting over the other.",
    "declared_by_chapters": [
      62,
      64
    ]
  },
  {
    "cross_cut_id": "CUT-A-FLAG-AND-A-CATEGORY",
    "chapters": [
      63,
      67
    ],
    "shared_timeline_id": "TL-MINDWARS-ONSET",
    "shared_reveal_id": null,
    "shared_consequence": "A withheld scientific flag does not leave the question open; it leaves it to be answered by a funded policy category, which is harder to correct than a mistake.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 63,
        "value": "Mara supplies the refusal in the room, the physics handed over intact and the flag withheld, and the cost of being read as difficult rather than accurate."
      },
      {
        "chapter": 67,
        "value": "Julian supplies what the withheld flag hardens into four chapters later, a category with a line item attached, assembled out of accounts like Nia's and citing them without having asked."
      }
    ],
    "replay_boundary": "Chapter 67 begins at the funded category and does not replay Mara's hearing or restate her measurements, and neither chapter may supply the attacker she declined to name.",
    "declared_by_chapters": [
      63,
      67
    ]
  },
  {
    "cross_cut_id": "CUT-DEMONSTRATION-CASE-REFUSED",
    "chapters": [
      64,
      65
    ],
    "shared_timeline_id": "TL-MINDWARS-ONSET",
    "shared_reveal_id": null,
    "shared_consequence": "A record built to hold one account needs a case to stand behind it, and the person it would use declines, so the account proceeds without her and she proceeds without access.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 64,
        "value": "Julian supplies the file's appetite, an emergency instrument that cannot function on uncertainty and therefore needs someone to stand in front of its single answer."
      },
      {
        "chapter": 65,
        "value": "Nia supplies the refusal and its price, the standing that cooperating would have bought weighed against being kept as a case instead of a person."
      }
    ],
    "replay_boundary": "Chapter 65 begins with the request already made and does not replay the opening of the file, and neither chapter may treat her refusal as evidence about origin or as consent withheld from anything but this program.",
    "declared_by_chapters": [
      64,
      65
    ]
  },
  {
    "cross_cut_id": "CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR",
    "chapters": [
      68,
      69
    ],
    "shared_timeline_id": "TL-MINDWARS-ONSET",
    "shared_reveal_id": null,
    "shared_consequence": "The experiment that could have produced a sender signature produces none, and in the same days doctrine issues under a category name, so the record's only available name for the war comes from policy rather than from measurement.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 68,
        "value": "Mara supplies the null result and what survives it, addressing that is real and says nothing about who is addressing, and a second request for a flag that arrives without a question mark in it."
      },
      {
        "chapter": 69,
        "value": "Julian supplies the doctrine issued with no declaration behind it, filed under the only heading the system offers while nobody in the signing room says the word war."
      }
    ],
    "replay_boundary": "Chapter 69 begins at the issued doctrine and does not replay the experiment or restate its parameters, and neither chapter may identify a sender or treat the category name as a finding about one.",
    "declared_by_chapters": [
      68,
      69
    ]
  },
  {
    "cross_cut_id": "CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE",
    "chapters": [
      70,
      71
    ],
    "shared_timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "shared_reveal_id": null,
    "shared_consequence": "Defense stops being a room a person sits in and becomes something aimed at a volume, which buys back the public life enclosure was costing and moves the whole question onto what may be aimed at whom.",
    "handoff_mode": "threshold-cut",
    "material_narrative_value": [
      {
        "chapter": 70,
        "value": "Julian supplies the working cost of enclosure as public policy, real defensive time bought by sealing people out of the public life the shielding was for."
      },
      {
        "chapter": 71,
        "value": "Mara supplies the crossing, an inverted copy of a captured pattern that takes the pattern to nothing inside a measured volume with no room built around anybody."
      }
    ],
    "replay_boundary": "Chapter 71 begins in the measured volume and does not replay the shielding audit or the sealed waiting rooms, and neither chapter may treat the canceled pattern as evidence about who produced it.",
    "declared_by_chapters": [
      70,
      71
    ]
  },
  {
    "cross_cut_id": "CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION",
    "chapters": [
      72,
      73
    ],
    "shared_timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "shared_reveal_id": "REVEAL-COUNTERPHASE-TRANSMITS",
    "shared_consequence": "The authorization question is created by the physics rather than raised against it: because the counterwave has to be transmitted through minds to reach a pattern inside a person's field, no version of the defense stays outside anybody, and the only remaining question is who is asked.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 72,
        "value": "Mara supplies the result she cannot design around, cancellation that works because it transmits, which makes the defense the same kind of act as the attack."
      },
      {
        "chapter": 73,
        "value": "Nia supplies the answer that finding demands, one bounded field entered on her own stated conditions, and what her own head sounds like from the inside while it is running."
      }
    ],
    "replay_boundary": "Chapter 73 begins at Nia's conditions and does not re-derive or restate Mara's result, and neither chapter may present the authorization question as prior to the transmission finding.",
    "declared_by_chapters": [
      72,
      73
    ]
  },
  {
    "cross_cut_id": "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT",
    "chapters": [
      73,
      76
    ],
    "shared_timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "shared_reveal_id": null,
    "shared_consequence": "Conditions spoken by one person become portable language, and portable language travels faster than the conditions it was made from, so the wording is already circulating at scale without the requirement that gave it meaning.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 73,
        "value": "Nia supplies the conditions themselves, stated aloud as the price of entry: a named person, an answer given now, a bounded field, and a stop she keeps hold of."
      },
      {
        "chapter": 76,
        "value": "Julian supplies what becomes of those conditions in draft, an instrument that requires a current answer from a named person and a scaled version on the next desk that keeps the wording and requires neither."
      }
    ],
    "replay_boundary": "Chapter 76 begins at the drafting desk and does not replay Nia's session or what she experienced inside the field, and neither chapter may treat the circulating draft as evidence that her conditions were met.",
    "declared_by_chapters": [
      73,
      76
    ]
  },
  {
    "cross_cut_id": "CUT-ENTRY-ON-A-CURRENT-ANSWER",
    "chapters": [
      74,
      75
    ],
    "shared_timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "shared_reveal_id": null,
    "shared_consequence": "A cancellation entered only on a current answer succeeds and produces a complete operational record with no semantic one, so the session can be accounted for in full without becoming evidence about origin or a standing permission for the next one.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 74,
        "value": "Mara supplies the run itself, entry on Nia's answer given now, coordination over a fluent paired channel where every contribution still has to be deliberately sent, Nia's failed deliberate send at a familiar phrase, and Nia's immediate report of the gap; Mara never receives the missing phrase or unoffered thought."
      },
      {
        "chapter": 75,
        "value": "Nia supplies the reckoning of her concrete phrase-access gap held against consent-state, transport metadata, and the integrity log, which agree on when and contain nothing that was thought."
      }
    ],
    "replay_boundary": "Chapter 75 works only from Nia's reported phrase-access gap and the records and may not re-narrate the session, and neither chapter may promote consent-state, transport metadata, or integrity entries into semantic content or into evidence about origin.",
    "declared_by_chapters": [
      74,
      75
    ]
  },
  {
    "cross_cut_id": "CUT-PROTOCOL-ON-PAPER-AND-IN-USE",
    "chapters": [
      76,
      77
    ],
    "shared_timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "shared_reveal_id": null,
    "shared_consequence": "The instrument's central clause proves operational rather than ceremonial: a stop taken mid-sentence during an easy session halts transport, which is the only thing that makes a written consent state mean anything.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 76,
        "value": "Julian supplies the requirement as written, a consent state that has to be current at the moment of sending and revocable by the person it belongs to."
      },
      {
        "chapter": 77,
        "value": "Nia supplies the same requirement under load, a pause taken by choice, a latency fault, and a fall back to spoken voice while a pattern is still arriving."
      }
    ],
    "replay_boundary": "Chapter 77 begins inside the running channel and does not replay the drafting or quote the instrument, and neither chapter may treat the fault log as evidence about what the incoming pattern was or where it came from.",
    "declared_by_chapters": [
      76,
      77
    ]
  },
  {
    "cross_cut_id": "CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE",
    "chapters": [
      78,
      79
    ],
    "shared_timeline_id": "TL-MINDWARS-SHIELD",
    "shared_reveal_id": null,
    "shared_consequence": "Automatic protective transmission is taken up as a defensive measure by institutions that condemned the same capability, which settles nothing about who sent anything and everything about what is now acceptable to build.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 78,
        "value": "Nia supplies the proposal as it is spoken in the room and the question it cannot answer, which is who exactly gets asked before a population is transmitted into for its own protection."
      },
      {
        "chapter": 79,
        "value": "Julian supplies the archival match, page nine laid beside the proposal, defenders requesting the same architecture they condemned, on different letterhead."
      }
    ],
    "replay_boundary": "Chapter 79 begins from the archived page and does not replay the room or Nia's questions, and neither chapter may read the resemblance between page nine and the proposal as evidence that the Open Channel Consortium sent anything.",
    "declared_by_chapters": [
      78,
      79
    ]
  },
  {
    "cross_cut_id": "CUT-THE-WE-AND-THE-SINGLE-ANSWER",
    "chapters": [
      80,
      83
    ],
    "shared_timeline_id": "TL-MINDWARS-SHIELD",
    "shared_reveal_id": null,
    "shared_consequence": "A first person plural spoken for a public and a single revocable answer given for one body are held against each other without either standing in for the other, so the protective network's we stays answerable to named singular consents and no answer given by one person becomes a permission held over anyone else.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 80,
        "value": "Mara supplies the register the work now demands of her, a first protective network argued into existence and a public spoken for in the first person plural in a room full of strangers, uncorrected."
      },
      {
        "chapter": 83,
        "value": "Nia supplies the single answer that plural has to remain answerable to, one bounded counterphase session she chose for herself, revocable while it ran, with her hand on the revocation the whole time and the not using of it the part that is hers."
      }
    ],
    "replay_boundary": "Chapter 83 begins at Nia's own decision and does not replay the room where the network was argued, and neither chapter may read Mara's we as consent given by anybody or Nia's session as a standing permission for the next one.",
    "declared_by_chapters": [
      80,
      83
    ]
  },
  {
    "cross_cut_id": "CUT-SESSION-AND-ITS-TRAFFIC",
    "chapters": [
      81,
      82
    ],
    "shared_timeline_id": "TL-MINDWARS-SHIELD",
    "shared_reveal_id": null,
    "shared_consequence": "One night of protective work can be reconstructed completely as traffic and not at all as speech, which supports a policy claim and no evidentiary one, while the institutional shorthand for the whole capability hardens into a single contested term over records that carry no meaning at all.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 81,
        "value": "Mara supplies the night as it is worked, fluent pairing as the coordination layer of a network run against the clock, where one deliberate pause and one drop to ordinary voice decide what happens to a block."
      },
      {
        "chapter": 82,
        "value": "Julian supplies the same night as traffic, consent-state transitions and transport metadata establishing who was paired with whom and for how long, a policy claim and no evidentiary one, with the briefing calling all of it Electronic Speech Pairings regardless."
      }
    ],
    "replay_boundary": "Chapter 82 begins at the records and may repeat only what the protocol carried, timing, volume, acknowledgments, consent transitions, and errors, and may not supply one word that was sent or any unrecorded meaning behind it.",
    "declared_by_chapters": [
      81,
      82
    ]
  },
  {
    "cross_cut_id": "CUT-POCKET-AND-THE-STREET",
    "chapters": [
      83,
      84
    ],
    "shared_timeline_id": "TL-MINDWARS-SHIELD",
    "shared_reveal_id": null,
    "shared_consequence": "Because the defense is built out of single answers given by named people, its coverage stops exactly where the asking stopped, so protection reaches the people who could be asked and nobody else.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 83,
        "value": "Nia supplies the unit the whole defense is assembled from, one bounded counterphase session taken on her own choosing, revocable while it ran and never revoked."
      },
      {
        "chapter": 84,
        "value": "Mara supplies the accounting that unit produces at scale, a handful of local pockets holding and two streets showing it, one block given a protected night and the other given the same night without it."
      }
    ],
    "replay_boundary": "Chapter 84 begins at the coverage accounting and does not replay Nia's session from the inside, and neither chapter may treat an unprotected block as a refusal by the people on it or a protected one as permission for the following night.",
    "declared_by_chapters": [
      83,
      84
    ]
  },
  {
    "cross_cut_id": "CUT-THEORIES-AND-THE-UNPARSED",
    "chapters": [
      86,
      87
    ],
    "shared_timeline_id": "TL-MINDWARS-TERRITORY",
    "shared_reveal_id": null,
    "shared_consequence": "Origin stays unestablished from both directions at once, an archive holding six attributed beliefs and no evidence, and material that will not parse as any spoken language, so a demand for a ranked sender is a demand for something neither side contains.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 86,
        "value": "Julian supplies the archive's competing origin accounts with every one of them attributed to the person who holds it, six accounts and six believers, against an institutional request to rank them into a finding that he refuses."
      },
      {
        "chapter": 87,
        "value": "Mara supplies the collapse under that request, half the intercepts failing to parse as any spoken language and an analytic frame built to hunt a message inside what was only ever structure aimed at people."
      }
    ],
    "replay_boundary": "Chapter 87 begins inside the unparsed material and does not restate the archive's theories, and neither chapter may let a ranking or a failure to translate become evidence that anybody sent anything.",
    "declared_by_chapters": [
      86,
      87
    ]
  },
  {
    "cross_cut_id": "CUT-RECORDED-AND-UNRECORDED",
    "chapters": [
      88,
      89
    ],
    "shared_timeline_id": "TL-MINDWARS-TERRITORY",
    "shared_reveal_id": null,
    "shared_consequence": "One separately consented recording fixes the evidence limit for every account after it, proving exactly what was carried in one sitting and nothing beyond it, and becomes something other people want the same day it exists.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 88,
        "value": "Nia supplies the one recorded session, content recording enabled by separate explicit mutual consent for a single investigative sitting, and a four-minute transcript that is completely true and asked for by two institutions by evening."
      },
      {
        "chapter": 89,
        "value": "Julian supplies the same limit under operational pressure, a disputed recording state stopping a decision mid-course while a transcript's one session is held apart from metadata that carries timing and nothing else."
      }
    ],
    "replay_boundary": "Chapter 89 begins at the disputed state and may repeat the recorded session only within its limit: a transcript proves recorded protocol-carried content from that one sitting, metadata proves timing, and recording stays separately mutual and off by default.",
    "declared_by_chapters": [
      88,
      89
    ]
  },
  {
    "cross_cut_id": "CUT-THE-SHORE-AND-THE-BELIEVERS",
    "chapters": [
      90,
      92
    ],
    "shared_timeline_id": "TL-MINDWARS-TERRITORY",
    "shared_reveal_id": null,
    "shared_consequence": "The title's reversal is held against the institutional ranking of sender theories without either becoming the other, so the reversal stays a statement about human position and never a provenance claim, and the ranking stays belief rather than finding.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 90,
        "value": "Mara supplies the reversal the whole event has been demonstrating, an inherited map turned around until the frontier is not the distance outward but human minds as the ground being crossed, with people as the shore rather than the explorers."
      },
      {
        "chapter": 92,
        "value": "Julian supplies the ranking the reversal must never be read into, sender theories ordered under institutional pressure and recorded as belief with believed by written beside every line, and a first-casualty attribution setting past the reach of any later correction."
      }
    ],
    "replay_boundary": "Chapter 92 begins at the ranked page and does not replay Mara's reversal or borrow its language, and neither chapter may let the reversal stand as a claim about who sent anything or the ranking stand as a finding.",
    "declared_by_chapters": [
      90,
      92
    ]
  },
  {
    "cross_cut_id": "CUT-FALLBACK-AND-THE-BREACH-MODEL",
    "chapters": [
      91,
      93
    ],
    "shared_timeline_id": "TL-MINDWARS-TERRITORY",
    "shared_reveal_id": null,
    "shared_consequence": "A protocol that refuses to complete anything it is unsure of costs measurable safety in a single room, and that per-room price is what makes the predicted synchronized event unanswerable, turning the defense question from coverage into scale.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 91,
        "value": "Nia supplies the price of correctness in one room, an integrity fault clipping a contribution at the worst moment, half a sentence offered and refused, and a fall back to ordinary voice that works but not fast enough."
      },
      {
        "chapter": 93,
        "value": "Mara supplies the scale that price is measured against, pockets holding while the model puts one synchronized event past the capacity of copper, operators, and one-to-one channels, against a defense built one room and one answer at a time."
      }
    ],
    "replay_boundary": "Chapter 93 begins at the model and does not replay the fault or the operation it clipped, and neither chapter may treat the integrity log as evidence about what the incoming pattern was or where it came from.",
    "declared_by_chapters": [
      91,
      93
    ]
  },
  {
    "cross_cut_id": "CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL",
    "chapters": [
      94,
      95
    ],
    "shared_timeline_id": "TL-NULL-DECISION",
    "shared_reveal_id": null,
    "shared_consequence": "The two pressures arrive together, institutional defaults reaching past any current local answer and a model whose one workable defense subtracts from people it cannot identify beforehand, which leaves a measure nobody can be asked about in advance.",
    "handoff_mode": "threshold-cut",
    "material_narrative_value": [
      {
        "chapter": 94,
        "value": "Nia supplies the pressure named one claim at a time, default pairing enrollment, centralized metadata, and standing continuity assumptions, each of them reaching past a current local answer, with her own session logs refused as the template."
      },
      {
        "chapter": 95,
        "value": "Mara supplies the measure no default could cover, one broad unaddressed field likely to stop a synchronized event, returned together with the prediction that it will subtract from people it cannot name beforehand."
      }
    ],
    "replay_boundary": "Chapter 95 begins at the model's return and does not replay the enrollment argument, and neither chapter may treat the field's predicted reach as an enumerated list of people or Nia's logs as an answer given by anyone else.",
    "declared_by_chapters": [
      94,
      95
    ]
  },
  {
    "cross_cut_id": "CUT-NEGLIGIBLE-AND-THE-EXTENT",
    "chapters": [
      96,
      97
    ],
    "shared_timeline_id": "TL-NULL-DECISION",
    "shared_reveal_id": "REVEAL-AFFECTED-AREA-EXTENT",
    "shared_consequence": "The word in the summary and the properties of the thing it describes are set side by side, an affected area three counties wide called negligible in one clause, and effects that are not predictable before, not enumerable during, not fully mapped after, and not able to be put back.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 96,
        "value": "Julian supplies the wording and what sits underneath it, official summaries calling the field's civilian effects negligible over a working annex describing an affected area three counties wide."
      },
      {
        "chapter": 97,
        "value": "Mara supplies the properties that make the same extent unbearable, a night spent trying to aim, bound, and enumerate the field that returns nothing predictable before, nothing enumerable during, nothing fully mapped after, and nothing that can be put back."
      }
    ],
    "replay_boundary": "Chapter 97 begins at the aiming attempt and may repeat only the canonical extent, an affected area three counties wide, without deriving a radius, naming counties, or producing the list of names the field will not take.",
    "declared_by_chapters": [
      96,
      97
    ]
  },
  {
    "cross_cut_id": "CUT-THE-EXTENT-RETURNED",
    "chapters": [
      96,
      101
    ],
    "shared_timeline_id": "TL-NULL-DECISION",
    "shared_reveal_id": "REVEAL-AFFECTED-AREA-EXTENT",
    "shared_consequence": "A phrase found buried in a working annex returns as first person admission by the person deciding, spoken at full cost before the field runs rather than after, which is what completes the extent as something owned rather than something disclosed.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 96,
        "value": "Julian supplies the extent as a document, one clause of official summary and the annex beneath it giving an affected area three counties wide."
      },
      {
        "chapter": 101,
        "value": "Mara supplies the same extent in her own words at full price, a defense that will work whose reach is the reach that takes things from civilians across an affected area three counties wide, admitted on the record before it runs and with people she will never meet inside it."
      }
    ],
    "replay_boundary": "Chapter 101 begins at Mara's own admission and may repeat only the canonical extent from the annex, carrying the reach as thematic admission of cost rather than a computed geographic measurement or a victory slogan.",
    "declared_by_chapters": [
      96,
      101
    ]
  },
  {
    "cross_cut_id": "CUT-NOBODY-TO-ASK",
    "chapters": [
      98,
      99
    ],
    "shared_timeline_id": "TL-NULL-DECISION",
    "shared_reveal_id": null,
    "shared_consequence": "Authorization and consent are held apart as different kinds of thing rather than degrees of one thing, so the instrument that lets an area-scale field run is institutional and is never individual consent from every affected person.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 98,
        "value": "Nia supplies the refusal of manufactured unanimity, an affected area she is asked to say agrees and a count of exactly how many people she is entitled to answer for, with neither a pair's mutual consent nor a recorded transcript able to answer for anybody outside it."
      },
      {
        "chapter": 99,
        "value": "Julian supplies the instrument written into the gap that refusal opens, an emergency authorization whose exact character goes permanently into the record as an institutional standing-in where individual consent cannot be obtained, with authorized written in the box and consented kept off the page entirely."
      }
    ],
    "replay_boundary": "Chapter 99 begins at the unfilled authorization and does not replay Nia's count or borrow her voice for it, and neither chapter may let the authorization read as consent obtained from the affected area or as consent Nia gave on its behalf.",
    "declared_by_chapters": [
      98,
      99
    ]
  },
  {
    "cross_cut_id": "CUT-PEAK-AND-THE-PHASE",
    "chapters": [
      102,
      103
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "One peak is read two ways in the same minutes, as people arriving already certain of things they never decided and as a measurable phase that can be matched, and the declaration fixes only that both readings are of that one peak.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 102,
        "value": "Nia supplies the peak as it arrives at a door, arrivals carrying certainties they never decided into a consent shelter where every entry is that one person's own current answer, asked for again at the threshold."
      },
      {
        "chapter": 103,
        "value": "Mara supplies the same peak as an instrument reading, a phase measured and matched until the two patterns cancel, and an emission she starts and then does not stop."
      }
    ],
    "replay_boundary": "Chapter 103 begins at the phase match and does not restate the shelter or its list, and neither chapter may treat the matched phase as evidence of what the incoming pattern meant or of who aimed it.",
    "declared_by_chapters": [
      102,
      103
    ]
  },
  {
    "cross_cut_id": "CUT-WHO-CAME-IN",
    "chapters": [
      102,
      108
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "A written list of everyone who came through one door returns against an affected set that was unpredictable before, unenumerable during, and incompletely mapped after, so the night closes holding one small complete record inside losses no list will ever hold.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 102,
        "value": "Nia supplies the one enumerable thing in the night, a list of who came in kept by hand through the peak, each entry made on that person's own current answer at the door."
      },
      {
        "chapter": 108,
        "value": "Mara supplies what the list is returned to, a field shut down into silence covering an affected area three counties wide and the first reports of things removed from people no list will ever hold, with nothing removed able to be put back."
      }
    ],
    "replay_boundary": "Chapter 108 does not replay the shelter, the doorway, or any entry from the list, and neither chapter may let the list stand as a map of the affected set or the affected set stand as a roll that could in principle be written.",
    "declared_by_chapters": [
      102,
      108
    ]
  },
  {
    "cross_cut_id": "CUT-FIELD-AND-THE-INSTRUMENT",
    "chapters": [
      103,
      104
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "The emission and the custody record run in the same minutes, one taking things out of people across an area and the other fixing scope, timing, and consent state while it happens, so the night ends with a paper trail nobody can soften later.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 103,
        "value": "Mara supplies the emission itself going live, two patterns held against each other until they cancel and a hand that stays on the emitter once the cancellation takes."
      },
      {
        "chapter": 104,
        "value": "Julian supplies the custody record made while the field is running, the authorization timestamped with its scope and the consent state of every coordinating channel, and one page of paper recorded as the thing removing things from people without a single name anywhere on it."
      }
    ],
    "replay_boundary": "Chapter 104 begins at the timestamp and does not replay the phase match or the emission's mechanics, and neither chapter may let the custody record describe what the cancellation removed or the emission supply content the record did not carry.",
    "declared_by_chapters": [
      103,
      104
    ]
  },
  {
    "cross_cut_id": "CUT-A-PAGE-AND-A-DOORWAY",
    "chapters": [
      104,
      105
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "Institutional authorization at area scale sits beside one person's unobtainable current answer, an authorizing page carrying no name at all against a single doorway where the one name that matters cannot be got, and neither one closes the other.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 104,
        "value": "Julian supplies the page at scale, an authorization whose recorded scope reaches an entire affected area and whose text holds no individual name, timestamped to the minute it began operating on people."
      },
      {
        "chapter": 105,
        "value": "Nia supplies the case the page cannot reach, one arrival on the step in no condition to answer for herself and thirty seconds in which no current answer can be obtained, ending with Nia standing in the doorway beside her rather than carrying her in."
      }
    ],
    "replay_boundary": "Chapter 105 does not cite, quote, or invoke the authorization, and neither chapter may let institutional authorization read as consent for the woman on the step or her unanswered case read as an argument that the authorization was individually consented anywhere.",
    "declared_by_chapters": [
      104,
      105
    ]
  },
  {
    "cross_cut_id": "CUT-THE-LOCK-AND-THE-UNSHELTERED",
    "chapters": [
      105,
      106
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "The lock holds across everyone the field reaches in the same minutes that one person on a step cannot be asked anything, which fixes the night's proportion: protection arriving without asking, over people inside no shelter and outside any list.",
    "handoff_mode": "temporal-braid",
    "material_narrative_value": [
      {
        "chapter": 105,
        "value": "Nia supplies the smallest unit of the night, thirty seconds at a threshold with a woman who cannot answer for herself and a decision about what an unobtainable answer permits, made without moving her."
      },
      {
        "chapter": 106,
        "value": "Mara supplies the reach that is holding while those thirty seconds pass, a lock steady across everyone the field touches, sheltered or not and asked or not, with her hand still on the emitter."
      }
    ],
    "replay_boundary": "Chapter 106 begins inside the holding lock and does not replay the doorway or the woman on the step, and neither chapter may let the lock's reach be read as an enumerated set of people or the doorway be read as the shape of what the field did to anybody else.",
    "declared_by_chapters": [
      105,
      106
    ]
  },
  {
    "cross_cut_id": "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG",
    "chapters": [
      106,
      107
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "Subtraction that is real leaves no semantic trace anywhere in the operational record, one operator's inner speech measurably thinner while the log of those same minutes stays clean, so a clean record is never evidence that nothing was taken.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 106,
        "value": "Mara supplies the loss from inside, a reach for the phrase she checks her own work with and a flat place where it used to be, noticed while she is still holding the field up."
      },
      {
        "chapter": 107,
        "value": "Julian supplies the record of the same stretch, a carrier stopping into a silence he can timestamp that contains no surrender, no counterparty, and no sender, and nothing at all about what anybody lost."
      }
    ],
    "replay_boundary": "Chapter 107 begins at the flat trace and does not narrate Mara's thinning or name what went missing from her, and neither chapter may let a clean log stand as evidence that nothing was removed or a private loss stand as content the protocol carried.",
    "declared_by_chapters": [
      106,
      107
    ]
  },
  {
    "cross_cut_id": "CUT-SILENCE-WITHOUT-A-COUNTERPARTY",
    "chapters": [
      107,
      108
    ],
    "shared_timeline_id": "TL-NULL-NIGHT",
    "shared_reveal_id": null,
    "shared_consequence": "The carrier stopping is what the shutdown and the first reports are measured against, an ending with no surrender, no counterparty, and nobody who ever said anything, followed by losses arriving before morning that have no additive inverse and no procedure for being put back.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 107,
        "value": "Julian supplies the ending as a recorded fact, a trace going flat at a minute he can name and a written note that nobody said anything, because nobody ever did."
      },
      {
        "chapter": 108,
        "value": "Mara supplies what follows the flat trace, a field shut down over an affected area three counties wide, a defense that worked, and reports of what it took from people starting before morning with no procedure anywhere for putting any of it back."
      }
    ],
    "replay_boundary": "Chapter 108 begins at the shutdown and does not replay the flat trace as a scene, and neither chapter may supply a counterparty, a surrender, an all-clear, or a sender for the silence, or read the working defense as an inverse for anything the cancellation removed.",
    "declared_by_chapters": [
      107,
      108
    ]
  },
  {
    "cross_cut_id": "CUT-HISTORY-AND-THE-WORD-SAVED",
    "chapters": [
      109,
      110
    ],
    "shared_timeline_id": "TL-POSTNULL-HISTORY",
    "shared_reveal_id": null,
    "shared_consequence": "The name the event is filed under and one person's usable self-trust are settled in the same stretch, absences entered into the history under a heading of their own and Nia's DEC-007 resolution reached on her own judgment, a regained self-trust that decides no causation, forgives nobody, and validates no archive, with both origin accounts left unverified.",
    "handoff_mode": "threshold-cut",
    "material_narrative_value": [
      {
        "chapter": 109,
        "value": "Julian supplies the absences the announcement leaves out, one paragraph of success with no surrender and no counterparty in it, and the consent dispute and the uncounted civilian uncertainty filed into the history the event is now named by, under a heading of their own."
      },
      {
        "chapter": 110,
        "value": "Nia supplies the refusal of the word and the crossing that follows it, saved rejected as a complete description of what happened to the area, and a live decision taken and stood behind on her own judgment without first settling where her old certainty began."
      }
    ],
    "replay_boundary": "Chapter 110 begins at the live decision and does not replay the filed history or argue with the announcement's paragraph, and neither chapter may let Nia's regained self-trust decide causation, forgive anybody, or validate an archive, or let either unverified origin account become evidence for the other.",
    "declared_by_chapters": [
      109,
      110
    ]
  },
  {
    "cross_cut_id": "CUT-DEPOSITED-AND-SUMMARIZED",
    "chapters": [
      109,
      111
    ],
    "shared_timeline_id": "TL-POSTNULL-HISTORY",
    "shared_reveal_id": null,
    "shared_consequence": "The public contest over the night's account opens and declares its own limit in one move: two properly sourced accounts of the same event stand in the open, no adjudicating body exists to decide between them, and the first-casualty attribution goes uncorrected.",
    "handoff_mode": "delayed-return",
    "material_narrative_value": [
      {
        "chapter": 109,
        "value": "Julian supplies the deposit that makes the contest possible, the consent dispute and the uncounted civilian uncertainty filed into the named history under a heading of their own on the day the one-paragraph announcement runs."
      },
      {
        "chapter": 111,
        "value": "Julian supplies the contest itself once that deposit is old, official summaries smoothing inference into fact against the first conditioned provenance-preserving releases sent out to compete with them, and the established fact that no body anywhere has the job of deciding."
      }
    ],
    "replay_boundary": "Chapter 111 begins at the summaries and the releases rather than at the filing and does not re-narrate the deposit or the announcement, and neither chapter may produce an adjudicator, turn the first-casualty attribution from inference into a finding, or let a conditioned release carry provenance the material never had.",
    "declared_by_chapters": [
      109,
      111
    ]
  }
]
```

### Aftermath_Coda cross-cuts — chapters 113–128

Ten records, ordered by first participating chapter, then by second. No Coda chapter records `"none"`: the movement is one continuous causal chain running from an intake desk through a threshold, an account, a request, a refusal, an evening, and a new door, so each chapter genuinely shares a moment, a consequence, or a disclosure with at least one other. Chapters 114, 117, 119, and 126 participate in two relationships each, which is where the movement hands off between public accounting, the threshold, the account, and staying. Nine of the ten join adjacent chapters, which is what deceleration looks like structurally: the relationships carry consequence forward one step at a time instead of braiding a compressed clock.

Two are worth naming here. `CUT-TUESDAY-AND-THE-SHAPE` is the only same-POV relationship in the movement and the only one carrying a `shared_reveal_id`; it is legitimate because Chapters 118 and 119 hold two halves of one withheld disclosure rather than one scene told twice, and its `handoff_mode` is the grammar's own clean-silence-to-missing-word `sensory-match`. `CUT-KNOCK-TAUGHT-AND-OWED` is the movement's only long-span record and rests on a stated Canon Fact consequence rather than on a motif family: the threshold protocol arrives at Mara's own door as a correctly performed claim in Chapter 117 and returns in Chapter 128 as the form of her own obligation. `MOT-KNOCK-02` and `MOT-KNOCK-03` remain two distinct events, and the record's replay boundary keeps Chapter 128 from re-narrating Safiya's arrival.

No `CrossCut` record exists for the `DEC-017` parallel, and none may be created. A record would make Chapter 73 declare the relationship reciprocally and would state in planning structure what the manuscript is permitted to state exactly once, in Chapter 128. Chapters 116–117 carry the only Coda `threshold-cut` obligation fixed in advance by [when the obligation applies](#when-the-obligation-applies), and it is `CUT-THREE-KNOCKS-BOTH-SIDES`.

```json record=CrossCut schema=1
[
  {
    "cross_cut_id": "CUT-INTAKE-AND-RELEASE",
    "chapters": [
      113,
      114
    ],
    "shared_timeline_id": "TL-CODA-PUBLIC-ACCOUNTING",
    "shared_reveal_id": null,
    "shared_consequence": "Public accounting acquires the one thing it lacked, a category for what went out, and that category is what lets a subtraction claim be documented and then found inside a witness-conditioned release two years after a night nobody has finished counting.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 113,
        "value": "Nia supplies the missing category, a line ruled by hand on forms built to record what arrived, and the working knowledge of which losses the official summaries hold and which only a conditioned release surfaces."
      },
      {
        "chapter": 114,
        "value": "Julian supplies what the category makes findable, one documented request inside the next release naming a location eleven miles from the array and a maternal language missing since the null, and the limits of what custody can do with it."
      }
    ],
    "replay_boundary": "Chapter 114 begins inside the release file and does not re-narrate intake calls or re-argue the category, and neither chapter may open complete holdings, produce an adjudicator, verify or correct Safiya's account, or correct the first-casualty attribution.",
    "declared_by_chapters": [
      113,
      114
    ]
  },
  {
    "cross_cut_id": "CUT-ADDRESS-AND-THE-ROAD",
    "chapters": [
      114,
      115
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "Control of the encounter passes to the claimant and stays there: an address is handed over with no notice sent ahead, and what happens next is a journey taken on a day she picked, in terms she sets for herself.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 114,
        "value": "Julian supplies the handover and its deliberate asymmetry, an address given to the claimant, contact left entirely in her hands, and a defender given no week in which to prepare an answer."
      },
      {
        "chapter": 115,
        "value": "Safiya supplies what she does with it, a crossing of the affected area past other people's uncounted losses and a decision to arrive as herself rather than as anyone's representative."
      }
    ],
    "replay_boundary": "Chapter 115 opens on the road and does not replay the release process or Julian's reasoning, and neither chapter may turn Safiya into an institutional case, a class claimant, or a spokesperson for the affected area.",
    "declared_by_chapters": [
      114,
      115
    ]
  },
  {
    "cross_cut_id": "CUT-THREE-KNOCKS-BOTH-SIDES",
    "chapters": [
      116,
      117
    ],
    "shared_timeline_id": "TL-CODA-THRESHOLD",
    "shared_reveal_id": null,
    "shared_consequence": "One arrival is completed from both sides of a single door: the defenders' own threshold protocol is performed exactly by a stranger and recognized from inside by the person who wrote it, and correct compliance settles nothing about what will be given.",
    "handoff_mode": "threshold-cut",
    "material_narrative_value": [
      {
        "chapter": 116,
        "value": "Safiya supplies the arrival as performed, three unhurried knocks and the waiting after them, done correctly and without any assurance attached to doing it correctly."
      },
      {
        "chapter": 117,
        "value": "Mara supplies the same sound heard from inside, the recognition that the rule is her own, the paralysis and self-mythology that arrive before she moves, and the door opened anyway."
      }
    ],
    "replay_boundary": "Chapter 117 begins at the sound inside the house and does not replay Safiya's approach, her journey, or her waiting from her side; the three knocks remain one Motif_Event seen from two positions and never become two events, and neither chapter may convert correct protocol into a promise of remedy.",
    "declared_by_chapters": [
      116,
      117
    ]
  },
  {
    "cross_cut_id": "CUT-TUESDAY-AND-THE-SHAPE",
    "chapters": [
      118,
      119
    ],
    "shared_timeline_id": "TL-CODA-ACCOUNT",
    "shared_reveal_id": "REVEAL-SAFIYA-TUESDAY-LOSS",
    "shared_consequence": "The withheld account is released in two halves by its only owner: the event on the Tuesday and then the exact standing shape of the absence it left, with no summary permitted to stand in for either half.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 118,
        "value": "Safiya supplies the event, a Tuesday with the kettle on eleven miles from the array, nothing foreign arriving, and the moment the private two-person layer stopped being where she had left it."
      },
      {
        "chapter": 119,
        "value": "Safiya supplies the shape of what remains, which words still arrive and which will not descend, and the ordinary cleanness of the space where one of them should have been."
      }
    ],
    "replay_boundary": "Chapter 119 begins at the reach for one specific missing word and does not re-narrate the Tuesday, the kettle, or the eleven miles, and neither chapter may quote or invent heritage wording, supply a surviving corpus, let anyone but Safiya summarize the account, or place a question of permission anywhere near it.",
    "declared_by_chapters": [
      118,
      119
    ]
  },
  {
    "cross_cut_id": "CUT-ACCOUNT-AND-THE-PEOPLE-IN-IT",
    "chapters": [
      119,
      120
    ],
    "shared_timeline_id": "TL-CODA-ACCOUNT",
    "shared_reveal_id": null,
    "shared_consequence": "A finished first-person account converts an extent into a debt: the affected area canonically described as three counties wide stops functioning as a measure of reach and becomes an account owed by the person who fired it.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 119,
        "value": "Safiya supplies the completed account and her refusal to have it summarized, closing on the absence stated precisely and in her own words."
      },
      {
        "chapter": 120,
        "value": "Mara supplies the reception, two years of describing a reach meeting one person from inside it, and the arrival of an obligation where a figure used to be."
      }
    ],
    "replay_boundary": "Chapter 120 begins after the account is finished and does not re-narrate the Tuesday or the lexical absence from Mara's side, and neither chapter may convert the canonical width into a radius or any other geometry, name a county or a country, or let Mara narrate Safiya's interior.",
    "declared_by_chapters": [
      119,
      120
    ]
  },
  {
    "cross_cut_id": "CUT-REFLEXES-AND-THE-REQUEST",
    "chapters": [
      121,
      122
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "The room stops being a place where the mechanism gets explained, which is the condition under which the request arrives as a request rather than as a case to be handled, and permission stops being the question in it.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 121,
        "value": "Mara supplies the inventory and the setting down, the number saved, the mechanism, and the doctrine each recognized and declined, with no reassurance asked for in exchange."
      },
      {
        "chapter": 122,
        "value": "Safiya supplies the request and the consent carrying it, affirmative, sober, specific, and repeated, which removes lack of authorization from the objections still available."
      }
    ],
    "replay_boundary": "Chapter 122 begins at the request and does not replay Mara's interior inventory, and neither chapter may let Mara's ethics pre-empt the asking, let the request belong to anyone but Safiya, or treat her consent as anything less than genuine.",
    "declared_by_chapters": [
      121,
      122
    ]
  },
  {
    "cross_cut_id": "CUT-VALID-YES-AND-TRUTHFUL-NO",
    "chapters": [
      123,
      124
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "A freely given, repeatedly stated yes meets a refusal that is not about permission: the answer rests on possession and truth, so the consent stays valid, the requested restoration stays unmet, and nothing counterfeit is transmitted.",
    "handoff_mode": "contradiction-cut",
    "material_narrative_value": [
      {
        "chapter": 123,
        "value": "Safiya supplies the yes held steady under ethical pressure, the refusal to let a no become a lecture about consent, and the admitted hope that even a counterfeit might feel merciful."
      },
      {
        "chapter": 124,
        "value": "Mara supplies what the yes cannot reach, neither the mother nor any source of the erased layer in her possession and no reverse for the operation, and then the relay switched off and the kettle filled."
      }
    ],
    "replay_boundary": "Chapter 124 begins at Mara's consideration of the mechanism and does not replay Safiya's argument or her admitted hope, and neither chapter may invalidate or reinterpret the consent, transmit or partly transmit a substitute, or let the refusal harden into doctrine.",
    "declared_by_chapters": [
      123,
      124
    ]
  },
  {
    "cross_cut_id": "CUT-NOTHING-BACK-AND-STAYING",
    "chapters": [
      125,
      126
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "The refusal produces no second offer and no request for absolution, so what happens next belongs to the person who was refused: presence is accepted on her terms and given its accurate name.",
    "handoff_mode": "causal-cut",
    "material_narrative_value": [
      {
        "chapter": 125,
        "value": "Mara supplies the emptied hands, doctrine declined, absolution not asked for, no second proposal dressed as help, and attention narrowed to water, chairs, and breath."
      },
      {
        "chapter": 126,
        "value": "Safiya supplies the decision, restoration received as permanently unavailable, absolution withheld, and staying chosen as her own act with its name kept exact."
      }
    ],
    "replay_boundary": "Chapter 126 begins at Safiya's own decision and does not replay Mara's kitchen or the refusal itself, and neither chapter may present staying as repair, restoration, forgiveness, or an exchange for anything.",
    "declared_by_chapters": [
      125,
      126
    ]
  },
  {
    "cross_cut_id": "CUT-VOICE-ACROSS-THE-TABLE",
    "chapters": [
      126,
      127
    ],
    "shared_timeline_id": "TL-CODA-STAYING",
    "shared_reveal_id": null,
    "shared_consequence": "Staying becomes an evening of ordinary speech: a remembered life is told aloud and heard, companionship proves real and insufficient at the same time, and no instrument takes any part in it.",
    "handoff_mode": "sensory-match",
    "material_narrative_value": [
      {
        "chapter": 126,
        "value": "Safiya supplies the choice to speak and full authority over what is said, a mother remembered aloud to a consenting listener without the act being called restoration."
      },
      {
        "chapter": 127,
        "value": "Mara supplies the listening, spoken voice crossing ordinary air into a consenting ear in both directions, unverifiable, unkeepable, and the whole of what she has to give."
      }
    ],
    "replay_boundary": "Chapter 127 begins once Safiya is already speaking about her mother and does not replay her decision to stay, and neither chapter may let remembering aloud become restoration or admit any machine, pairing, transcript, or recording into the evening.",
    "declared_by_chapters": [
      126,
      127
    ]
  },
  {
    "cross_cut_id": "CUT-KNOCK-TAUGHT-AND-OWED",
    "chapters": [
      117,
      128
    ],
    "shared_timeline_id": null,
    "shared_reveal_id": null,
    "shared_consequence": "The threshold protocol changes function between the two chapters: what arrives at Mara's own door as a correctly performed claim becomes, at the end, the form of her own unfinished obligation to go out, knock, and wait.",
    "handoff_mode": "threshold-cut",
    "material_narrative_value": [
      {
        "chapter": 117,
        "value": "Mara supplies the protocol received, her own rule arriving at her own door with a claimant behind it and no preparation available to her."
      },
      {
        "chapter": 128,
        "value": "Mara supplies the protocol owed, the same knocking and waiting performed by her at a stranger's door inside the affected area as obligation rather than doctrine, campaign, or remedy."
      }
    ],
    "replay_boundary": "Chapter 128 begins at a new door and does not replay Safiya's arrival, the visit, or the door opened in Chapter 117; `MOT-KNOCK-02` and `MOT-KNOCK-03` stay two distinct events, and neither chapter may make the obligation a campaign, a triumph, or a completed remedy.",
    "declared_by_chapters": [
      117,
      128
    ]
  }
]
```

---

## Task 5.6 audit result

**Date: 2026-09-14. Scope: the complete 128-entry outline, all 65 `CrossCut` records, and their agreement with [`canon-bible.md`](canon-bible.md), [`pov-roster.md`](pov-roster.md), and [`motif-ledger.md`](motif-ledger.md).** This section records the audit; it creates no record and changes no invariant. The Provisional Arc is still incomplete for the purposes of task 5.8, which owns the final verification and the `Baseline.provisional_arc_complete` flag.

### Verified

| Obligation | Evidence |
|---|---|
| Parsing | Every typed JSON fence in every planning document parses strictly — UTF-8, no duplicate keys, no trailing commas, no concatenated values. |
| Identity and sequence | 128 `ArcEntry` records, `chapter` 1–128 with no gap, duplicate, or reuse; 128 unique `filename` values, each matching its movement directory and three-digit prefix. |
| Movement structure | Four contiguous blocks in order: 1–29, 30–61, 62–112, 113–128, with boundaries at 29/30, 61/62, 112/113. |
| Chronology membership | Every entry's `timeline_id` resolves to exactly one `TimelineEntry`, and every chapter appears in that entry's `chapter_numbers`. No `TimelineEntry` names a chapter without an entry. |
| Cross-cut reciprocity | All 65 records carry two ascending existing chapters, a `declared_by_chapters` set equal to `chapters`, a valid `handoff_mode`, one distinct `material_narrative_value` per chapter, and a nonblank `replay_boundary`. Reciprocity holds in both directions for all 65: every participant's `cross_cuts` array names the ID and no nonparticipant declares it. No dangling reference. 58 records share a Timeline_ID and 7 rest on shared consequence alone; 9 also share a Reveal, and none shares one of the three never-revealed IDs. |
| Cross-cut absence | Exactly 18 entries record the literal string `"none"` — 5, 6, 9, 10, 15, 20, 22, 25, 37, 39, 41, 49, 55, 59, 66, 85, 100, 112. No entry uses `[]`, `""`, `"N/A"`, or omission. |
| December mechanism | `TL-DECEMBER-RECEIVE` is `mode: RECEIVE`, `source_side_continuity: continuous`, `receiver_offset_seconds: 8`, `apparatus_mode: receive-only`, `transmit_stage_present: false`, `person_specific_address_state: locked`. Mara-only offset and Nia's gapless morning hold in entries 1–5. |
| Distinct later bench transmit | `TL-DISCOVERY-HANDSHAKE` (16–20) is a separate chronology carrying `mode: INTRUDE`, `apparatus_mode: bench-transmit`, `transmit_stage_present: true`, and address state `reused`. The wanting event stays inside it and is never merged with December. |
| Page nine | `CF-APRIL-TERM-SHEET-PAGE-NINE` and `CF-PAGE-NINE-EVIDENCE-LIMIT` frame `transmit enable` as broader architectural capability and explicitly deny that it gives December a transmit stage. Only entries 45 and 79 invoke it, both as architecture rather than proof. |
| `DEC-002` both roles, causation open | Nia holds the December source and first-casualty roles across 1–25 with the join landing in 21–25. No entry field resolves causation. |
| `DEC-007` belief distribution | Mara's non-authoritative private conviction at 20, 23, 25, 63; Nia's refusal of both accounts at 24, 42, 52, 62; Julian's inference-not-proof at 53, 64, 67, 92; Nia's release from needing provenance at 110, which decides no causation, forgives nobody, and validates no archive. |
| Record chronology | April alteration at 50 precedes Trust formation at 51, which precedes deposits from 52. Pre-Trust composition (1–5, 16–29) is entirely before its deposit window (52–55). Every rolling-deposit chapter — 52, 54, 62, 73, 110, 113, 118, 128 — falls after formation. |
| `DEC-005` names and geography | `Northline Array`, `Open Channel Consortium`, and `Civic Record Trust` appear with exact spelling and no variant anywhere in the planning artifacts. No country or county proper name appears. |
| Null extent wording | `three counties wide` appears in entries 96, 101, 108, 120, 128 and nowhere is converted into a radius, a derived distance, or a named county. |
| Contested archive | Conditioned Trust releases compete with official summaries at 109–111, 113, and 114. No entry adjudicates between them, compels complete holdings, or opens them; 111 and 114 state the absence of an adjudicator and the closure of complete holdings as facts. |
| One mode per neural event | All 31 `TimelineEntry` records satisfy the closed four-mode invariants. `CANCEL` appears only at 70–77, 78–85, and 102–108, all inside Mindwars; the two bounded-local scopes carry Nia's current revocable individual consent with no institutional authorization, and the area-scale null carries institutional authorization with no individual consent. Every `CANCEL` record keeps `inserted_content` and `provenance_yield` at `none`, all three affected-set booleans `false`, and `additive_inverse_exists` `false`. |
| Pairing session state | `TL-PRIVATE-PROTOCOL` carries two living participants (`CHAR-001`, `CHAR-002`), current specific revocable mutual consent, a pair-specific nontransferable `calibration_id`, `deliberate_send_state: required`, mandatory opaque consent-state and transport metadata, `content_recording_enabled: false` with both recording consents false, and a null transcript. |
| Fluent pairing beats | Requirement 15.1 is satisfied in all five ranges: 36, 37, 38, 40, 41, 42; 56, 57, 58, 59, 61; 74, 75, 77; 81, 82, 83, 88, 89; 94, 98. Every session sits in an existing Mara, Nia, or Julian chapter, so Requirements 15.2 and 15.3 hold. Traffic analysis at 82 is limited to consent-state and transport metadata. The beat lists stand as of this audit date and are superseded for 70–77 and 94–108 by the [2026-09-15 amendment pass](#2026-09-15-author-approved-amendment-pass), which adds 73 and states 102 and 105; the 15.2 and 15.3 findings are unaffected. |
| POV loads | Mara 14/14/21/7 = 56, Nia 9/8/14/1 = 32, Julian 6/10/16/1 = 33, Safiya 0/0/0/7 = 7. Only the four roster POV IDs appear, and `POV-SAFIYA` appears only from 115. |
| Same-POV runs | 111 runs across the global sequence. The longest is two chapters, so the three-chapter limit is never approached. All 17 multi-chapter runs carry a non-null integer `estimated_words` on every member and clear the 3,600-word limit; the largest total is 3,450 at 100–101, then 2,710 at 127–128. |
| Length budget | 109 `normal` against a floor of 108; 19 combined outliers against a ceiling of 20, within every per-movement ceiling; every outlier carries a non-null `outlier_purpose` and every `normal` entry carries `null`. No entry is planned above 2,500. |
| `DEC-012`/`DEC-015` chronology | `ESP` appears only at 36 and 82, both after Discovery, both as contested institutional language. No entry gives December a transmit stage, attributes articulate speech to an unconsented write, reconstructs semantics from metadata, or closes provenance. |
| Reveals | The six released reveals each have an owner, a release chapter inside their payoff window, and a release chapter listed by the owning POV's entry. Every reveal reference sits inside its payoff window. The three never-revealed IDs carry no owner, release chapter, or payoff window and appear in no `reveal_ids` array. |
| Record horizons | Every `record_horizon` resolves and carries a nonblank limit. No horizon window begins after its own chapter. No `purpose` or `hook` claims knowledge of a later event; the fourteen entries using predictive language do so inside their narrator's own present. |
| `DEC-017` | No entry in 62–123 states the parallel. Chapter 118 contains no word for consent, permission, or authorization anywhere in its purpose, hook, or knowledge limit, so the absence of the question is the echo. Chapter 128 carries the single dry statement inside its existing `MOT-RECORD-03` entry. The motif ledger holds exactly 22 events with `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` closed, no fourth event in any family, exactly two `LiteralPhraseConstraint` records, and no motif, constraint, or `Reveal` record created for the parallel. |
| Coda boundaries | No Coda entry depicts a Foreign Signal return, counterphase restart, renewed combat, campaign, or adversary proof. Active counterphase closes at 112. |
| Status and calibration | At audit time all 128 entries carried `status: "planned"`, `calibration_selected: false`, and `representative_purpose: null`. Task 5.7 owns those flags and has since set them; the finding stands as of this audit date and is superseded for those three fields by [task 5.7 Calibration Batch](#task-57-calibration-batch). |

### Repaired

1. **`TimelineEntry.cross_cut_ids` synchronization.** Every array was `[]` while 58 cross-cuts named a shared Timeline_ID. The [chronology assignment](#chronology-assignment) section assigned this synchronization to task 5.6, and it is now done: 21 chronology entries in the Canon Bible carry 58 sorted, duplicate-free, resolving back-references, and the remaining 10 keep `[]` because no cross-cut names them. Every reference resolves to a `CrossCut` whose own `shared_timeline_id` is that entry.
2. **Two reveal release chapters disagreed with their owner.** `record-schemas.md` requires `Reveal.reader_release_chapter` to agree with `reveal_owner_pov`. `REVEAL-NIA-SOURCE-CASUALTY` recorded release 23 and `REVEAL-CASUALTY-CONSEQUENCE` recorded release 53, but both are owned by `POV-NIA` while 23 is Mara's chapter and 53 is Julian's. Release moved to 24 and 52, the owning POV's chapters already inside the unchanged payoff windows 21–25 and 50–55. Owners were preserved rather than reassigned because the design fixes Nia as the owner of the first casualty's operational consequence, and `DEC-007` forbids letting Mara own Nia's injury. No `ArcEntry`, POV load, payoff window, or `reveal_ids` array changed; 23 and 53 still advance their reveals inside the window.

**Residual editorial question, for human decision rather than record repair.** Repair 2 restored the objective invariant but left a craft judgment open in both clusters: the reader receives the joined identity in Mara's 23 and the cleared-outcome timestamps in Julian's 53, one chapter away from the owning POV's release chapter. The alternative repair — reassigning ownership to `POV-MARA` and `POV-JULIAN` — was rejected because it contradicts fixed design authority. If the author prefers the release beat and the owner to coincide on the page, the fix belongs in the 21–25 and 50–55 beat structure, not in the reveal records.

### Referred upward, not repaired

**Pairing-session chronology has no home.** The Canon Bible's `evidence_scope` for `TL-MINDWARS-COUNTERPHASE` and `TL-MINDWARS-SHIELD` states that pairing sessions in those ranges "receive their own chronology in the Arc Outline," but this document's [persistence contract](#persistence-contract) creates no `TimelineEntry` record, and no PAIR-mode chronology exists for 36–42, 70–77, 78–93, or 94–108. Only `TL-PRIVATE-PROTOCOL` at 56–61 carries `pair_state` and `pairing_evidence`. The consequence is narrow but real: the Fluent_Pairing beats in the other four ranges are constrained by entry text and by `DEC-015` but carry no machine-recorded mode, consent state, calibration identity, or evidence boundary, so Requirement 14.1's one-mode-per-event rule and Requirements 14.10 through 14.12 are unenforced there.

This is not repairable inside task 5.6. The fix needs new `TimelineEntry` records in the Canon Bible, which is task 4.2's authority, and the sessions at 36 and 88 involve supporting participants with no Character ID, which is task 4.3's. Fabricating either here would invent canon. Recommended resolution: task 4.2 adds one PAIR-mode chronology entry per uncovered range, overlapping the existing scene window exactly as the record-custody windows already do, with each range's `pair_state` naming only living participants who hold Character IDs.

**Resolved 2026-09-15**, along the recommended line and with the author's approval: the Canon Bible gained thirteen `mode: PAIR` entries, for fourteen counting `TL-PRIVATE-PROTOCOL`, and six non-viewpoint supporting Character IDs. See the [2026-09-15 amendment pass](#2026-09-15-author-approved-amendment-pass).

---

## Task 5.7 Calibration Batch

**Date: 2026-09-14. Scope: the `status`, `calibration_selected`, and `representative_purpose` fields of the 128 `ArcEntry` records in this document.** This section records the selection. It creates no record, adds no field, and writes no prose. No Chapter File exists for any calibration chapter, and none may be created by this task.

Requirement 1.8 asks for 6–8 chapters. The batch is eight, fixed by the design rather than chosen here, and it equals `Baseline.calibration_chapters` exactly. Nothing else in any entry changed: no purpose, hook, motif set, cross-cut, estimate, length class, POV assignment, record horizon, or reveal reference was touched.

### The eight selected chapters

| Chapter | POV | `status` | `representative_purpose` |
|---:|---|---|---|
| 1 | `POV-MARA` | `planned` | `null` — inside the opening sequence |
| 2 | `POV-NIA` | `planned` | `null` — inside the opening sequence |
| 3 | `POV-MARA` | `planned` | `null` — inside the opening sequence |
| 4 | `POV-NIA` | `planned` | `null` — inside the opening sequence |
| 5 | `POV-MARA` | `planned` | `null` — inside the opening sequence |
| 73 | `POV-NIA` | `exploratory` | Tests counterphase consent, the Mindwars tonal expansion, and Nia's ability to exercise authorization authority without a resolved provenance (`DEC-007`). |
| 118 | `POV-SAFIYA` | `exploratory` | Tests Safiya's own voice, the material specificity of her loss, the first kettle event, describe-never-quote handling, and the `unspecified_by_author` guardrail. |
| 124 | `POV-MARA` | `exploratory` | Tests Mara's response to Safiya, the truth-based refusal, the Coda_Turn, and the Refused_Swell. |

Chapters 1–5 are the opening sequence, so Requirement 1.9 does not attach and `representative_purpose` stays `null` for all five, as the [field contract](#arcentry-field-contract) requires. Their calibration function — opening momentum, Mara/Nia voice separation, first cross-cut legibility, source-record immediacy, and the eight seconds read as Mara-observed reception timing rather than a source-side discontinuity — is design authority and is recorded in the [Baseline commentary](#baseline-and-final-targets-placeholder), not in an entry field.

Chapters 73, 118, and 124 sit outside the opening sequence, so each carries the non-null single-line `representative_purpose` above. Each names what the sample is meant to test, not what the chapter contains; the entry's own `purpose` and `hook` remain the narrative record.

### Why 73, 118, and 124 are `exploratory`

`exploratory` is a legal `ChapterStatus` in [`record-schemas.md`](record-schemas.md) and, on an `ArcEntry`, it is a planning state that does not assert a Chapter File. `ArcEntry.status` agrees with a `ChapterHeader` only when the file exists, and none does.

The three nonconsecutive samples will be drafted out of sequence, from complete provisional planning context, before the movement batches around them exist. The design fixes their status: they remain `exploratory` until their surrounding movement batches are drafted and the chapters are reconciled into final continuity. Calibration text does not become approved continuity because it was reviewed. Marking them `exploratory` now is what keeps the intervening chapters — 62–72 and 74–112 around 73, 113–117 and 119–123 around 118, 119–123 and 125–128 around 124 — from being treated as settled by association.

Chapters 1–5 stay `planned` because they are contiguous and open the book: they are drafted in sequence with nothing earlier to reconcile against, so the final-continuity qualification the other three need does not apply to them. Requirement 13.5 keeps the batch itself at `draft` or `revised` while any objective or editorial finding is unresolved, and Requirement 13.6 permits separately labeled `exploratory` drafting outside a blocked batch. Neither status here anticipates a gate result.

### Julian is not represented, and the Requirement 5.11 gate is open

The batch represents three of the four roster POVs, counted from each entry's own `pov_id`: Mara narrates 1, 3, 5, and 124; Nia narrates 2, 4, and 73; Safiya narrates 118. `POV-JULIAN` narrates none of the eight and is deliberately absent. No entry field, count, or load changed to compensate, and no chapter was added or swapped to include him.

Chapter 73 is Nia's chapter, not Mara's. The design describes it as testing Mara's technical context against Nia's authorization challenge, but that is content inside a Nia-narrated chapter; the Requirement 5.10 calibration finding for 73 is evidence against Nia's Voice_Brief.

The consequence is a live obligation, not a defect:

- Julian's first appearance anywhere in the outline is **chapter 6** (`chapters/discovery-part/discovery-part-006-no-transmit-stage.md`), which is also his first appearance after calibration.
- Requirement 5.11 therefore requires Editorial_Review to record representative prose evidence and a `pass` or `revision` finding against Julian's Voice_Brief **before the first later Drafting_Batch containing him can be approved**. The batch containing chapter 6 stays unapproved until that gate is recorded.
- The finding lives in [`editorial-log.md`](editorial-log.md) as an `EditorialFinding`, and the dated result replaces `first_appearance_review: null` in `VOICE-JULIAN`. [`voice-briefs.md`](voice-briefs.md) already carries that obligation for `POV-JULIAN`; this section only records why it is owed and which chapter triggers it.
- The gate is owned by tasks 12.1 and 12.2, which draft the batch containing chapter 6 and record the first-appearance Editorial_Gate. Nothing here duplicates, satisfies, weakens, or pre-judges that gate, and task 5.7 records no finding of its own.

Requirement 5.10 separately requires a dated calibration finding for each POV the batch does represent — Mara, Nia, and Safiya. `editorial-log.md` holds zero active `EditorialFinding` records and `Baseline.calibration_finding_ids` is `[]`, which is the honest state: no calibration prose has been drafted and no review has occurred.

### Verified after the change

| Check | Result |
|---|---|
| Parsing | Every typed JSON fence in this document still parses strictly. |
| Entry count and sequence | 128 `ArcEntry` records, `chapter` 1–128, no gap, duplicate, or reuse. 65 `CrossCut` records and 1 `Baseline` record, unchanged. |
| Closed key set | All 128 entries carry the same seventeen keys, once each. No key added, removed, or renamed. |
| Selection | Exactly 8 entries carry `calibration_selected: true`, and they are 1, 2, 3, 4, 5, 73, 118, and 124. |
| Baseline agreement | That set equals `Baseline.calibration_chapters`, satisfying global invariant 20. |
| Requirement 1.9 | 73, 118, and 124 each carry a nonblank single-line `representative_purpose`. 1–5 and all 120 non-calibration entries carry `null`. |
| Status legality | Only `planned` and `exploratory` appear, both members of the `ChapterStatus` enum. Exactly 3 entries are `exploratory` — 73, 118, 124 — and the other 125 are `planned`. |
| No collateral change | The 120 non-calibration entries still carry `status: "planned"`, `calibration_selected: false`, and `representative_purpose: null`. Each of the eight edits replaced only those three lines, so every other field of the eight selected entries is as tasks 5.2–5.6 left it. |
| No prose | No file was created under `chapters/`, and every `chapters/` directory still holds only its `.gitkeep`. |

One stale statement predating this task is left for task 5.8 rather than repaired here: the [worked template](#worked-arcentry-template) preamble still says there is no chapter 124 entry in this document, which task 5.5 made false when it wrote the Coda entries. Task 5.8 owns the final verification pass.

---

## Task 5.8 verification pass

**Date: 2026-09-14. Scope: the complete Provisional Arc — 128 `ArcEntry` records, 65 `CrossCut` records, and the `provisional` `Baseline` — verified against [`canon-bible.md`](canon-bible.md), [`pov-roster.md`](pov-roster.md), [`motif-ledger.md`](motif-ledger.md), [`voice-briefs.md`](voice-briefs.md), [`record-schemas.md`](record-schemas.md), and [`decisions.md`](decisions.md).** This section owns the final verification and the `Baseline.provisional_arc_complete` flag. It creates no record, adds no field, changes no invariant, and writes no prose.

**Result: eighty objective checks, eighty passes, no failures. `provisional_arc_complete` is set to `true`.** One gap remains open and is restated below; it belongs to task 4.2 and does not bear on the flag.

### Verified — identity, structure, and viewpoint

| Obligation | Evidence |
|---|---|
| Parsing (Req 1.2) | All 41 fenced JSON blocks across all nine planning documents parse strictly. 36 typed record fences and 5 untyped commentary fences; no duplicate keys, trailing commas, or concatenated values. The four untyped fences in this document, [`arc-changes.md`](arc-changes.md), and [`editorial-log.md`](editorial-log.md) carry no `record=` type and are correctly invisible to the parsing contract. |
| Sequence (Req 1.3) | 128 `ArcEntry` records; `chapter` = 1..128 with no gap, duplicate, or reuse; records appear in ascending order in every typed fence. |
| One entry per file (Req 1.2) | 128 unique `filename` values, unique independently of `chapter`. Every path matches `chapters/<movement>/<movement>-NNN-<slug>.md` with a three-digit zero-padded sequence and a lowercase hyphenated slug. |
| Closed key set (Req 1.4) | All 128 entries carry exactly the seventeen contract keys, once each. No entry adds, omits, or renames a key, and none carries a craft score of any kind (global invariant 25). |
| Movements (Req 1.5, 11.4) | Four contiguous blocks in the order Discovery_Part 1–29, Private_Defense_Part 30–61, Mindwars_Part 62–112, Aftermath_Coda 113–128, boundaries at 29/30, 61/62, 112/113. No movement value reappears after its block closes. |
| Movement extremes (Req 3.7, 3.8) | Mindwars is the longest movement at 51 chapters and 59,000 provisional Prose_Words; the Coda is the shortest at 16 chapters and 16,500. Final verification is against observed word counts in the completed manuscript, not this table. |
| Anchor coverage (Req 4.9) | `POV-MARA` is the roster's single `anchor: true` profile and holds chapters in all four movements: 14 / 14 / 21 / 7. |
| POV loads (Req 15.3) | Per-movement and total loads match exactly — Mara 14/14/21/7 = 56, Nia 9/8/14/1 = 32, Julian 6/10/16/1 = 33, Safiya 0/0/0/7 = 7. Each roster `provisional_load` object agrees. Only the four roster POV IDs appear; no fifth POV exists for a sender, adversary, operative, archive, simulation, model, or group mind. `POV-SAFIYA` appears only from 115. |
| Same-POV runs (Req 2.7, `DEC-016`) | 111 runs on the global sequence. Longest is 2 chapters, so the three-chapter limit is never approached. All 17 multi-chapter runs match the documented run table exactly and each member carries a non-null integer `estimated_words`; every run total clears 3,600, the largest being 3,450 at 100–101 and 2,710 at 127–128. All 94 single-chapter runs correctly record `null`. |
| Length budget (Req 2.8, 2.10, 2.11) | 109 `normal` against a floor of 108; 19 combined outliers (10 `microchapter`, 9 `long-outlier`) against a ceiling of 20, inside every per-movement ceiling at 4/4/8/3 and above every per-movement normal floor. Every outlier carries a non-null `outlier_purpose`; every `normal` entry carries `null`. Every non-null estimate falls inside its declared class band, and no entry is planned above the 2,500-word Hard_Chapter_Maximum. |
| Purpose and hook (Req 1.4) | All 256 `purpose` and `hook` values are nonblank single lines. |

### Verified — references, motifs, cross-cuts, and reveals

| Obligation | Evidence |
|---|---|
| Chronology (Req 1.5) | Every `timeline_id` resolves to exactly one `TimelineEntry`, and every chapter appears in that entry's `chapter_numbers`. Every `record_horizon` carries exactly `through_timeline_id` and `knowledge_limit`, resolves, and holds a nonblank limit. |
| POV, character, motif, cut, reveal IDs | Every `pov_id` resolves in the roster; all four referenced Character_IDs (`CHAR-001`..`CHAR-004`) resolve to roster characters, with no ID referenced anywhere that the roster does not declare; every `motif_events` ID resolves in the ledger; every `cross_cuts` ID resolves to a `CrossCut` in this document; every `reveal_ids` ID resolves in the Canon Bible. No dangling reference of any kind. |
| Motif mapping (Req 7) | `ArcEntry.motif_events` equals the ledger's `participating_chapters` assignment for all 128 chapters, with `[]` wherever the ledger assigns none — an exact set match, no chapter over- or under-assigned. All 22 ledger events have a participating chapter and a `planned_chapter` inside it. `MOT-KNOCK-01` is ledgered in Mindwars at 73, `MOT-KNOCK-02` is one event spanning 116–117, there is no `MOT-CHAIN-04`, Record Progression has exactly three events, and exactly two `LiteralPhraseConstraint` records exist. |
| Cross-cut contract (Req 1.6) | All 65 records carry at least two unique ascending chapters that all have entries, a `declared_by_chapters` set equal to `chapters`, a valid `handoff_mode`, at least one non-null `shared_timeline_id`/`shared_reveal_id`/`shared_consequence`, one materially distinct nonblank `material_narrative_value` per participating chapter, and a nonblank `replay_boundary`. No cut shares one of the three never-revealed Reveal IDs. |
| Reciprocity is total (Req 1.6, 1.7) | Verified in both directions for all 65: every participating entry's `cross_cuts` array names the ID, and no nonparticipant declares it. Exactly 18 entries record the literal string `"none"`, and none of those 18 participates in any cut. All seven null-night chapters 102–108 hold `TL-NULL-NIGHT` and each participates in at least one cut, joined by temporal braids; 116–117 carry the reciprocal `threshold-cut` `CUT-THREE-KNOCKS-BOTH-SIDES`. |
| Reveals (Req 6.7) | The six released reveals match this document's reveal table on owner, release chapter, and payoff window; each release chapter is narrated by the owning POV and its entry lists the reveal; every reveal reference across all 128 entries sits inside its payoff window. The three never-revealed IDs carry null owner, release chapter, and payoff window, and appear in no `reveal_ids` array. |
| Compression bound (Req 15.5) | Compression is confined to chronology-supported clusters. Declared chronology spans the December reception to two years after null night, so the manuscript cannot sit inside one global twenty-four-hour frame. |

### Verified — mandatory Fluent_Pairing coverage

Requirement 15.1 is satisfied in all five ranges, and Requirements 15.2 and 15.3 hold: every beat sits inside an existing Mara, Nia, or Julian chapter, and no beat is assigned to a Safiya chapter or to a created POV.

| Range | Beats | POVs |
|---|---|---|
| 36–42 | 36, 37, 38, 40, 41, 42 — freely chosen benefit, and Mara and Nia's joint calibration beginning at 40 | Mara, Nia, Julian |
| 56–61 | 56, 57, 58, 59, 60, 61 — sustained on-page conversation, a Deliberate_Send_Act per contribution, pause and revocation stopping transport, one consent-protocol failure and its repair, ordinary-speech fallback | Mara, Nia, Julian |
| 70–77 | 74, 75, 77 — the operational channel under counterphase pressure, with a pause, a latency fault, and a fallback to spoken voice | Mara, Nia |
| 78–93 | 81, 82, 83, 88, 89, 91 — pairing as a coordination layer, the movement's one recorded session at 88 under separate explicit mutual consent, and traffic analysis at 82 limited to consent-state and transport metadata | Mara, Nia, Julian |
| 94–108 | 94, 98, 104 — enrollment and default-consent escalation, the limits of a pair's consent at area scale, and coordinating-channel consent state timestamped while the field runs | Nia, Julian |

### Verified — decisions resolved and mirrored

Tasks 1.2, 1.3, 1.4, 1.5, and 1.7 are resolved. Each names its task in [`decisions.md`](decisions.md) and each carries `State: binding`, none superseded.

| Task | Decision | State | Mirrored in |
|---|---|---|---|
| 1.2 | `DEC-002` Nia holds both roles, causation unresolved | `binding` | Canon Bible (17 references), this outline (3), roster (3), schemas (4); receive-only December apparatus, person-specific address lock, and the distinct later bench transmit path all carried |
| 1.3 | `DEC-003` Safiya's private two-person maternal layer, base unspecified | `binding` | Canon Bible (4), this outline (1), schemas (1); `heritage_base: unspecified_by_author` preserved in Canon Bible, roster, briefs, and this outline |
| 1.4 | `DEC-004` first casualty's operational consequence | `binding` | Canon Bible (2), this outline (1), schemas (1) |
| 1.5 | `DEC-005` institutional and geographic names | `binding` | Canon Bible (7), this outline (5), roster (2), schemas (2); `Northline Array`, `Open Channel Consortium`, and `Civic Record Trust` appear with exact spelling and no variant, no country or county proper name appears anywhere, and the canonical `three counties wide` wording is never converted to a radius |
| 1.7 | `DEC-007` asymmetric belief strength, Nia moves toward release | `binding` | Canon Bible (2), this outline (8), roster (1), briefs (2), schemas (1); Mara's conviction stays `non-authoritative-belief`, Nia refuses both accounts, Julian's attribution stays inference |

`Baseline.resolved_decision_refs` lists exactly the sixteen binding nonsuperseded decisions, correctly omitting `DEC-013`. No entry field resolves the Provenance Question or the origin of Nia's wanting. Every "group mind" string in every planning document is a prohibition, never an assertion.

### Verified — architecture evidence for the human gates

`DEC-016`'s pacing criteria are **human Editorial_Gates**. Global invariant 25 and Requirement 12.12 forbid scoring them, so this pass verifies only that the planning evidence exists and that the structure is consistent with the claim. Neither judgment is made here.

- **Fastest Mindwars turnover and tightest threading.** Declared in three places: the allocation table ("Longest movement by words, fastest turnover, tightest threading"), the [movement pacing profile](#movement-pacing-profile), and the Mindwars section invariants. Structurally consistent: 51 chapters across seven clusters, 30 of the 65 cross-cuts (46 percent of the book's cuts in 40 percent of its chapters, the highest density of any Main Part), the widest handoff-mode mix at five of six modes, and the book's tightest compressed-clock cluster at 102–108, where all seven chapters hold one Timeline_ID and are joined by temporal braids. Recorded honestly for the reviewer: the rate of viewpoint rotation per chapter is marginally lower in Mindwars than in Discovery or Private Defense, because Mindwars carries six of the seventeen multi-chapter runs. Turnover in `DEC-016` is a craft judgment about cutting rate and convergence, not a POV-rotation ratio, so this is an observation for the Editorial_Gate and not an objective violation. It is deliberately not scored.
- **Deliberate post-112 deceleration.** Declared in the Coda section invariants and the pacing profile. Structurally consistent and objectively visible: mean run length rises from 1.07 / 1.07 / 1.13 chapters in the three Main Parts to 1.60 in the Coda, six of sixteen Coda chapters sit in multi-chapter runs, and threat-bearing handoff modes give way to `causal-cut`, `threshold-cut`, and `sensory-match`. All sixteen Coda hooks turn on disclosure, arrival, refusal, emotional choice, or moral remainder; none is a threat cliffhanger. No Coda entry depicts a Foreign_Signal return, counterphase, renewed combat, campaign, spectacle, or adversary proof. Active counterphase closes at 112.
- **Requirement 15.6 has not run and is not satisfied here.** [`editorial-log.md`](editorial-log.md) holds zero active `EditorialFinding` records and `Baseline.calibration_finding_ids` is `[]`, which is the honest state: no prose exists to review.

### Verified — no prose, and site isolation

No file exists under `chapters/`; all four movement directories hold only their `.gitkeep`. The complete Provisional_Arc contains no Prose_Body, satisfying Requirement 1.1. `python3 .tools/check_novel.py --site-exclusion` passes with `manuscript_entries=0` and exit status 0, and the eight-test fixture suite in `.tools/tests/test_site_exclusion.py` passes. The checker's own `LIMIT` line stands: a passing local reference check does not prove the external Site_Build has adopted the Manuscript_Exclusion_Contract.

### Repaired

Five stale prose statements. All five were commentary, which under the [persistence contract](#persistence-contract) can never repair, complete, or override a record — so no record value, invariant, or continuity fact was wrong in any of them. They were false sentences in a binding planning artifact, and are now correct.

1. **Four movement-section sentences still named the pre-5.6 reveal release chapters.** Task 5.6 moved `REVEAL-NIA-SOURCE-CASUALTY` to 24 and `REVEAL-CASUALTY-CONSEQUENCE` to 52 in the `Reveal` records and in this document's [reveal table](#reveal-reference-rules), but four sentences in the Discovery and Private_Defense sections were left behind: the Discovery invariant naming release "at 23", the Discovery entries preamble reading "advanced at 21, released at 23, and completed at 24", the Private_Defense invariant naming release "at 53", and the Private_Defense entries preamble reading "advanced at 52 and released at 53". All four now name 24 and 52 and state which chapter is the owning POV's. The underlying records were already correct and are unchanged: release 24 is Nia's chapter inside the unchanged 21–25 window, release 52 is Nia's chapter inside the unchanged 50–55 window, and 23 and 53 still advance their reveals from Mara's and Julian's viewpoints.
2. **The worked template preamble claimed no chapter 124 entry exists.** Task 5.5 made that false. The sentence now explains the actual reason the template cannot collide with a planned chapter — its `chapter` values 900 and 901 sit outside the 1–128 sequence — and points to the real `POV-MARA` chapter 124 entry in the Coda section. The template's instructional purpose, its untyped fence, and its `EXAMPLE` identifiers are untouched.

One further repair was made outside this document. [`voice-briefs.md`](voice-briefs.md)'s calibration representation table credited `POV-MARA` with the whole 1–5 opening sequence and with chapter 73, and `POV-NIA` with 1–5 only. Counted from each entry's own `pov_id`, the eight calibration chapters divide Mara 1/3/5/124, Nia 2/4/73, Safiya 118, Julian none — the same division [task 5.7](#task-57-calibration-batch) already recorded. The table now matches, which fixes which brief the Requirement 5.10 finding for chapter 73 is evidence against: `VOICE-NIA`, not `VOICE-MARA`. No brief, obligation, or record value changed.

### Still open, and why it does not block the flag

**Pairing-session chronology still has no home.** Task 5.6 referred this upward and it is unresolved. The Canon Bible's `evidence_scope` for `TL-MINDWARS-COUNTERPHASE` and `TL-MINDWARS-SHIELD` states that pairing sessions in those ranges "receive their own chronology in the Arc Outline," but this document's [persistence contract](#persistence-contract) creates no `TimelineEntry` record and never can. No PAIR-mode chronology exists for 36–42, 70–77, 78–93, or 94–108; only `TL-PRIVATE-PROTOCOL` at 56–61 carries `mode: PAIR`, `pair_state`, and `pairing_evidence`. The Canon Bible therefore points at a record type in another document that document is forbidden to hold.

This does not block `provisional_arc_complete`, for four reasons.

1. **It is not an Arc_Outline defect.** The flag's declared condition is that all 128 entries and every direct reference they make exist and resolve. No `ArcEntry` references a per-session PAIR chronology; every `timeline_id` and every `record_horizon.through_timeline_id` resolves. The condition is met.
2. **The requirements at risk do not bind this document.** Requirement 14.1 binds the Canon_Bible; 14.10 and 14.11 bind the Manuscript; 14.12 binds the Manuscript_Project. The Arc_Outline obligations task 5.8 must verify — Requirements 15.1, 15.2, and 15.3 — all pass, as the coverage table above shows.
3. **Nothing is currently violated.** 14.10 through 14.12 attach to a depicted Pairing_Session in a Prose_Body. No Prose_Body exists. Those criteria are unenforced in these four ranges rather than broken, which is what task 5.6 recorded.
4. **The alternative would be worse.** Closing it here would mean either fabricating Character IDs for the unnamed supporting participants at 36, 38, 41, 81, 82, 84, 89, 91, 102, and 105, or adding a second mode to a `TimelineEntry` that already carries exactly one — inventing canon in the first case and breaking Requirement 14.1's one-mode rule in the second.

**What it does block.** Task 7.3 requires the minimal checker to parse each Timeline_ID's `technical_state` and, for chapter 73 specifically, to "validate only the objective `CANCEL` bounded-consent state and `PAIR` metadata and references." Chapter 73 is a Calibration Batch member inside 70–77, and there is no PAIR metadata in that window to validate. The gap therefore blocks the chapter-73 half of task 7.3, and with it task 8.3, but not task 5.8 and not the task 6 checkpoint.

**Minimal correct fix, and its owner.** Task **4.2**, which owns [`canon-bible.md`](canon-bible.md) and the four-mode classification. Two changes: add one `mode: PAIR` `TimelineEntry` per uncovered range — overlapping the existing scene window exactly as the record-custody windows already do, each carrying its own `pair_state` and `pairing_evidence` and naming only living participants who already hold Character IDs, which for the Mara–Nia channel means `CHAR-001`, `CHAR-002`, and the existing `PAIR-CAL-MARA-NIA` calibration; and correct the two `evidence_scope` sentences to point at the Canon Bible rather than at this document. Any range whose sessions belong only to unnamed supporting participants additionally needs task **4.3** to declare Character IDs first, or must record the absence honestly instead of naming participants who do not exist. Neither change is made here, and no Character ID or canon fact is invented to close it.

**Closed 2026-09-15 by an author-approved amendment pass**, exactly as scoped above: six non-viewpoint Character IDs were declared first, then thirteen `mode: PAIR` entries were added to the Canon Bible, then the two `evidence_scope` sentences were corrected to name those entries, and only then did this document name the participants. Chapter 73 also gained the Fluent_Pairing beat this section identified as the blocker for the chapter-73 half of task 7.3 and for task 8.3. Both are unblocked. See the [2026-09-15 amendment pass](#2026-09-15-author-approved-amendment-pass).

### Flag decision

`Baseline.provisional_arc_complete` is set to `true`. Eighty objective checks pass with no failures; all 128 entries exist; every direct reference resolves; tasks 5.2 through 5.7 are complete; and tasks 1.2, 1.3, 1.4, 1.5, and 1.7 are resolved, binding, and mirrored across the planning artifacts.

The flag asserts nothing beyond that. `state` stays `provisional`, `final_targets` stays `null`, no Chapter File exists for any of the eight calibration chapters, no gate has run, `calibration_finding_ids` is `[]`, and no Prose_Body may begin outside the exploratory calibration path. The path to `approved` still runs: minimal checker gate, calibration prose and editorial findings, exactly one Baseline_Revision_Pass dispositioning every finding, a passing full-suite gate, then author approval and Final_Targets.
---

## 2026-09-15 author-approved amendment pass

**Date: 2026-09-15. Scope: this document's chronology window table, the Private_Defense and Mindwars section prose, and thirteen field values across twelve `ArcEntry` records.** The author approved this change set after review. It closes the pairing-chronology gap that [task 5.6](#referred-upward-not-repaired) referred upward and [task 5.8](#still-open-and-why-it-does-not-block-the-flag) restated. It creates no record in this document, adds no field, changes no invariant, and writes no prose.

### What changed elsewhere, and why this document had to follow

[`canon-bible.md`](canon-bible.md) declares six non-viewpoint supporting Character IDs and thirteen `mode: PAIR` `TimelineEntry` records, and [`record-schemas.md`](record-schemas.md) states the [Character ID registry](record-schemas.md#character-id-registry) that lets a Character ID exist without a `POVProfile`. Task 5.8 named both prerequisites exactly: the fix needed `TimelineEntry` records this document may not hold, and Character IDs for participants who did not yet have them. Both now exist, so the sessions this outline had described only by role can name the people in them.

| Supporting participant | Sessions | Recorded chronology |
|---|---|---|
| `CHAR-005` Ada Ferris, `CHAR-006` Lena Ferris | 36, 37, 41 | `TL-PAIR-CLINICAL-BENEFIT` |
| `CHAR-007` Tomas Reyner, `CHAR-008` Cora Baird | 38; 102 and 105 | `TL-PAIR-DISPATCH-DEMONSTRATION`, `TL-PAIR-SHELTER-INTAKE` |
| `CHAR-007` Tomas Reyner with `CHAR-002` Nia | 91 | `TL-PAIR-DISPATCH-OPERATIONS` |
| `CHAR-009` Idris Vane with `CHAR-001` Mara | 81; 104 | `TL-PAIR-OPERATOR-SHIFT-VANE`, `TL-PAIR-NULL-NIGHT-COORDINATION` |
| `CHAR-010` Rhea Osei with `CHAR-001` Mara | 84 | `TL-PAIR-OPERATOR-SHIFT-OSEI` |
| `CHAR-009` and `CHAR-010` with each other | 82, 89 | `TL-PAIR-OPERATOR-TRAFFIC` |

None of the six holds a POV, a `pov_id`, a Voice Brief, or a chapter. The four POVs, the 56/32/33/7 loads, and the 29/32/51/16 movement allocation are untouched.

### Chapter 73 gains its Fluent_Pairing beat

Task 8.3 requires a valid Fluent_Pairing beat in the chapter it drafts, and 73's beat set was 74, 75, 77 — the beat was in the neighbours, not the chapter. Chapter 73 now carries one: Nia coordinates her own conditions with Mara over their consented channel, contribution by deliberately sent contribution, while she answers **aloud** in the room. The spoken answer matters. `MOT-YES-01` and the protected question `Did I say yes?` stay where they were, spoken, in Nia's mouth, and no consent is given by channel.

Two fields changed on that entry: `purpose` and `record_horizon.knowledge_limit`. Everything else is byte-identical — `pov_id: POV-NIA`, `timeline_id: TL-MINDWARS-COUNTERPHASE`, `status: exploratory`, `calibration_selected: true`, the unchanged `representative_purpose` that only task 5.7 may touch, `estimated_length_class: long-outlier`, `estimated_words: null`, `outlier_purpose`, both cross-cuts, both motif events, and `REVEAL-COUNTERPHASE-TRANSMITS`. Chapter 73's neighbours are Mara's 72 and 74, so 73 remains a single-chapter run and no run limit is touched; the largest run total in the book is still 3,450 words at 100–101.

`DEC-017` is intact and untouched. The parallel it protects is the one between this consented bounded cancellation and the later area-scale null: no character states it anywhere in 62–123, and it is still named exactly once, inside the existing `MOT-RECORD-03` beat in Chapter 128. The new beat adds a different and unremarked contrast inside the room — a two-person addressed revocable channel carrying only what is offered, beside one unaddressed field that subtracts — and no character comments on that either. The concrete inside-the-field vocabulary Chapter 118 will reuse is unchanged and remains this chapter's calibration burden.

### Beat coverage after the pass

| Range | Beats | Change |
|---|---|---|
| 36–42 | 36, 37, 38, 40, 41, 42 | participants named; no beat added or moved |
| 56–61 | 56, 57, 58, 59, 60, 61 | unchanged |
| 70–77 | **73**, 74, 75, 77 | 73 added |
| 78–93 | 81, 82, 88, 89, 91 | participants named; no beat added or moved; 83 carries no paired channel |
| 94–108 | 94, 98, 102, 104, 105 | 102 and 105 stated as beats, matching the shelter sessions this section already described |

Every chapter in the Beats column is now inside the `chapter_numbers` of a Canon Bible entry carrying `mode: PAIR`, so Requirement 14.1 holds for each of those events and Requirements 14.10 through 14.12 are recorded rather than only narrated. Requirements 15.2 and 15.3 continue to hold: every session sits in an existing Mara, Nia, or Julian chapter, and no POV was created.

### Chapter 83 carries no paired channel

This pass first gave Chapter 83 a coordinating channel and a `mode: PAIR` chronology entry. Both were removed on author approval, and the removal is a craft decision, not an oversight. Three reasons. It repeated Chapter 73's staging — Nia setting conditions with Mara over their channel while a bounded field runs — instead of escalating from it, and 73 already owns that scene. Chapter 83's subject is one person alone with a bounded field and a revocation she never uses, and a second person on a channel gives her someone to answer to, which is the opposite of the beat. And the 78–85 sequence needs one chapter at its center with the machinery quiet; every other chapter in the range has apparatus running in it.

So the 78–93 beat list is **81, 82, 88, 89, 91**, and Requirement 15.1 is satisfied for the range by those five. The absence at 83 is structural and unremarked: no character comments on it, no entry field has Nia decline to pair, and nothing in the chapter names a channel that is not there. A later pass must not add a PAIR entry, a participant, or a line of dialogue to close the apparent gap. `Editorial_Review` enforces this.

Nothing else moves. Chapter 83's `ArcEntry` is byte-identical to its pre-pass state — `pov_id: POV-NIA`, `timeline_id: TL-MINDWARS-SHIELD`, both cross-cuts, `motif_events: []`, purpose, hook, and record horizon all unchanged. No requirement changes. No consent record changes. `TL-MINDWARS-SHIELD` keeps its `mode: CANCEL` state exactly as written, bounded-local, with Nia's current revocable individual consent and null institutional authorization, because the bounded consented cancellation at 83 is still real and still hers. The Canon Bible holds thirteen amendment-added `mode: PAIR` entries, fourteen counting `TL-PRIVATE-PROTOCOL`.

### Superseded rows in the earlier audits

The dated audit sections are left as written. Two rows in them are superseded for their beat lists only:

- [Task 5.6 audit](#verified), **Fluent pairing beats** row: its 70–77 and 78–93 beat lists and its unnamed supporting participants stand as of 2026-09-14 and are superseded by the table above. That row's own inline note names only 70–77 and 94–108 as superseded ranges; this list supersedes it and 78–93 belongs on it too, because 83 is no longer a beat.
- [Task 5.8 verification pass](#verified--mandatory-fluent_pairing-coverage), 70–77, 78–93, and 94–108 rows: same, superseded for the beat lists only. The POV columns and the 15.2/15.3 findings are unaffected.

Where either audit lists 83 among the 78–93 beats, the table above governs: the beats are 81, 82, 88, 89, 91. Nothing else in either audit changes, and the eighty checks recorded on 2026-09-14 were not re-run by this pass.

### What this pass did not do

No Chapter File was created and no prose was drafted. No requirement, design, or decision document was edited. No POV, Voice Brief, `POVProfile`, motif event, literal-phrase constraint, `Reveal`, `CrossCut`, or `Baseline` field was added or changed. No entry's `timeline_id`, `status`, `calibration_selected`, or `representative_purpose` changed, so global invariants 19 and 20 still describe the current state. `Baseline.provisional_arc_complete` stays `true` and `state` stays `provisional`.
