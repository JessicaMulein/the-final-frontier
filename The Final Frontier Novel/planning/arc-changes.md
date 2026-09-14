# Arc Changes

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `ArcChange`  
Workflow authority: Requirements 1.16–1.18, 10.7, 10.8, and 13.5–13.10; the design's Baseline, Arc Change, status, and delivery rules

This document is the active audit trail for changes proposed after the Approved Baseline. It makes an arc, continuity, motif, POV, voice, or related reference change atomic across every affected project record.

## Initialization state

**Active `ArcChange` records: 9.**

`ARC-CHANGE-VOICE-SEPARATION-001` is the ninth post-baseline change and is `complete`. It closes the Discovery current-evidence gap, repairs fifteen chapter revisions including two authorization-continuity gaps at Chapters 16 and 27, rebuilds one duplicated warmth scene, gives Chapter 57 a physical body, and applies one house spelling standard across the delivered manuscript. It changes no `ArcEntry`, canon fact, motif, reveal, POV, or movement allocation, and it leaves the `POV-MARA`/`POV-NIA` voice-separation finding open as the sole blocker on task 14.

`ARC-CHANGE-REVISION-001` and `ARC-CHANGE-REVISION-002` are the second and third post-baseline changes, both dated 2026-09-18 and both `in-progress`. They authorize the author-directed revision pass on delivered Chapters 1–46 under `DEC-018` and the supporting canon that pass requires. Their Private Defense and planning work is complete; current Discovery chapter review, objective reruns, and movement-gate obligations remain open. See [`ARC-CHANGE-REVISION-001`](#arc-change-revision-001--prose-revision-of-delivered-chapters-146-under-dec-018) and [`ARC-CHANGE-REVISION-002`](#arc-change-revision-002--dec-018-supporting-canon).

`ARC-CHANGE-LENGTH-GOVERNANCE-001` is the eighth post-baseline change and is `complete`. It records `DEC-021`, closes the obsolete mass re-budget by supersession rather than performance, authorizes and synchronizes the Chapter 118 craft expansion, and carries the passing reruns for the nine-finding revision pass and task 13.6. It changes no `ArcEntry`, canon fact, motif, POV, reveal, or movement allocation.

The Approved Baseline remains `BASELINE-FINAL-FRONTIER-PROVISIONAL` with `state: approved` in [`arc-outline.md`](arc-outline.md). Task 10.2 established that baseline. `ARC-CHANGE-DISCOVERY-001` is the first post-baseline correction: task 12.7 aligned the source/casualty Reveal record with the current Chapter 23 prose rather than forcing artificial withholding, without changing prose, canon identity, causation, motif placement, POV load, or movement architecture.

## Pre-approval Baseline Revision Pass

The single `Baseline_Revision_Pass` was performed at `2026-09-16T21:00:00Z` against the complete provisional Arc Outline and the corrected calibration evidence in `editorial-log.md`. The machine-readable authority is `BASELINE-FINAL-FRONTIER-PROVISIONAL.baseline_revision_pass` in [`arc-outline.md`](arc-outline.md); this section supplies the task-10.1 Arc Change audit requested for human review.

Impact assessment found **no genuine Arc_Outline change**. The two original `revision` findings were prose-level issues already resolved in the exploratory Chapter Files and passed on corrective reread. Every other finding affirms the existing purpose, chronology, POV, Cross Cut, Hook, motif, voice, or continuity plan. Therefore every finding receives `no-change-rationale`, every `arc_change_id` remains `null`, and no typed `ArcChange` record is invented before approval.

The pass specifically preserves the corrected December processing-latency canon: continuous raw acquisition; no gap for Nia; no transmit stage; and an eight-second receiver-side acquisition-to-resolved-output reconstruction under the same early configuration and information conditions, not a permanent physical constant, source-side delay, or hidden transmission. It also preserves every corrected prose/planning decision, all eight `exploratory` statuses, Julian's still-open first-appearance review at Chapter 6, and the existing Chapter 73/118 delayed sensory echo.

| Finding | Disposition | Arc_Outline rationale |
|---|---|---|
| `EDITORIAL-CAL-001` | `no-change-rationale` | Mara's represented Discovery and Coda registers already perform the planned experiment-to-consequence movement and Chapter 124 Coda_Turn. |
| `EDITORIAL-CAL-002` | `no-change-rationale` | Nia's chapters validate the planned dispatch logic, evidence restraint, consent authority, and usable-self-trust trajectory. |
| `EDITORIAL-CAL-003` | `no-change-rationale` | Chapter 118 validates Safiya's voice, agency, describe-never-quote handling, and unspecified heritage base. |
| `EDITORIAL-CAL-004` | `no-change-rationale` | The shared reader-instruction tic was resolved only in exploratory prose and passed by `EDITORIAL-CAL-013`; no arc or Voice Brief value changed. |
| `EDITORIAL-CAL-005` | `no-change-rationale` | Opening momentum and receive-only facts validate the Chapters 1–5 sequence and corrected receiver-owned processing latency. |
| `EDITORIAL-CAL-006` | `no-change-rationale` | Existing opening Cross Cuts are reciprocal, clear, and materially nonredundant. |
| `EDITORIAL-CAL-007` | `no-change-rationale` | Existing hooks and pacing already vary across information, decision, absence, and moral-remainder turns. |
| `EDITORIAL-CAL-008` | `no-change-rationale` | Chapter 73 realizes its current bounded-consent, pairing, authority, and unresolved-provenance purpose. |
| `EDITORIAL-CAL-009` | `no-change-rationale` | The copied cancellation-field phrasing was resolved only in Chapter 118 prose and passed by `EDITORIAL-CAL-014`; `DEC-017` remains unchanged. |
| `EDITORIAL-CAL-010` | `no-change-rationale` | Safiya owns the request and loss, while Mara's truth-and-physics refusal validates the current Coda sequence. |
| `EDITORIAL-CAL-011` | `no-change-rationale` | Tenderness, restraint, human cost, emotional truth, and originality pass under the present architecture. |
| `EDITORIAL-CAL-012` | `no-change-rationale` | Julian's calibration absence remains deliberate; Requirement 5.11 is still due at planned Chapter 6. |
| `EDITORIAL-CAL-013` | `no-change-rationale` | The corrective follow-up confirms distinct sentence-making without changing POV assignments or Voice Brief guidance. |
| `EDITORIAL-CAL-014` | `no-change-rationale` | The corrected Chapter 73/118 echo now carries only the planned sensory family and leaves the link unnamed. |
| `EDITORIAL-CAL-015` | `no-change-rationale` | Corrected chronology validates the already synchronized continuous-acquisition, variable-reconstruction-latency plan. |
| `EDITORIAL-CAL-016` | `no-change-rationale` | Chapter 73 preserves its contemporaneous horizon, local authorization, consequence, and usable self-trust without scalable doctrine. |
| `EDITORIAL-CAL-017` | `no-change-rationale` | Safiya's maternal-language continuity, Mara's refusal, and the two kettle assignments already agree across plan and prose. |
| `EDITORIAL-CAL-018` | `no-change-rationale` | The final reread validates the provisional plan's momentum, Cross Cuts, hooks, restraint, human cost, and emotional truth. |

The outcome count is exactly **18 no-change rationales, 0 Arc_Outline changes, and 0 active ArcChange records**. At completion of task 10.1, this pass had not yet performed task 10.2: `author_approval` and `final_targets` were still `null`, the Baseline was `pending-author-approval`, and no chapter became approved. Task 10.2 subsequently approved that unchanged revised outline and recorded Final_Targets in the Baseline record. All eight calibration chapters remain exploratory; baseline approval did not promote them.

## Approved-baseline boundary

The baseline became approved at `2026-09-16T22:00:00Z` on Jessica Mulein's explicit response, `Approve recommended baseline`. Its controlling Final_Targets are exactly 128 planned chapters and an inclusive total of 130,000–150,000 Prose_Words. The approval preserves the corrected configuration-dependent receiver reconstruction latency, the `DEC-001` title, the `DEC-006` restrained record frame, and all eight exploratory calibration statuses. It changes no arc value and creates no `ArcChange`; it establishes the prior state against which the next actual change must be recorded.

An actual project change exists here only when it appears in a schema-compatible typed JSON fence whose opening line is exactly:

`json record=ArcChange schema=1`

The JSON body must be one object or a nonempty array of `ArcChange` objects. Typed fences are reserved for real proposals. Templates, placeholders, empty arrays, speculative changes, and `EXAMPLE` records must not appear in typed fences in this file. Commentary and tables outside typed fences are never parsed as record values.

The obligation catalog and worked templates below therefore use untyped `json` fences and `EXAMPLE` identifiers. Because they carry no `record=` type, the parsing contract never treats them as `ArcChange` records, and nothing in them is an approved change.

## When an `ArcChange` is required

After baseline approval, every proposed change to the approved arc or to continuity, motif placement or function, POV state, Voice Brief state, chapter dependency, or another baseline-governed reference must be documented here before the changed state can be treated as valid. The Approved Baseline is never silently overwritten.

A proposal may be edited while it is `proposed` or `in-progress`, but the revised state has no approved continuity authority until the change is `complete`. Partial synchronization, an approval without evidence, or edits made in only one affected file cannot establish the new state.

## `ArcChange` record contract

Every active record uses exactly the schema fields below and no additional fields.

| Field | Active-record rule |
|---|---|
| `arc_change_id` | Unique stable ID that is never reused. |
| `date` | Proposal date in `YYYY-MM-DD` form. |
| `prior_state` | A nonempty JSON object capturing the exact approved logical values before the change. It names enough IDs, chapter/status values, assignments, or other fields to distinguish the old state without inference. |
| `revised_state` | A nonempty JSON object containing the intended replacement values at the same logical level as `prior_state`. It does not become authoritative until completion. |
| `rationale` | A nonblank narrative, calibration, continuity, or author-feedback reason for the change. |
| `affected_chapters` | Unique chapter numbers in ascending order. It may be empty only for a genuinely reference-only change. |
| `affected_documents` | A unique, nonempty list of workspace-relative paths covering every document that must change or supply synchronization evidence. |
| `synchronization_obligations` | A nonempty array. Each item contains exactly `document`, nonblank `required_change`, `status` (`pending` or `complete`), and `evidence_ref` (`null` while pending, nonblank when complete). |
| `approval` | `null` before approval. When present, an object containing exactly `approved_by`, `approved_at`, and `approval_record`. |
| `status` | Exactly `proposed`, `approved`, `in-progress`, `complete`, or `rejected`. |
| `completed_at` | `null` before completion; an RFC 3339 timestamp with explicit offset when `status` is `complete`. |

`prior_state` and `revised_state` are the schema's intentionally open JSON objects, but they are not free-form commentary. They must use stable IDs and explicit values so a reviewer and checker can determine what changed. The prose rationale explains why; it cannot replace either state object.

## Atomic change workflow

1. **Open the proposal.** Add a real `ArcChange` with `status: proposed`, exact prior and revised state, rationale, affected chapters, affected documents, and every known synchronization obligation.
2. **Assess all references.** Trace the proposal through the Arc Outline, Chapter Files, Canon Bible, Motif Ledger, POV Roster, Voice Briefs, and any gate or status record that can be affected. Add newly discovered paths and obligations to the same change before completion.
3. **Demote before relying on edits.** If an affected Chapter File or ArcEntry is `approved` or `final` and receives a Substantive Prose Change or a changed arc dependency, set both its Chapter Header and matching ArcEntry to `revised`. If the chapter belongs to a delivered batch, that affected work and Batch Status also return to `revised`.
4. **Record approval.** A change may enter `approved` or `in-progress` only with the required approval object and approval record. Approval authorizes synchronized implementation; it does not make a partly applied revised state valid.
5. **Apply one atomic synchronization set.** Make every listed change and retain an evidence reference for each obligation. An obligation becomes `complete` only when its named document agrees with the revised state.
6. **Rerun affected gates.** Run every objective gate whose metadata, references, counts, literal constraints, or scope changed, and every editorial gate whose prose or craft context changed. A prior gate over superseded state cannot support reapproval.
7. **Complete only with evidence.** Set `status: complete` and record `completed_at` only when every synchronization obligation is complete, every obligation has a nonblank evidence reference, approval is present, and all affected records agree.
8. **Reject without adoption.** A `rejected` proposal does not alter the Approved Baseline. Any exploratory text associated with it remains explicitly exploratory and cannot be presented as approved continuity.

## Synchronization impact rules

The affected-document list and obligations are change-specific, but impact assessment is mandatory across the full reference system.

- **Arc beat, purpose, chronology, reveal, or dependency:** synchronize every affected ArcEntry, Chapter File, Canon Bible timeline/reveal/extension record, and direct planning reference.
- **Continuity change:** within the same `ArcChange`, synchronize every affected entry in the Arc Outline, Chapter Files, Canon Bible, Motif Ledger, POV Roster, and Voice Briefs. If impact review establishes that a named component needs no value change, preserve that conclusion as explicit synchronization evidence rather than assuming silence means review.
- **Motif placement, function, movement, representation, or phrase scope:** synchronize the Motif Ledger, affected ArcEntries, affected Chapter Headers, and every other continuity, POV, or voice record whose declared state changes.
- **POV or relationship change:** synchronize the POV Roster, Voice Briefs, affected ArcEntries and Chapter Headers, Canon Bible extensions/relationships, and all affected load or movement-coverage records.
- **Voice-state or Coda-Turn change:** synchronize the Voice Brief, affected ArcEntries/chapters, calibration or first-appearance evidence, and editorial gates that relied on the prior guidance.
- **Author feedback changing a delivered chapter or planned beat:** demote affected work and the batch to `revised`, apply the feedback through this record when post-baseline architecture or references are involved, and rerun every affected objective and editorial gate before reapproval or finalization.

Every affected reference must either be synchronized to the revised state or carry explicit evidence that review found no value change necessary. A document omitted from the original proposal but later found to be affected must be added to the same record; it must not be left for an undocumented follow-up.

### Machine-readable obligation catalog

The obligations themselves live in each record's `synchronization_obligations` array, which is the only machine-readable obligation list with continuity authority. The block below is the authoring catalog that says which documents that array must cover for each class of change. It is **not** a project record: it carries no `record=` type, defines no new record type, and never substitutes for a real record's obligations.

```json
{
  "catalog": "arc-change-synchronization-obligations",
  "catalog_version": 1,
  "is_project_record": false,
  "path_base": "manuscript root, matching the ArcChange example in record-schemas.md",
  "invalid_until_synchronized": "A post-baseline change remains invalid until every affected reference listed for its class is synchronized within that same ArcChange record.",
  "same_record_rule": "Every obligation for the change class must appear in one ArcChange. Splitting obligations across records, or deferring one to an undocumented follow-up, blocks status: complete.",
  "no_change_needed_rule": "A listed document whose values need no change still requires its own obligation whose required_change records the review conclusion and whose evidence_ref cites that conclusion once complete.",
  "change_classes": [
    {
      "change_class": "continuity",
      "trigger": "Any post-baseline change to established continuity.",
      "required_documents": [
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "chapter_file_scope": "Every Chapter File whose header, status, or prose depends on the changed continuity.",
      "authority": "Requirement 1.17"
    },
    {
      "change_class": "motif",
      "trigger": "Changed motif placement, dramatic function, movement, representation mode, phrase scope, or event identity.",
      "required_documents": [
        "planning/motif-ledger.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md"
      ],
      "chapter_file_scope": "Every Chapter Header whose motif_events set changes, plus any file inside a changed literal-phrase scope.",
      "authority": "Requirements 1.17, 7.1-7.18"
    },
    {
      "change_class": "arc-beat",
      "trigger": "Changed purpose, hook, chronology, cross-cut, reveal horizon, length class, or chapter dependency.",
      "required_documents": [
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/editorial-log.md"
      ],
      "chapter_file_scope": "Every Chapter File participating in the changed beat or cross-cut relationship.",
      "authority": "Requirements 1.16, 1.17"
    },
    {
      "change_class": "pov",
      "trigger": "Changed POV identity, mapping, knowledge, relationship, movement coverage, or chapter load.",
      "required_documents": [
        "planning/pov-roster.md",
        "planning/voice-briefs.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md"
      ],
      "chapter_file_scope": "Every Chapter Header whose pov_id or status changes.",
      "authority": "Requirement 1.17"
    },
    {
      "change_class": "voice",
      "trigger": "Changed Voice Brief guidance, Reverb Profile, movement evolution, Coda Turn, or review evidence.",
      "required_documents": [
        "planning/voice-briefs.md",
        "planning/pov-roster.md",
        "planning/editorial-log.md",
        "planning/arc-outline.md"
      ],
      "chapter_file_scope": "Every drafted Chapter File whose prose relied on the superseded guidance.",
      "authority": "Requirements 1.17, 13.10"
    },
    {
      "change_class": "status-demotion",
      "trigger": "A Substantive Prose Change or changed dependency affecting an approved or final chapter, or author feedback on delivered work.",
      "required_documents": [
        "planning/arc-outline.md",
        "planning/editorial-log.md"
      ],
      "chapter_file_scope": "Every affected Chapter Header, which must carry status revised in step with its ArcEntry.",
      "authority": "Requirements 10.7, 10.8, 13.9, 13.10"
    },
    {
      "change_class": "reference-only",
      "trigger": "A changed planning reference on which no Chapter File depends.",
      "required_documents": [],
      "chapter_file_scope": "None. This is the only class permitted to record affected_chapters as an empty array.",
      "authority": "Requirement 1.16",
      "note": "The record still names every document holding the changed reference, and impact review must confirm that no Chapter File depends on it."
    }
  ]
}
```

One change may belong to more than one class. When classes overlap, the record carries the union of their obligations.

## Status and validity rules

| Status | Meaning and permitted reliance |
|---|---|
| `proposed` | The change is defined but not approved. The Approved Baseline remains controlling. |
| `approved` | Implementation is authorized. The revised state is still invalid for approval/finalization until synchronization completes. |
| `in-progress` | One or more obligations are being applied. All affected work remains `revised` or exploratory, and partial state is not authoritative. |
| `complete` | Approval exists; all obligations and evidence are complete; affected records agree; required gates have rerun. Only now may the revised state support approved/final work. |
| `rejected` | The proposal is not adopted and supplies no continuity authority. |

A post-baseline change remains invalid until **every listed affected reference is synchronized within the same recorded change**. The record's `synchronization_obligations` array is the machine-readable list that decides this: no obligation may be tracked elsewhere, deferred to a second record, or satisfied by prose commentary. No partial synchronization may be treated as approval. A `complete` record requires all obligations to use `status: complete`, all `evidence_ref` values to be nonblank, `approval` to be present, and `completed_at` to be present.

## Status demotion and reapproval

A Substantive Prose Change to an `approved` or `final` chapter immediately requires `status: revised` in both the Chapter Header and its ArcEntry. A post-baseline planned-arc change that invalidates an approved chapter's dependencies requires the same paired demotion even before prose is rewritten. The statuses must remain synchronized.

The affected chapter and batch cannot return to `approved` or `final` until:

1. every Arc Change synchronization obligation is complete;
2. the current Chapter Header and ArcEntry agree;
3. every affected objective gate passes against current files and references;
4. every affected editorial gate passes against current prose and guidance; and
5. approval-time reference records are synchronized.

Objective success cannot substitute for editorial success, and editorial approval cannot override an objective violation or incomplete Arc Change. See [`editorial-log.md`](editorial-log.md) for the independent editorial record and gate workflow.

## Completion evidence

Each synchronization obligation's `evidence_ref` identifies the changed path, record ID, gate result, or other durable proof that the named obligation is complete. Completion evidence must permit a reviewer to trace the revised state across all affected records; a general statement such as “updated everything” is insufficient.

The `approval.approval_record` identifies the durable authorization. `completed_at` records when the atomic set actually became complete, not when the first edit was made. The historical `ArcChange` remains in this file after completion or rejection; it is never replaced by an undocumented summary.

## Worked templates

**The two blocks below are templates, not proposals.** An Approved Baseline now exists, but nothing in these untyped examples is proposed or approved, and every identifier, path, date, and value is an illustrative fixture. The chapter path in the second template is a placeholder for a Chapter File the Arc Outline has not yet named. Copy the shape, then write a real proposal into a typed fence under [Active records](#active-records).

A real record matures in place: the same `arc_change_id` moves from `proposed` through `approved` or `in-progress` to `complete`. The two templates show the opening and closing forms of that lifecycle using two different illustrative changes, so they are not two states of one record.

The first shows the reference-only form, which is the only form permitted to record `affected_chapters` as an empty array. Every obligation is `pending`, so `evidence_ref` is `null`, `approval` is `null`, and the revised state carries no continuity authority yet.

```json
{
  "arc_change_id": "ARC-CHANGE-EXAMPLE-TEMPLATE-001",
  "date": "2026-09-14",
  "prior_state": {
    "record_type": "NovelExtension",
    "extension_id": "EXT-EXAMPLE-UNUSED-DETAIL",
    "state": "approved",
    "superseding_arc_change_id": null
  },
  "revised_state": {
    "record_type": "NovelExtension",
    "extension_id": "EXT-EXAMPLE-UNUSED-DETAIL",
    "state": "retired",
    "superseding_arc_change_id": "ARC-CHANGE-EXAMPLE-TEMPLATE-001"
  },
  "rationale": "Illustrates the reference-only form: an extension that no Chapter File depends on is retired, so no chapter value changes and no chapter status is demoted.",
  "affected_chapters": [],
  "affected_documents": [
    "planning/canon-bible.md",
    "planning/arc-outline.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/canon-bible.md",
      "required_change": "Set the extension state to retired and record this change as its superseding Arc Change.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Confirm that no ArcEntry reveal reference or record horizon cites the retired extension, and record that conclusion.",
      "status": "pending",
      "evidence_ref": null
    }
  ],
  "approval": null,
  "status": "proposed",
  "completed_at": null
}
```

The second shows the completed form of a combined motif and continuity change: the one case the Motif Ledger names as requiring an Arc Change, where Mindwars counterphase material stops being connective context and becomes a ledgered event with its own stable ID. Its obligations cover the full continuity sweep, including the documents that review found need no value change, and each carries an evidence reference. The three prior chain events are the real ledgered IDs; the new event uses an `EXAMPLE` identifier because no fourth chain event exists, and a real change would assign the next real chain ID.

```json
{
  "arc_change_id": "ARC-CHANGE-EXAMPLE-TEMPLATE-002",
  "date": "2026-09-15",
  "prior_state": {
    "record_type": "MotifEvent",
    "motif_family": "spectrum / wire / voice",
    "ledgered_chain_events": [
      "MOT-CHAIN-01",
      "MOT-CHAIN-02",
      "MOT-CHAIN-03"
    ],
    "mindwars_counterphase_representation": "connective context only, with no ledgered chain event in the Mindwars Part",
    "chapter_96_status": "approved"
  },
  "revised_state": {
    "record_type": "MotifEvent",
    "motif_family": "spectrum / wire / voice",
    "ledgered_chain_events": [
      "MOT-CHAIN-01",
      "MOT-CHAIN-02",
      "MOT-CHAIN-03",
      "MOT-EXAMPLE-CHAIN-04"
    ],
    "mindwars_counterphase_representation": "one ledgered event carrying its own distinct dramatic function",
    "new_event": {
      "motif_event_id": "MOT-EXAMPLE-CHAIN-04",
      "movement": "mindwars_part",
      "planned_chapter": 96,
      "participating_chapters": [
        96
      ],
      "representation_mode": "image",
      "literal_constraint_id": null
    },
    "chapter_96_status": "revised"
  },
  "rationale": "Illustrates the atomic form required when counterphase material acquires a distinct dramatic function: the event needs a new stable ID and every continuity reference must move with it inside one record.",
  "affected_chapters": [
    96
  ],
  "affected_documents": [
    "planning/motif-ledger.md",
    "planning/arc-outline.md",
    "chapters/mindwars-part/mindwars-part-096-counterphase-to-bone.md",
    "planning/canon-bible.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/editorial-log.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Add MOT-EXAMPLE-CHAIN-04 with its distinct dramatic function, movement, planned chapter, representation mode, scene scope, and Arc Change history.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md, MotifEvent MOT-EXAMPLE-CHAIN-04"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Add MOT-EXAMPLE-CHAIN-04 to the chapter 96 ArcEntry motif event set and set that entry's status to revised.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, ArcEntry 96"
    },
    {
      "document": "chapters/mindwars-part/mindwars-part-096-counterphase-to-bone.md",
      "required_change": "Add MOT-EXAMPLE-CHAIN-04 to the Chapter Header motif event set and set the header status to revised in step with the ArcEntry.",
      "status": "complete",
      "evidence_ref": "chapters/mindwars-part/mindwars-part-096-counterphase-to-bone.md, Chapter Header"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that the new event asserts no canon fact, extension, timeline, or reveal beyond the existing counterphase records, and record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, reviewed with no value change required"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm that the change alters no POV mapping, movement coverage, or provisional load, and record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md, reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm that the Mindwars movement evolution still supports the image family the new event uses, and record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md, reviewed with no value change required"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Rerun the chapter-local objective gate and the chapter editorial gate against the revised prose and record both results.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, GATE-EXAMPLE-TEMPLATE-CHAPTER-096 and GATE-EXAMPLE-TEMPLATE-EDITORIAL-096"
    }
  ],
  "approval": {
    "approved_by": "Author",
    "approved_at": "2026-09-15T14:00:00Z",
    "approval_record": "Illustrative author approval entry for ARC-CHANGE-EXAMPLE-TEMPLATE-002"
  },
  "status": "complete",
  "completed_at": "2026-09-16T18:00:00Z"
}
```

Note what the second template does not do. It does not return chapter 96 to `approved`. The revised state records `revised`, and the chapter recovers `approved` only through the rerun gates named in the last obligation. Nor does any obligation stand as `complete` without an evidence reference, because that combination is exactly the partial synchronization this document forbids.

## Active records

There are no active records at initialization. Real records are appended below this heading only when an actual post-baseline change is proposed.

## `ARC-CHANGE-DISCOVERY-001` — Reveal release aligned with current prose

Task 12.7 found one planning mismatch during honest movement review. The machine-readable Reveal said Nia owned reader release in Chapter 24, but Chapter 23 necessarily and explicitly verifies in Mara's limited POV that the December source and later casualty are Nia Calder. Making Mara conceal that known fact for one chapter would violate the design rule against artificial withholding. The correction gives Mara ownership only of the verified identity release; Nia continues to own the Chapter 24 refusal, interpretation, and denial of causal closure.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-DISCOVERY-001",
  "date": "2026-09-17",
  "prior_state": {
    "reveal_id": "REVEAL-NIA-SOURCE-CASUALTY",
    "reveal_owner_pov": "POV-NIA",
    "reader_release_chapter": 24,
    "discovery_chapter_statuses": {
      "1-5": "exploratory",
      "6-10": "approved",
      "11-29": "draft"
    }
  },
  "revised_state": {
    "reveal_id": "REVEAL-NIA-SOURCE-CASUALTY",
    "reveal_owner_pov": "POV-MARA",
    "reader_release_chapter": 23,
    "chapter_24_ownership": "Nia owns refusal of both unsupported origin accounts and the meaning of the confirmed identity; causation remains unresolved.",
    "discovery_chapter_statuses": {
      "1-29": "approved"
    }
  },
  "rationale": "Chapter 23 openly verifies the shared source/casualty identity from Mara's established record horizon. Aligning the Reveal with that scene preserves fair disclosure and rejects coy concealment, while Chapter 24 remains Nia's contradiction cut and supplies no absolution, archive validation, or origin proof.",
  "affected_chapters": [21, 23, 24],
  "affected_documents": [
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "chapters/discovery-part/discovery-part-021-reconstruction.md",
    "chapters/discovery-part/discovery-part-023-the-match-holds.md",
    "chapters/discovery-part/discovery-part-024-not-case-zero.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/canon-bible.md",
      "required_change": "Set REVEAL-NIA-SOURCE-CASUALTY owner/release to POV-MARA/23 and preserve Nia's Chapter 24 interpretive ownership and unresolved causation.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, Reveal REVEAL-NIA-SOURCE-CASUALTY"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Correct Discovery reveal commentary and synchronize eligible Chapter 1-29 ArcEntry statuses after current gates pass.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, Discovery_Part movement invariants and ArcEntries 1-29"
    },
    {
      "document": "chapters/discovery-part/discovery-part-021-reconstruction.md",
      "required_change": "Confirm that Nia's reconstruction advances identity joining but establishes no origin; no prose change required; synchronize approval status.",
      "status": "complete",
      "evidence_ref": "Chapter 21 current prose and GATE-CHAPTER-LOCAL-DISCOVERY-021-MOVEMENT-RERUN"
    },
    {
      "document": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
      "required_change": "Confirm that Mara's explicit verification is the fair reader release; no prose change required; synchronize approval status.",
      "status": "complete",
      "evidence_ref": "Chapter 23 current prose and GATE-CHAPTER-LOCAL-DISCOVERY-023-MOVEMENT-RERUN"
    },
    {
      "document": "chapters/discovery-part/discovery-part-024-not-case-zero.md",
      "required_change": "Preserve Nia's refusal and interpretive ownership without making the chapter the first factual identity release; no prose change required; synchronize approval status.",
      "status": "complete",
      "evidence_ref": "Chapter 24 current prose and GATE-CHAPTER-LOCAL-DISCOVERY-024-MOVEMENT-RERUN"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm that the reveal correction changes no motif placement, function, representation mode, or literal constraint.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed; MOT-CHAIN-01 remains Chapter 13 and MOT-COME-01 remains Chapter 16"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm that release ownership changes no POV identity, knowledge position, movement coverage, or 14/9/6 Discovery load.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm that Mara may state verified identity while Nia retains refusal and that both voices still preserve unresolved origin.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md, VOICE-MARA and VOICE-NIA Discovery evolution reviewed with no value change required"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Preserve the revision finding, resolve it to a follow-up pass, and record current chapter, batch, and movement editorial gates.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, EDITORIAL-DISCOVERY-MOVEMENT-006 and GATE-EDITORIAL-DISCOVERY-MOVEMENT-001"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record clean current Chapter_Local and batch objective reruns after reveal and status synchronization.",
      "status": "complete",
      "evidence_ref": "planning/gate-results.md, task 12.7 Discovery approval reruns"
    }
  ],
  "approval": {
    "approved_by": "Author via explicit task 12.7 correction instruction",
    "approved_at": "2026-09-17T02:00:00Z",
    "approval_record": "User instruction: if any finding is revision, make the best thematically and narratively coherent prose/planning corrections, preserve audit history, rerun affected objective gates, and re-review until all required current findings pass."
  },
  "status": "complete",
  "completed_at": "2026-09-17T03:30:00Z"
}
```

## `ARC-CHANGE-REVISION-001` — prose revision of delivered Chapters 1–46 under `DEC-018`

An author-commissioned craft review of the delivered manuscript returned nine `revision` findings and no passes, recorded as `EDITORIAL-REVISION-001` through `EDITORIAL-REVISION-009` in [`editorial-log.md`](editorial-log.md) with `GATE-EDITORIAL-REVISION-PASS-001`. The author directed that all nine be fixed. `DEC-018` records the binding craft rules; this record authorizes the prose revision and carries the status consequences.

**The consequence that matters most.** Discovery Chapters 1–29 are currently `approved` and passed the task 12.7 movement gate. Revising their prose invalidates that approval. This record states plainly that each of Chapters 1–29 moves to `status: revised` in both its Chapter_Header and its `ArcEntry` at the moment its prose changes, and that the Discovery movement Editorial_Gate must be re-recorded against the revised prose before any of them returns to `approved`. `GATE-EDITORIAL-DISCOVERY-MOVEMENT-001`, the `GATE-EDITORIAL-DISCOVERY-*` chapter and batch gates, and every task 12.7 finding **remain in the audit trail as historical records of the state they evaluated**. None of them is edited, deleted, or rewritten. A superseded gate is not a wrong gate; it is a gate over superseded text, which is exactly why step 6 of the atomic change workflow requires a rerun rather than an amendment.

**No chapter status changes in this wave.** This wave writes planning and canon only and touches no file under `chapters/`. Demotion happens per file, in the wave that edits that file, which is why every Chapter_File obligation below is `pending`.

`VOICE-JULIAN.first_appearance_review` is preserved as valid. It is carried by `EDITORIAL-DISCOVERY-006-010-001` on Chapter 6, none of the nine findings concerns Julian's first appearance, and revision under `DEC-018` does not unmake the fact that his register was established there.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-REVISION-001",
  "date": "2026-09-18",
  "prior_state": {
    "authority_through": "DEC-017",
    "chapter_shape_rule": "none; ArcEntry hook text was routinely reproduced as the chapter's final prose line in every delivered chapter from 30 to 46",
    "normal_class_drafting_target": "none; only the 700-1600 Normal_Chapter_Range band",
    "delivered_word_state": {
      "delivered_chapters_with_declared_words": 45,
      "declared_prose_words": 41020,
      "declared_mean": 912,
      "projection_across_128": "approximately 117000 against Final_Targets of 130000-150000"
    },
    "chapter_statuses": {
      "1-29": "approved",
      "30-46": "draft",
      "73": "exploratory",
      "118": "exploratory",
      "124": "exploratory"
    },
    "discovery_movement_gate": "GATE-EDITORIAL-DISCOVERY-MOVEMENT-001 pass, recorded 2026-09-17T04:40:00Z over the pre-DEC-018 prose",
    "julian_first_appearance_review": "valid, carried by EDITORIAL-DISCOVERY-006-010-001 on chapter 6"
  },
  "revised_state": {
    "authority_through": "DEC-018",
    "chapter_shape_rule": "DEC-018 clauses 1-7: no thesis opening, no hook echo, one live question per boundary, reluctant retrospection authorized, contradiction-cuts unspoken, enumerated absence rationed to one per chapter, voice separation carried structurally",
    "human_cost_and_warmth_rule": "DEC-018 clauses 8 and 9: one personal non-abstract cost per lead per movement; per-movement warmth, comfort offered and accepted, and non-professional humor; no lead flatter than the supporting cast",
    "normal_class_drafting_target": "1050-1200 Prose_Words with a planning mean near 1125; outliers keep their declared outlier_purpose and are not inflated",
    "word_budget_arithmetic": {
      "distribution": "110 normal, 10 microchapter, 8 long-outlier",
      "outlier_contribution_mid_band": 19700,
      "total_at_target_floor": 135200,
      "total_at_target_midpoint": 143450,
      "total_at_target_ceiling": 151700,
      "operative_rule": "the normal-class mean must land between roughly 1000 and 1185; 1200 is a per-chapter ceiling for the class and not a target for the mean"
    },
    "chapter_statuses": {
      "1-29": "revised at the moment each file's prose changes; not changed by this wave",
      "30-46": "draft, unchanged",
      "73": "exploratory, unchanged",
      "118": "exploratory, unchanged",
      "124": "exploratory, unchanged"
    },
    "discovery_movement_gate": "GATE-EDITORIAL-DISCOVERY-MOVEMENT-001 retained unedited as a historical record; a new Discovery movement Editorial_Gate must be recorded against the revised prose before any of chapters 1-29 returns to approved",
    "julian_first_appearance_review": "valid and unchanged",
    "preserved_unchanged": [
      "DEC-002 receive-only December apparatus with no transmit stage, and the distinct later temporary bench path",
      "receiver-owned configuration-and-information-load-dependent reconstruction latency, not a constant, transit time, or source-side delay",
      "the content-free handshake and Nia's self-experienced wanting",
      "unresolved causation and the DEC-007 asymmetry with no confirmation, appropriation, or absolution",
      "the three never-revealed Reveal IDs",
      "Mara's chapter 23 first reader release of REVEAL-NIA-SOURCE-CASUALTY with Nia owning the chapter 24 refusal",
      "page nine as architectural capability only",
      "closed motif families with no new MotifEvent and no new LiteralPhraseConstraint",
      "the four-POV limit and the 56/32/33/7 loads",
      "the 29/32/51/16 movement allocation",
      "the prohibition on any POV for a sender, adversary, archive, simulation, model, or group mind",
      "Final_Targets of 128 chapters and 130000-150000 Prose_Words, and BASELINE-FINAL-FRONTIER-PROVISIONAL state approved"
    ]
  },
  "rationale": "The delivered manuscript had become a sequence of closed loops: each chapter states its thesis in its first sentence and restates its ArcEntry hook as its last, so no question survives a chapter boundary. Eight further craft defects travel with that shape, including dissolved dramatic irony in declared contradiction-cut relationships, three viewpoints sharing one syntax, no lead with a family, a meal, a joke, or a touch on the page, no personal cost for the highest-load viewpoint before chapter 55, two abandoned threads in Private_Defense, and a word budget projecting roughly 13000 words below the approved floor. The author directed that all nine findings be fixed and DEC-018 records the rules the fixes are measured against. Revising approved Discovery prose invalidates its approval, so the status and gate consequences are recorded here rather than discovered later.",
  "affected_chapters": [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46
  ],
  "affected_documents": [
    "planning/decisions.md",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/motif-ledger.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "chapters/discovery-part/discovery-part-001-noise-floor.md",
    "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
    "chapters/discovery-part/discovery-part-003-the-failed-check.md",
    "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
    "chapters/discovery-part/discovery-part-005-not-a-message.md",
    "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
    "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
    "chapters/discovery-part/discovery-part-008-provisional-identity.md",
    "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
    "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
    "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md",
    "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
    "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
    "chapters/discovery-part/discovery-part-014-rights-before-names.md",
    "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
    "chapters/discovery-part/discovery-part-016-come-in.md",
    "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
    "chapters/discovery-part/discovery-part-018-clean-silence.md",
    "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
    "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
    "chapters/discovery-part/discovery-part-021-reconstruction.md",
    "chapters/discovery-part/discovery-part-022-fundable.md",
    "chapters/discovery-part/discovery-part-023-the-match-holds.md",
    "chapters/discovery-part/discovery-part-024-not-case-zero.md",
    "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
    "chapters/discovery-part/discovery-part-026-already-outside.md",
    "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
    "chapters/discovery-part/discovery-part-028-named-second.md",
    "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
    "chapters/private-defense-part/private-defense-part-030-something-came-in.md",
    "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md",
    "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md",
    "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md",
    "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md",
    "chapters/private-defense-part/private-defense-part-035-a-private-no.md",
    "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md",
    "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md",
    "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md",
    "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md",
    "chapters/private-defense-part/private-defense-part-040-first-calibration.md",
    "chapters/private-defense-part/private-defense-part-041-two-interpreters.md",
    "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md",
    "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md",
    "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md",
    "chapters/private-defense-part/private-defense-part-045-page-nine.md",
    "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/decisions.md",
      "required_change": "Record DEC-018 as binding with the ten craft clauses, the clause 10 word-budget arithmetic, the narrow canon authorization, the preserved-unchanged list, and the retired alternatives.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-018 - Chapter shape, forward pressure, voice separation, and human cost"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Record the nine review findings with representative prose evidence and one editorial GateResult for the pass with a null checker_exit_status, without editing any earlier finding or gate.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, EDITORIAL-REVISION-001 through EDITORIAL-REVISION-009 and GATE-EDITORIAL-REVISION-PASS-001"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Add the DEC-018 chapter-shape Editorial_Gate criteria, record the clause 10 target band and its arithmetic beside the length-class budget, and confirm no ArcEntry, CrossCut, or Baseline record value changed in this wave.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, DEC-018 chapter-shape controls and DEC-018 clause 10 - the normal-class target inside the band"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Re-budget the estimated_words value of every normal-class ArcEntry into the 1050-1200 clause 10 band, keeping every same-POV run at or under 3600 Prose_Words and every outlier estimate at its declared outlier_purpose.",
      "status": "complete",
      "evidence_ref": "Closed by supersession rather than performance: DEC-021 clause 5 and ARC-CHANGE-LENGTH-GOVERNANCE-001 retire mass normalization as a conflicting formula. No ArcEntry estimated_words value changed; existing estimates remain planning metadata for movement scale and same-POV run safety."
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Set the ArcEntry status of each of chapters 1-29 to revised as that chapter's prose changes, keeping it synchronized with its Chapter_Header.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm that the four Voice_Briefs already specify distinct registers and that DEC-018 clause 7 requires no change to their guidance, and confirm VOICE-JULIAN.first_appearance_review remains valid; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md reviewed with no value change required; all four briefs already specify distinct syntax_rhythm, image_sensory_families, and emotional_distance, and EDITORIAL-REVISION-004 finds the prose is not delivering the existing guidance rather than that the guidance is wrong; VOICE-JULIAN.first_appearance_review remains valid and unedited"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm that the revision creates no MotifEvent, no LiteralPhraseConstraint, and no change to any motif placement, function, representation mode, or phrase scope, and that the closed motif families stay closed; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed with no value change required; every MOT-CHAIN, MOT-COME, MOT-COPPER, MOT-KETTLE, MOT-KNOCK, MOT-RADIUS, MOT-RECORD, MOT-WHOSE, and MOT-YES assignment is unchanged and LPC-DID-I-SAY-YES and LPC-WHOSE-WAS-THAT keep their scope"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that the craft clauses of DEC-018 assert no canon fact, extension, timeline, reveal, or protected wording, and that the supporting canon is recorded separately under ARC-CHANGE-REVISION-002; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, DEC-018 - chapter shape, forward pressure, voice, cost, and warmth, which records the ten clauses as readable craft direction only"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm that the revision changes no POV identity, mapping, knowledge position, moral pressure, plot function, movement coverage, Anchor status, or provisional load; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md, 2026-09-18 amendment: four profiles, one Anchor, and the 56/32/33/7 loads across 29/32/51/16 unchanged"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record the objective reruns required as each revised chapter and batch is delivered, including the Chapter_Local_Gate word-count and status-agreement checks for chapters 43-46.",
      "status": "complete",
      "evidence_ref": "Objective reruns recorded in planning/gate-results.md: Chapters 43-49 chapter-local and batch backfill results, the Chapter 34, 44, 49 and 53 reruns, and the 30-35, 43-49 and 50-55 batch reruns. Chapters 43-46 now pass word-count and status-agreement checks."
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Re-record the Discovery_Part movement Editorial_Gate against the revised chapters 1-29 prose, plus current chapter and batch editorial gates, before any of those chapters returns to approved. GATE-EDITORIAL-DISCOVERY-MOVEMENT-001 and the task 12.7 records are retained unedited as historical.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-001-noise-floor.md",
      "required_change": "Revise chapter 1 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
      "required_change": "Revise chapter 2 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
      "required_change": "Revise chapter 3 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
      "required_change": "Revise chapter 4 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-005-not-a-message.md",
      "required_change": "Revise chapter 5 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
      "required_change": "Revise chapter 6 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
      "required_change": "Revise chapter 7 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
      "required_change": "Revise chapter 8 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
      "required_change": "Revise chapter 9 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
      "required_change": "Revise chapter 10 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md",
      "required_change": "Revise chapter 11 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
      "required_change": "Revise chapter 12 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
      "required_change": "Revise chapter 13 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-014-rights-before-names.md",
      "required_change": "Revise chapter 14 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
      "required_change": "Revise chapter 15 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-016-come-in.md",
      "required_change": "Revise chapter 16 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
      "required_change": "Revise chapter 17 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-018-clean-silence.md",
      "required_change": "Revise chapter 18 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
      "required_change": "Revise chapter 19 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
      "required_change": "Revise chapter 20 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-021-reconstruction.md",
      "required_change": "Revise chapter 21 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-022-fundable.md",
      "required_change": "Revise chapter 22 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
      "required_change": "Revise chapter 23 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-024-not-case-zero.md",
      "required_change": "Revise chapter 24 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
      "required_change": "Revise chapter 25 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-026-already-outside.md",
      "required_change": "Revise chapter 26 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
      "required_change": "Revise chapter 27 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-028-named-second.md",
      "required_change": "Revise chapter 28 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
      "required_change": "Revise chapter 29 against DEC-018 clauses 1-10 and demote the Chapter_Header status from approved to revised in step with its ArcEntry; approval returns only through a re-recorded Discovery movement Editorial_Gate.",
      "status": "pending",
      "evidence_ref": null
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-030-something-came-in.md",
      "required_change": "Revise chapter 30 against DEC-018 clauses 1-10, and develop the exposed-persons list and Ravi Anand's objection under CF-PRIVATE-EXPOSED-PERSONS-LIST; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 30 revised; opens on the running tap, the exposed-persons list is created and contested by Ravi on the page, and the Ruth scene supplies clause 9 warmth. GATE-EDITORIAL-PRIVATE-DEFENSE-030 pass; header and ArcEntry both revised at 1,169 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md",
      "required_change": "Revise chapter 31 against DEC-018 clauses 1-10; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 31 revised; MOT-COPPER-01 keeps its relief-and-measurement function and Nia forces the page to be dated and annotated. GATE-EDITORIAL-PRIVATE-DEFENSE-031 pass; 1,148 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md",
      "required_change": "Revise chapter 32 against DEC-018 clauses 1-10, and remove any explicit statement of the CUT-SEALED-ROOM-AND-A-LIFE contradiction; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 32 revised; the sealed-enclosure refusal is retained and no explicit statement of the CUT-SEALED-ROOM-AND-A-LIFE contradiction remains. GATE-EDITORIAL-PRIVATE-DEFENSE-032 pass; 1,170 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md",
      "required_change": "Revise chapter 33 against DEC-018 clauses 1-10; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 33 revised; the thesis opening and the Hook-echo ending are both gone, and Dalby now extracts a concession and opens the named-individuals inquiry. GATE-EDITORIAL-PRIVATE-DEFENSE-033 pass; 1,171 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md",
      "required_change": "Revise chapter 34 against DEC-018 clauses 1-10, and remove Nia's explicit statement of the CUT-SEALED-ROOM-AND-A-LIFE contradiction; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 34 revised; the spoken contradiction is removed and the cost is paid on the corridor floor, with warmth through the supervisor and Joss. GATE-EDITORIAL-PRIVATE-DEFENSE-034 pass; 1,116 Prose_Words after the voice-separation repair."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-035-a-private-no.md",
      "required_change": "Revise chapter 35 against DEC-018 clauses 1-10, and carry the car at the gate forward under CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY without resolving it inside the chapter's final line; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 35 revised; the car at the gate is carried forward as counted freight rather than resolved in the final line, and Ravi announces his transfer request. GATE-EDITORIAL-PRIVATE-DEFENSE-035 pass; 1,210 Prose_Words, with the ten-word clause 10 overage recorded in EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003 rather than trimmed."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md",
      "required_change": "Revise chapter 36 against DEC-018 clauses 1-10, connect the demonstration room to the Chapter 35 arrival under CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY, and establish the private two-person layer class through Ada and Lena Ferris under CF-PRIVATE-TWO-PERSON-LAYER-CLASS; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 36 revised; the gate visitor book connects the demonstration room to the Chapter 35 arrival, and the Ferris two-person layer class is established with no connection to Safiya. GATE-EDITORIAL-PRIVATE-DEFENSE-036 pass; 1,186 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md",
      "required_change": "Revise chapter 37 against DEC-018 clauses 1-10; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 37 revised; the Hook echo is gone, Ada challenges the observation resolution, and Ravi's single Thursday is expressly not a series. GATE-EDITORIAL-PRIVATE-DEFENSE-037 pass; 1,159 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md",
      "required_change": "Revise chapter 38 against DEC-018 clauses 1-10; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 38 revised; the fire benefit stays bounded, Tomas's argument for recording is left unanswered, and the enrollment clock carries a dated external consequence. GATE-EDITORIAL-PRIVATE-DEFENSE-038 pass; 1,172 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md",
      "required_change": "Revise chapter 39 against DEC-018 clauses 1-10; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 39 revised; the five definitions are accepted without amendment and the interface specification is withheld. GATE-EDITORIAL-PRIVATE-DEFENSE-039 pass; 1,171 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-040-first-calibration.md",
      "required_change": "Revise chapter 40 against DEC-018 clauses 1-10, and remove any explicit statement of the CUT-CALIBRATION-AND-THE-UNCALIBRATED contradiction; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 40 revised; no explicit statement of the CUT-CALIBRATION-AND-THE-UNCALIBRATED contradiction remains, and Ravi's handwritten transfer delivers the Anchor cost. GATE-EDITORIAL-PRIVATE-DEFENSE-040 pass; 1,187 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md",
      "required_change": "Revise chapter 41 against DEC-018 clauses 1-10, and carry the private two-person layer class through the Ferris pair's working practice under CF-PRIVATE-TWO-PERSON-LAYER-CLASS; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 41 revised; the Ferris pair carry the two-person layer class as paid professional practice under CF-PRIVATE-TWO-PERSON-LAYER-CLASS. GATE-EDITORIAL-PRIVATE-DEFENSE-041 pass; 1,054 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md",
      "required_change": "Revise chapter 42 against DEC-018 clauses 1-10, and remove Nia's explicit statement of the CUT-CALIBRATION-AND-THE-UNCALIBRATED contradiction; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 42 revised; the explicit contradiction statement is gone, the single enumerated absence is the chapter's own subject, and the irony moves onto other people at the close. GATE-EDITORIAL-PRIVATE-DEFENSE-042 pass; 1,057 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md",
      "required_change": "Revise chapter 43 against DEC-018 clauses 1-10 and correct the declared words value to the actual Prose_Body token count; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 43 revised and its declared count corrected; Dalby's ambulance argument stands unanswered. GATE-EDITORIAL-PRIVATE-DEFENSE-043 pass; 1,692 Prose_Words as a declared long outlier."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md",
      "required_change": "Revise chapter 44 against DEC-018 clauses 1-10, remove any explicit statement of the CUT-CONSTRAINABLE-CLAUSE contradiction, and correct the declared words value to the actual Prose_Body token count; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 44 revised and its declared count corrected; no explicit statement of the CUT-CONSTRAINABLE-CLAUSE contradiction remains and the reserved reader-instruction formula was removed from Julian's narration. GATE-EDITORIAL-PRIVATE-DEFENSE-044 pass; 1,052 Prose_Words."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-045-page-nine.md",
      "required_change": "Revise chapter 45 against DEC-018 clauses 1-10, remove any explicit statement of the CUT-CONSTRAINABLE-CLAUSE contradiction, keep the declared microchapter compression, and correct the declared words value to the actual Prose_Body token count; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 45 revised and its declared count corrected; the declared microchapter compression is retained at 431 Prose_Words and GATE-EDITORIAL-PRIVATE-DEFENSE-045 passes. Reasoned deviation from the literal obligation: Mara's recognition of the gap between the initialed clause and the specification is retained rather than removed, because she is holding both documents and suppressing her reading would be the artificial withholding Requirements 2.13 and 2.14 forbid. The cut's irony belongs to Julian and is preserved, since the chapter ends on him stopping writing. Recorded in EDITORIAL-PRIVATE-DEFENSE-LOCAL-045 and EDITORIAL-REVISION-003-FOLLOWUP-001."
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md",
      "required_change": "Revise chapter 46 against DEC-018 clauses 1-10 and correct the declared words value to the actual Prose_Body token count; set the Chapter_Header status to revised in step with its ArcEntry.",
      "status": "complete",
      "evidence_ref": "Chapter 46 revised and its declared count corrected; the Hook-echo ending is replaced by nodes already in manufacture while the parties agree about permission. GATE-EDITORIAL-PRIVATE-DEFENSE-046 pass; 1,054 Prose_Words."
    }
  ],
  "approval": {
    "approved_by": "Author via explicit revision-pass direction after the commissioned craft review",
    "approved_at": "2026-09-18T08:00:00Z",
    "approval_record": "Author instruction: fix all nine findings from the craft review of delivered Chapters 1-46 plus calibration Chapters 73, 118, and 124; canon may be added where the fix requires it."
  },
  "status": "in-progress",
  "completed_at": null
}
```

## `ARC-CHANGE-REVISION-002` — `DEC-018` supporting canon

The canon additions the revision pass needs, recorded separately from the prose authorization so that the continuity change is auditable on its own. All of them sit inside the narrow canon authorization in `DEC-018`; none is Canon Lyric, and none creates a POV, a Voice Brief, a chapter, a `Reveal`, a `MotifEvent`, or a `LiteralPhraseConstraint`.

Two boundaries are worth restating outside the record, because they are the ones a later wave could break by accident. The technician's single uncharacterized report is **not** the first reported pattern of arrivals in strangers, which remains Chapter 62, and it resolves nothing about provenance or the origin of Nia's wanting. And the private two-person language layer class is established through Ada and Lena Ferris, whose own layer is intact and who are connected to Safiya Mir by nothing at all; `DEC-003` is unweakened, `heritage_base: unspecified_by_author` stays exact, and no corpus of Safiya's layer exists anywhere.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-REVISION-002",
  "date": "2026-09-18",
  "prior_state": {
    "character_id_registry": "CHAR-001 through CHAR-014; four POVProfile records and ten non-viewpoint character-name extensions",
    "EXT-CHAR-RAVI-NAME": {
      "character_id": "CHAR-011",
      "selected_name": "Ravi",
      "surname": "none selected",
      "role": "independent December timing and control witness"
    },
    "exposed_persons_list": "established in chapter 30 prose with three names and the technician's objection; no canon record, no status, and no development anywhere after chapter 30",
    "technician_private_report": "does not exist",
    "mara_private_defense_personal_cost": "none; all Mara costs scheduled at chapters 55, 106, and 112",
    "car_at_the_gate": "unidentified at the end of chapter 35; chapter 36 opens inside a Consortium demonstration room and never refers to the arrival",
    "two_person_language_layer": "appears only as Safiya's loss in the Coda; not established anywhere as a class of thing that can be lost",
    "nia_non_professional_relationships": "none on the page",
    "mara_non_professional_relationships": "none on the page",
    "TL-PRIVATE-COPPER": {
      "participants": ["CHAR-001", "CHAR-002", "CHAR-003"],
      "fact_refs": ["CF-PRIVATE-COPPER-BOUNDARY", "CF-CONSENT-SOVEREIGNTY"]
    },
    "civilian_loss_before_118": "no planning obligation; the class first appears in Safiya's chapter 118 account"
  },
  "revised_state": {
    "character_id_registry": "CHAR-001 through CHAR-016; four POVProfile records unchanged and twelve non-viewpoint character-name extensions",
    "EXT-CHAR-RAVI-NAME": {
      "character_id": "CHAR-011",
      "selected_name": "Ravi Anand",
      "surname": "Anand, added by DEC-018",
      "role": "independent December timing and control witness and copper-room technician"
    },
    "new_canon_facts": [
      "CF-PRIVATE-EXPOSED-PERSONS-LIST",
      "CF-PRIVATE-TECHNICIAN-REPORT",
      "CF-PRIVATE-TECHNICIAN-REASSIGNMENT",
      "CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY",
      "CF-PRIVATE-TWO-PERSON-LAYER-CLASS"
    ],
    "new_novel_extensions": [
      "EXT-CHAR-JOSS-NAME",
      "EXT-CHAR-RUTH-NAME",
      "EXT-REL-NIA-JOSS",
      "EXT-REL-MARA-RUTH"
    ],
    "TL-PRIVATE-COPPER": {
      "participants": ["CHAR-001", "CHAR-002", "CHAR-003", "CHAR-011"],
      "fact_refs": ["CF-PRIVATE-COPPER-BOUNDARY", "CF-CONSENT-SOVEREIGNTY", "CF-PRIVATE-EXPOSED-PERSONS-LIST", "CF-PRIVATE-TECHNICIAN-REPORT", "CF-PRIVATE-TECHNICIAN-REASSIGNMENT", "CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY"]
    },
    "civilian_loss_before_118": "planning obligation recorded in the Mindwars and Coda movement sections of arc-outline.md: the class of uncounted private civilian loss must be vivid inside chapters 109-114, without Safiya's POV, without entering her home, without naming or foreshadowing her loss, and without pre-empting REVEAL-SAFIYA-TUESDAY-LOSS",
    "preserved_unchanged": [
      "REVEAL-SAFIYA-TUESDAY-LOSS releases at 118 inside its unchanged 118-119 window with POV-SAFIYA as owner",
      "chapter 62 remains the first reported pattern of arrivals in strangers",
      "DEC-003, heritage_base unspecified_by_author, and the absence of any surviving corpus of Safiya's layer",
      "no connection of any kind between Ada or Lena Ferris and Safiya Mir",
      "the four POVProfile records, the single Anchor, and the 56/32/33/7 loads",
      "the chapter 55 loss of instruments and the chapter 112 shutdown as separate later Mara costs",
      "all nine Reveal records, all motif assignments, and both literal phrase constraints"
    ]
  },
  "rationale": "Three of the nine review findings cannot be fixed in prose alone. The dropped-thread finding needs the exposed-persons list to have a defined status and the car at the gate to have an owner. The Mara-pays-nothing finding needs a personal, non-abstract cost available inside Private_Defense. The warmth finding needs at least one non-professional relationship for Nia and one for Mara. The Safiya-arrives-late finding needs the class of private two-person layer, and the class of uncounted civilian loss, established before chapter 118 without moving her or entering her home. The author explicitly authorized canon additions for exactly this purpose, and DEC-018 carries the narrow authorization these records cite.",
  "affected_chapters": [30, 32, 35, 36, 41, 43, 109, 110, 111, 112, 113, 114],
  "affected_documents": [
    "planning/canon-bible.md",
    "planning/decisions.md",
    "planning/arc-outline.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/motif-ledger.md",
    "planning/editorial-log.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/decisions.md",
      "required_change": "Record the narrow canon authorization inside DEC-018, enumerating exactly which additions it permits and what it does not create.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-018 section Narrow canon authorization"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Add the five CanonFact records with authority_basis author-decision and source_location DEC-018, add the four NovelExtension records declaring CHAR-015 and CHAR-016 and the two relationships, amend EXT-CHAR-RAVI-NAME to carry the surname without changing CHAR-011, add CHAR-011 and the new fact_refs to TL-PRIVATE-COPPER, and update the names-and-entities quick reference to twelve supporting names.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, DEC-018 supporting canon section, amended EXT-CHAR-RAVI-NAME, amended TL-PRIVATE-COPPER, and the Names and entities quick reference"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Record the Chapters 109-114 uncounted-civilian-loss obligation where the Mindwars and Coda drafting tasks will read it, with the no-Safiya-POV, no-home, no-foreshadowing, and no-pre-emption boundaries stated.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, Mindwars_Part and Aftermath_Coda movement invariants, DEC-018 planning obligation bullets"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Restate CHAR-015 and CHAR-016 and the CHAR-011 surname, confirm no POVProfile record or relationships array changed, and confirm four profiles, one Anchor, and the 56/32/33/7 loads.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md, 2026-09-18 amendment and the non-viewpoint supporting participants and witnesses section"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm that no new POV, Voice_Brief, or Coda_Turn is created, that exactly four briefs remain, and that Safiya's describe-never-quote handling and unspecified heritage base are untouched by the two-person-layer class; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md reviewed with no value change required; exactly four VoiceBrief records remain, the twelve non-viewpoint Character IDs create no VoiceBrief obligation, and VOICE-SAFIYA keeps describe-never-quote with heritage_base unspecified_by_author"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm that none of the five CanonFacts or four extensions creates a MotifEvent or LiteralPhraseConstraint, and that the closed families and both existing constraints are unchanged; record that conclusion.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed with no value change required; none of the five new CanonFacts carries protected_wording, no new phrase enters Chapter File literal scan scope, and the closed motif families stay closed"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Point the dropped-thread, Mara-cost, warmth, and Safiya-preparation findings at the specific canon records that make each fix available.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, requested_action of EDITORIAL-REVISION-005, EDITORIAL-REVISION-006, EDITORIAL-REVISION-007, and EDITORIAL-REVISION-008"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that no Reveal record changes: REVEAL-SAFIYA-TUESDAY-LOSS keeps owner POV-SAFIYA, release 118, and window 118-119; the three never-revealed reveals stay unresolved with null owner, null release, and null window.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, Reveal Ledger reviewed with no value change required; all nine Reveal records unchanged"
    }
  ],
  "approval": {
    "approved_by": "Author via explicit authorization of canon additions for the revision pass",
    "approved_at": "2026-09-18T08:00:00Z",
    "approval_record": "Author instruction: we can always add to canon; add what the nine findings need to be fixable, without creating a new POV, Voice Brief, or chapter."
  },
  "status": "in-progress",
  "completed_at": null
}
```

### Why both records are `in-progress` rather than `complete`

Every planning and canon obligation above is `complete` with an evidence reference. The open obligations are all Chapter_File work and the objective and editorial reruns that follow it: revising Chapters 1–29 and 30–46, re-budgeting `estimated_words`, demoting Chapters 1–29 to `revised` as each is touched, correcting the declared `words` of Chapters 43–46, and re-recording the Discovery movement Editorial_Gate. Under the status rules above, partial synchronization is never approval, so neither record may reach `complete` and no revised chapter may return to `approved` until those obligations carry evidence.

## `ARC-CHANGE-REVISION-003` — Chapter 52 horizon synchronization and third-party deposit authority

Task 5.6 moved `REVEAL-CASUALTY-CONSEQUENCE` from Chapter 53 to Chapter 52 so the release chapter would match its owning `POV-NIA`, and the Arc Outline recorded the remaining beat-structure question as a residual matter for human decision rather than record repair. The Chapter 52 `record_horizon` was never synchronized to that move: it still said Nia knew only that the logs existed and had not been told what the timestamps established, while the reveal records require her to own and release the documentary exoneration in her own chapter. Drafting Chapter 52 made the contradiction operative rather than theoretical, because no chapter can both release the finding and be barred from knowing it.

The same review found a second problem that the checker cannot see. Chapter 51 establishes that a depositor may deposit only their own account, and Chapter 54 enforces that rule against Mara by refusing Ravi Anand's notebook. Chapter 52 as first drafted let Nia deposit and set release conditions on the county's dispatch review, which is a third party's record containing a dead man's clinical details. That is the precise act the Trust exists to refuse, so the institution contradicted itself at the point its credibility depends on.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-REVISION-003",
  "date": "2026-09-12",
  "prior_state": {
    "ArcEntry_52_record_horizon_knowledge_limit": "Nia composes this as one of the first rolling witness deposits accepted after formation and knows only her own account, her own conditions, and that the logs exist; she has not been told what the timestamps establish, and she still refuses both accounts of where her certainty came from.",
    "dispatch_review_deposit_authority": "Chapter 52 prose had Nia deposit the county dispatch review herself, under one shared reference with her sealed account, on her own release conditions",
    "chapter_52_condition_two_scope": "unqualified trigger on any published account, official summary, history, submission, or product document identifying the incident as mental intrusion, with no definition of published and no identification threshold",
    "chapter_53_holding_description": "one sealed envelope and one dispatch review under the same reference, single depositor",
    "chapter_53_local_heading_constraint": "a local heading appears in no other index, matches no other search, and is invisible to every future researcher",
    "chapter_54_checksum_verification": "archivist compared eleven of sixty-four characters and recorded content corroboration described as better than a date"
  },
  "revised_state": {
    "ArcEntry_52_record_horizon_knowledge_limit": "Nia composes this as one of the first rolling witness deposits accepted after formation and owns the documentary release: nobody explains the closed review to her, so she reads it herself and establishes that her routing did not cause the death and that no available routing would have prevented it. She knows the review is silent on where her certainty came from, that she cannot compel release of the county's certified copy, and she still refuses both origin accounts.",
    "dispatch_review_deposit_authority": "the archivist refuses the review from Nia because it is a third party's record; the county records office issues a certified copy direct to the Trust under its own authority as a separate accession with a separate reference, deposited and conditioned by the county",
    "chapter_52_condition_four": "negative control only: Nia's account is not released unless the county's certified copy is released beside it, and she cannot compel the county's copy to open",
    "chapter_52_condition_two_scope": "published or laid before a public body, and identified as hers by name or by particulars amounting to her name; Nia states on the page that Chapter 47's internally circulated Case B binder is deliberately outside the trigger",
    "chapter_53_holding_description": "two accessions with two depositors, bound by her condition rather than by the catalogue",
    "chapter_53_local_heading_constraint": "only scheme authority headings are exported in the quarterly accessions return that county and national listings harvest; local headings and scope notes remain in the Trust's own catalogue and are reachable only by direct enquiry",
    "chapter_54_checksum_verification": "archivist runs the checksum herself and matches all sixty-four characters in blocks of eight, then records that content corroboration is not a date"
  },
  "rationale": "Two findings could not be fixed in prose alone. The Chapter 52 horizon contradicted the authoritative reveal ownership that task 5.6 established, so the stale planning value had to move rather than the prose. The third-party deposit problem required an actual lawful mechanism, because the Trust cannot enforce depositor ownership against Mara in Chapter 54 while suspending it for Nia in Chapter 52 without losing the moral credibility the whole record thread rests on. The scoped release trigger, the two-accession catalogue, the realistic index-export constraint, and the corrected checksum verification are the synchronization consequences of those two decisions. No reveal owner, release chapter, payoff window, motif assignment, cross-cut, timeline, or origin-account status changed, and the dispatch review still sits beside Nia's account as the Arc Outline requires.",
  "affected_chapters": [52, 53, 54],
  "affected_documents": [
    "planning/arc-outline.md",
    "planning/arc-changes.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md",
    "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md",
    "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/arc-outline.md",
      "required_change": "Replace the stale Chapter 52 record_horizon knowledge_limit with one that matches Nia's authoritative ownership and release of the documentary exoneration, while preserving her silence on authorship and her refusal of both origin accounts.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, ArcEntry chapter 52 record_horizon.knowledge_limit"
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md",
      "required_change": "Have the archivist refuse the third-party review, route the certified copy through the county's own authority as a separate accession, reduce condition four to negative control, scope condition two so the Chapter 47 binder is deliberately excluded, and replace the procedural closing beat.",
      "status": "complete",
      "evidence_ref": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md, condition two scope passage, condition four, the two-conversation passage, and the closing three paragraphs"
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md",
      "required_change": "Describe two accessions and two depositors, remove the duplicated Chapter 52 timestamp proof and repeated review-field enumeration, and replace the absolute invisible-local-heading claim with the authority-heading export constraint.",
      "status": "complete",
      "evidence_ref": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md, opening two paragraphs, the compressed review paragraph, and the local-heading passage"
    },
    {
      "document": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md",
      "required_change": "Replace the partial eleven-character checksum comparison with full verification and drop the claim that content corroboration is better than a date.",
      "status": "complete",
      "evidence_ref": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md, procedure-sheet paragraph"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that no CanonFact, NovelExtension, TimelineEntry, or Reveal record requires a value change: CF-CASE-ZERO-LOGS remains Nia's attributed first-person documentary account, REVEAL-CASUALTY-CONSEQUENCE keeps POV-NIA ownership with release 52 and window 50-55, EXT-TRUST-GOVERNANCE already requires witness-controlled conditions and provenance rather than truth, and TL-PRIVATE-RECORD-DEPOSITS keeps its participants and uncertainty notes.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md reviewed with no value change required; CF-CASE-ZERO-LOGS, REVEAL-CASUALTY-CONSEQUENCE, EXT-TRUST-GOVERNANCE, EXT-APRIL-RECORD-ALTERATION, and TL-PRIVATE-RECORD-DEPOSITS all already permit the revised state, and the county's own deposit authority is an ordinary institutional mechanism that creates no new canon record"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record this change as a typed ArcChange carrying exact prior and revised state, every affected document, an approval object, and completion only once every other obligation holds evidence.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, the ARC-CHANGE-REVISION-003 record and its closing note on what the change deliberately does not do"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm that MOT-RECORD-01 remains assigned only to Chapter 51 and that no new literal phrase enters Chapter File scan scope.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed with no value change required; MOT-RECORD-01 stays at Chapter 51 as the private insistence event, and Chapters 52-54 carry empty motif_events"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Record the editorial findings that produced this change and the craft findings resolved in the same pass.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, EDITORIAL-PRIVATE-DEFENSE-050-055 findings"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record the six Chapter_Local_Gate results and the Chapters 50-55 drafting-batch result for task 13.4 after the repair pass.",
      "status": "complete",
      "evidence_ref": "planning/gate-results.md, task 13.4 objective drafting gates section"
    }
  ],
  "approval": {
    "approved_by": "Author instruction during the Chapters 50-55 review",
    "approved_at": "2026-09-12T00:00:00Z",
    "approval_record": "Author instruction: please make the repair pass, following the reviewed findings for Chapters 51-53 and the technical correction in Chapter 54."
  },
  "status": "complete",
  "completed_at": "2026-09-12T00:00:00Z"
}
```

### What this change deliberately does not do

It does not move a reveal, an owner, a release chapter, or a payoff window. It does not resolve either origin account: Nia still refuses both, Julian still enters the adversary heading as an inference he records as an inference, and Mara's conviction remains unvoiced here. It does not make the Trust an adjudicator; the county's certified copy is deposited on the county's terms precisely so that no custodian and no witness can be shown controlling another party's record. And it does not convert Nia's release trigger into a device that fires offstage: she states the limit herself, names what it excludes, and accepts the cost.
## `ARC-CHANGE-DEC-020-ANTI-FORMULA-001` — Contextual propulsion without a batch recipe

The author approved softening `DEC-020` after identifying that its fixed remedies could create the same detectable pattern they were meant to prevent. The diagnosis remains binding; future prose is judged for cumulative propulsion, variety, consequence, and dramatic change without requiring each batch to display a prescribed set of devices.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-DEC-020-ANTI-FORMULA-001",
  "date": "2026-09-13",
  "prior_state": {
    "DEC-020_clause_1": "no more than two deliberation-deadline endings per drafting batch",
    "DEC-020_clause_2": "no three consecutive endings of one listed kind and a closed list treated as the legitimate ending kinds",
    "DEC-020_clause_3": "at least one interrupted cut in every drafting batch of four or more chapters",
    "DEC-020_clause_4": "at least one materially shorter chapter in every drafting batch of five or more chapters",
    "DEC-020_clause_7": "at least one scene outside an institutional interior in every drafting batch",
    "DEC-020_clause_8": "no three consecutive document, drafting, or deliberation chapters",
    "Requirement_15_9": "fixed occurrence, adjacency, ending-kind, length, and setting thresholds decide the batch finding",
    "task_application": "tasks 13.5, 13.6, and 15 operationalize the thresholds as a repeated batch checklist"
  },
  "revised_state": {
    "DEC-020_clauses_1_through_4_7_8": "the diagnosis and qualitative principles stand; fixed occurrence and adjacency thresholds are withdrawn as acceptance conditions",
    "ending_kinds": "illustrative rather than exhaustive or rotational",
    "interrupted_cuts_short_chapters_and_setting_changes": "available when dramatically earned and never mandatory tokens",
    "editorial_scale": "representative prose judged contextually across batch, movement, and manuscript without a numeric craft score",
    "Requirement_15_9": "propulsion, variety, accumulation, and material state change are judged without a fixed count, adjacency limit, rotation, length quota, or setting quota",
    "task_application": "tasks 13.5, 13.6, and 15 require anti-formula judgment rather than one of each technique"
  },
  "rationale": "The author explicitly rejected a rigid system and approved slight irregularity rather than a visible pattern. Mandatory interruption, microchapter, location, and ending slots would make future batches advertise an artificial construction. The amendment preserves consequence-bearing propulsion, meaningful change, bodily stakes, adversary agency, honest narration, and human review of accumulating prose tics while allowing the story to choose the strongest truthful shape.",
  "affected_chapters": [56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128],
  "affected_documents": [
    "planning/decisions.md",
    "planning/arc-changes.md",
    "planning/editorial-log.md",
    ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    ".kiro/specs/The-Final-Frontier-novel/tasks.md",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/gate-results.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/decisions.md",
      "required_change": "Amend DEC-020 without erasing its historical diagnosis; withdraw the fixed thresholds in clauses 1–4, 7, and 8 and state the contextual anti-formula application.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-020 amendment note dated 2026-09-13"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
      "required_change": "Replace Requirement 15.9's batch quotas with evidence-bearing contextual review and preserve Requirements 15.10 through 15.12 unchanged.",
      "status": "complete",
      "evidence_ref": ".kiro/specs/The-Final-Frontier-novel/requirements.md, Requirement 15.9"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/tasks.md",
      "required_change": "Replace quota instructions in tasks 13.5, 13.6, and parent task 15 with anti-formula drafting and editorial guidance without changing task state.",
      "status": "complete",
      "evidence_ref": ".kiro/specs/The-Final-Frontier-novel/tasks.md, tasks 13.5, 13.6, and 15"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Append a prospective application note that preserves the historical findings and makes clear that their old counts no longer decide future pass or revision findings.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, Prospective application after the DEC-020 anti-formula amendment"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record the author-approved amendment with exact prior and revised state, full future chapter scope, synchronization evidence, and completion metadata.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, ARC-CHANGE-DEC-020-ANTI-FORMULA-001"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Confirm that no ArcEntry purpose, hook, cross-cut, chronology, reveal, motif, POV, length class, or status changes solely because batch quotas were withdrawn.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md reviewed; no DEC-020 quota is copied into an ArcEntry and no ArcEntry value changes"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that the amendment asserts no new CanonFact, NovelExtension, TimelineEntry, Reveal, mode rule, or evidence rule.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md reviewed; no DEC-020 quota copy or canon value requires change"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm that no motif placement, function, representation mode, or literal phrase scope changes.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed; no value change required"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm that no POV identity, knowledge position, dramatic function, movement coverage, or load changes.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md reviewed; no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm that the existing distinct registers remain controlling and that anti-formula application changes no voice value.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md reviewed; no value change required"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Confirm that no completed objective or editorial GateResult claims DEC-020 quota compliance and that no objective rerun is required solely for this human craft amendment.",
      "status": "complete",
      "evidence_ref": "planning/gate-results.md reviewed; no DEC-020 or Requirement 15.9 GateResult exists and checker metadata is unchanged"
    }
  ],
  "approval": {
    "approved_by": "Author instruction in Kiro session",
    "approved_at": "2026-09-13T17:23:01Z",
    "approval_record": "Author instruction: 'I definitely dont want a rigid system. Soften DEC-020 for sure.'"
  },
  "status": "complete",
  "completed_at": "2026-09-13T17:23:01Z"
}
```

### What this change deliberately does not do

It does not reduce the obligation to create suspense, consequence, human cost, bodily stakes, active institutional counterforce, distinct voices, or chapters that materially change the situation. It does not authorize random events, fake cliffhangers, concealed narrator-held facts, spectacle, or imitation. It changes the editorial question from whether a batch filled its assigned slots to whether the prose moves, surprises, and varies without exposing a recipe.
## `ARC-CHANGE-REVISION-004` — Chapter 25–26 knowledge-horizon synchronization

The direct reread requested before further drafting found that Chapter 25 told Julian the verified identity and temporary bench path even though the approved Chapter 26 horizon and binding reveal boundary require him not to know either until Chapter 46. The repair changes the route and audience of Mara's factual disclosure, not what she knows, what the reader knows, or what the bench act did.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-REVISION-004",
  "date": "2026-09-13",
  "prior_state": {
    "chapter_25_disclosure": "Mara directly told Julian the verified source identity and unauthorized temporary-path transmission, then amended a compliance response circulated through the legal matter",
    "chapter_26_horizon": "Julian states that he knows neither the source identity nor any later path and his file ends at passive addressability",
    "chapter_26_hook_use": "the ArcEntry Hook was repeated nearly verbatim inside the body after already being performed by the opening inquiries",
    "compression_question": "EDITORIAL-PROPULSION-002 left percentage compression or redistribution of Chapters 15, 22, and 26 open under a fixed adjacency remedy"
  },
  "revised_state": {
    "chapter_25_disclosure": "Mara records the unauthorized act in a restricted hardware-safety deviation under the temporary driver's asset number, excludes source identity, marks chair review required, and creates no automatic legal-file alert",
    "chapter_26_horizon": "Julian truthfully remains ignorant of Nia and the later path; the receive-only audit remains as a first-person knowledge boundary and dramatic irony",
    "chapter_26_hook_use": "the near-verbatim body echo is removed while the opening and forced national briefing continue to perform the Hook",
    "compression_question": "a continuous reread rejects percentage compression; the named chapters are nonconsecutive and perform distinct state changes, so EDITORIAL-PROPULSION-002 resolves to a follow-up pass"
  },
  "rationale": "The prior seam asked the reader to accept mutually exclusive knowledge states. Synchronizing Chapter 25 to the already approved horizon preserves the stronger Chapter 26 irony and the delayed Chapter 46 reveal. Retaining Chapter 26's audit sentence is deliberate: its meaning is not hardware recap but the boundary between what Julian verified and what institutions are already pricing. No percentage cut is justified by the prose, and amended DEC-020 rejects arithmetic as a substitute for literary judgment.",
  "affected_chapters": [25, 26],
  "affected_documents": [
    "planning/arc-changes.md",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/decisions.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
    "chapters/discovery-part/discovery-part-026-already-outside.md"
  ],
  "synchronization_obligations": [
    {
      "document": "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
      "required_change": "Replace the direct Julian disclosure and broad compliance amendment with an honest restricted hardware-safety deviation that preserves the approved knowledge boundary; update the declared word count.",
      "status": "complete",
      "evidence_ref": "chapter 25, hardware-safety deviation and manual related-matter routing passages; Chapter Header words 1153"
    },
    {
      "document": "chapters/discovery-part/discovery-part-026-already-outside.md",
      "required_change": "Retain the receive-only knowledge boundary, remove the near-verbatim ArcEntry Hook echo from the body, preserve the forced-briefing ending, and update the declared word count.",
      "status": "complete",
      "evidence_ref": "chapter 26, receive-only audit, passive-addressability boundary, and national-briefing close; Chapter Header words 1196"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Confirm Chapter 25's purpose and Chapter 26's purpose, Hook, timeline, POV, status, and record horizon already describe the revised state and require no value change.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, ArcEntries 25 and 26 reviewed with no value change required"
    },
    {
      "document": "planning/decisions.md",
      "required_change": "Preserve the binding rule that Julian does not know the temporary bench path until Chapter 46 and record no decision change.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-019 Discovery compressed-clock finding and Chapter 46 knowledge boundary"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm no TimelineEntry, mode classification, participant, Reveal, or evidence rule changes; only the audience of one institutional record changes.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md reviewed with no value change required"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm Chapters 25 and 26 retain empty motif assignments and no literal phrase scope changes.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed with no value change required"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm Mara and Julian retain their existing identities, knowledge functions, and chapter loads.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm the revised passages deliver the existing Mara and Julian registers without changing voice guidance.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md reviewed with no value change required"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Resolve EDITORIAL-PROPULSION-002 through a full-scope follow-up finding and record current chapter-level continuity, voice, economy, and Hook passes for Chapters 25 and 26.",
      "status": "complete",
      "evidence_ref": "planning/editorial-log.md, EDITORIAL-PROPULSION-002-FOLLOWUP-001 and EDITORIAL-DISCOVERY-025/026-HORIZON-RERUN-001"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record clean current Chapter_Local_Gates for Chapters 25 and 26 and clean reruns of both affected Discovery drafting batches.",
      "status": "complete",
      "evidence_ref": "planning/gate-results.md, Chapter 25-26 knowledge-horizon repair objective reruns"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record the repair, no-change impact conclusions, author approval, and completion evidence in one typed ArcChange.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, ARC-CHANGE-REVISION-004"
    }
  ],
  "approval": {
    "approved_by": "Author instruction in Kiro session",
    "approved_at": "2026-09-13T17:23:01Z",
    "approval_record": "Author instruction to use GPT-5.6 judgment regarding the proposed Chapter 26 cut, Chapter 15/26 compression, and proceeding to Chapter 56."
  },
  "status": "complete",
  "completed_at": "2026-09-13T17:26:29Z"
}
```

### What this change deliberately does not do

It does not change the bench event, the unresolved origin accounts, Mara's belief, Nia's refusal, Julian's later Chapter 46 knowledge, any Reveal, or any ArcEntry. It does not compress Chapter 15, Chapter 22, or Chapter 26. The factual bench record remains available to its restricted safety audience; the reader loses nothing, and only the contradictory premature disclosure to Julian is removed.
## `ARC-CHANGE-PRIVATE-PROTOCOL-001` — Lawful calibration-room access and blocked stale-consent attempt

The pre-draft audit of Chapters 56–61 found two contradictions that prose could not safely improvise around. Chapter 55 removed Mara's array-room access without naming a lawful replacement source of equipment, space, or authority. The planned Chapter 57 beat also described an unconsented semantic `PAIR` contribution, which the four-mode taxonomy forbids. This change establishes the narrow retained asset path and makes the failed session a blocked attempt rather than an impossible fifth mode.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-PRIVATE-PROTOCOL-001",
  "date": "2026-09-13",
  "prior_state": {
    "chapter_56_asset_source": "no post-transfer owner, room booking, or equipment authority named after Chapter 55 removed the array room, source, probe, array time, anechoic hours, and badge access",
    "chapter_57_event": "a stale and overbroad consent state allowed a semantic contribution to cross without current recipient authorization",
    "TL-PRIVATE-PROTOCOL_mode": "PAIR for the whole interval despite the planned unconsented semantic crossing",
    "chapter_58_evidence": "metadata could prove closure timing but not what crossed",
    "chapter_59_hook": "the channel offered a sentence it was not sure of, implying semantic guessing",
    "task_13_5_motif_reference": "listed MOT-KNOCK-01 inside Chapters 56-61 despite its authoritative assignment to Chapter 73"
  },
  "revised_state": {
    "chapter_56_asset_source": "Northline research operations retains the calibration room, PAIR console, and contact bands outside the Emergency Preparedness transfer and grants written time-bounded room-and-equipment bookings; Mara's array badge and lost measurement assets remain unavailable",
    "chapter_57_event": "an older and broader session state accepts Mara's send request after Nia's current authorization has lapsed, but an independent live-consent gate rejects the request before neural transport",
    "TL-PRIVATE-PROTOCOL_mode": "PAIR describes successful and repaired sessions; the blocked failed attempt produces no neural communication event and therefore creates no second mode",
    "chapter_58_evidence": "metadata proves stale-state acceptance, live-consent rejection, and zero transport but cannot reconstruct Mara's intended contribution",
    "chapter_59_hook": "an incomplete integrity flag replaces any guessed sentence and ordinary speech supplies the fallback",
    "task_13_5_motif_reference": "MOT-COME-02 remains in Chapter 61 and MOT-KNOCK-01 is expressly preserved at Chapter 73"
  },
  "rationale": "The retained calibration console can test PAIR transport behavior without restoring the instruments Mara lost or energizing the transferred array, so Chapter 55 keeps its full cost and the two-operator rule is not evaded. Current mutual consent is constitutive of semantic PAIR, not an optional software label; an unconsented semantic contribution would contradict Requirements 14.3, 14.4, and 14.10. A blocked send request still fails ethically because the system solicited and accepted an act under stale authority, while the independent live gate demonstrates the exact defense the repaired protocol must retain. No new mode, participant, POV, sender, or provenance claim is created.",
  "affected_chapters": [56, 57, 58, 59, 60, 61],
  "affected_documents": [
    "planning/arc-changes.md",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    ".kiro/specs/The-Final-Frontier-novel/tasks.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/arc-outline.md",
      "required_change": "Revise Chapter 57 and 58 purposes, Hooks, horizons, and both failure Cross Cuts to describe stale-state acceptance followed by live-consent rejection and zero transport; revise Chapter 59's Hook to forbid semantic guessing.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, ArcEntries 57-59 and CUT-PROTOCOL-AND-THE-STALE-STATE / CUT-FAILURE-WITHOUT-CONTENT"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Name the retained calibration-room assets and booking authority, preserve the transferred array exclusion, and clarify that the blocked stale-state attempt creates no neural event or second mode while successful and repaired sessions remain PAIR.",
      "status": "complete",
      "evidence_ref": "planning/canon-bible.md, TL-PRIVATE-PROTOCOL relative_chronology, location, uncertainty_notes, and technical_state.evidence_scope"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/tasks.md",
      "required_change": "Correct task 13.5 so it does not assign MOT-KNOCK-01 to Chapters 56-61 and explicitly preserves that motif at Chapter 73.",
      "status": "complete",
      "evidence_ref": ".kiro/specs/The-Final-Frontier-novel/tasks.md, task 13.5"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm MOT-COME-02 remains assigned only to Chapter 61 and MOT-KNOCK-01 only to Chapter 73, with no motif value change.",
      "status": "complete",
      "evidence_ref": "planning/motif-ledger.md reviewed; authoritative chapter assignment table unchanged"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
      "required_change": "Confirm Requirements 14.3, 14.4, 14.10 through 14.12, and 15.6 already require the revised consent and evidence boundary and need no text change.",
      "status": "complete",
      "evidence_ref": ".kiro/specs/The-Final-Frontier-novel/requirements.md reviewed with no value change required"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm the Nia/Mara/Julian allocation and all knowledge functions remain unchanged.",
      "status": "complete",
      "evidence_ref": "planning/pov-roster.md reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm the existing PAIR registers already distinguish deliberate sends, current consent, opaque pauses, metadata, and ordinary-speech fallback and need no value change.",
      "status": "complete",
      "evidence_ref": "planning/voice-briefs.md reviewed with no value change required"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record exact prior and revised state, author approval, no-change impact evidence, and a clean planning-layer validation before prose relies on the repair.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, ARC-CHANGE-PRIVATE-PROTOCOL-001; global checker rerun after synchronization reported planning=0, global=134 expected incompleteness errors"
    }
  ],
  "approval": {
    "approved_by": "Author instruction in Kiro session",
    "approved_at": "2026-09-13T17:23:01Z",
    "approval_record": "Author instruction to soften the rigid system and use GPT-5.6 judgment before proceeding to Chapter 56."
  },
  "status": "complete",
  "completed_at": "2026-09-13T17:32:20Z"
}
```

### What this change deliberately does not do

It does not return Mara's array-room badge, source, probe, array time, anechoic hours, independent measurement capacity, or visibility into Emergency Preparedness. It does not let consent metadata stand in for semantic content, make an unconsented write articulate, create a fifth mode, or identify what caused Nia's winter. It changes no POV, participant, Reveal, motif placement, or later Chapter 62 onset boundary.
### Synchronization progress on `ARC-CHANGE-REVISION-001` and `ARC-CHANGE-REVISION-002`, 2026-09-13

Eighteen obligations moved from `pending` to `complete` with evidence in this pass: the seventeen Private_Defense Chapter_File obligations for Chapters 30 through 46, and the `planning/gate-results.md` objective-rerun obligation. The evidence for each names the current editorial gate and the observed Prose_Word count, and one obligation records a reasoned deviation rather than a clean discharge.

That deviation is Chapter 45. The obligation asked for the removal of any explicit statement of the `CUT-CONSTRAINABLE-CLAUSE` contradiction. Mara's recognition of the gap between Julian's initialed clause and the specification's waiting state is retained instead, because she is physically holding both documents at that moment and a narrator who failed to register what she was reading would be the artificial withholding Requirements 2.13 and 2.14 forbid. The irony that the cut exists to protect is Julian's, and it survives intact: Chapter 44 ends with the binder eighteen inches from his hand, and Chapter 45 ends on him stopping writing rather than on any account of what he now understands.

**Both revision records remain `in-progress`, and neither may reach `complete` yet.** Their current synchronization state is as follows.

- The twenty-nine Discovery Chapter_File obligations remain open. Their prose has been revised and every Chapter_Header and `ArcEntry` has been demoted to `revised`, so nothing currently overstates their status, but no per-chapter verification against the current craft authority exists for twenty-four of them. Word counts alone are not that verification.
- The former `estimated_words` mass re-budget is **closed by supersession, not performance**. `DEC-021` clause 5 and `ARC-CHANGE-LENGTH-GOVERNANCE-001` establish that existing estimates remain planning metadata and are not normalized into a quota the prose does not follow. No `ArcEntry.estimated_words` value changed.
- The re-recording of the Discovery movement Editorial_Gate remains open; `GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE` reports the unavailable current evidence and scopes it precisely.
- The objective chapter and batch reruns for Discovery remain open, because they have not been recorded since the revision changed those files.

`ARC-CHANGE-REVISION-002`'s own planning and canon obligations were already complete and remain so. It stays `in-progress` because it was written to close alongside the prose work it supports, and the Discovery half of that work is unfinished. Its Private_Defense half is now discharged: `CF-PRIVATE-EXPOSED-PERSONS-LIST`, `CF-PRIVATE-TECHNICIAN-REPORT`, `CF-PRIVATE-TECHNICIAN-REASSIGNMENT`, `CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY`, and `CF-PRIVATE-TWO-PERSON-LAYER-CLASS` are all on the page, and `CHAR-015` Joss Calder and `CHAR-016` Ruth Venn appear in Chapters 30, 34, 38, 40, 42, and 43 without becoming exposition audiences.

Under the status rules in this document, partial synchronization is never approval. No Discovery chapter returns to `approved`. The Private_Defense movement gate now passes as `GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-003`, completing task 13.6, but task 14 remains blocked by the separate Discovery evidence gap.

## `ARC-CHANGE-LENGTH-GOVERNANCE-001` — contextual manuscript budget and Chapter 118 repair

This change resolves a conflict created after baseline approval rather than disguising it as prose debt.
`DEC-018` and `DEC-019` left two different per-chapter bands and a fixed mean window in force while
amended `DEC-020` and Requirement 15.9 prohibited chapter-length quotas as craft logic. The current
manuscript was already inside its approved budget. `DEC-021` keeps the objective safeguards, retires the
formula, and authorizes the one chapter whose brevity remained a literary defect on independent grounds.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-LENGTH-GOVERNANCE-001",
  "date": "2026-09-18",
  "prior_state": {
    "decision_authority": "DEC-018 clause 10 named 1050-1200 and midpoint 1125; DEC-019 clause 11 named 900-1400 and a fixed normal mean window; DEC-019 clause 8 required exemptions",
    "outline_gate": "normal chapters judged against 1050-1200 with a mean near 1125",
    "estimated_words_obligation": "ARC-CHANGE-REVISION-001 required every normal ArcEntry estimate to be mass-rebudgeted into 1050-1200 and recorded the item as pending",
    "delivered_budget_evidence": "64 delivered files, historically recorded as 73147 Prose_Words; 55 normal chapters averaging 1134.4; projected completion approximately 143900, inside 130000-150000",
    "chapter_118": "756 Prose_Words, normal, exploratory; emotionally under-inhabited under EDITORIAL-REVISION-009-FOLLOWUP-001",
    "private_defense_gate": "GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002 revision solely because EDITORIAL-LENGTH-BAND-MANUSCRIPT-001 was open",
    "task_13_6": "unchecked"
  },
  "revised_state": {
    "decision_authority": "DEC-021 preserves objective limits and makes historical bands, midpoint, and derived means diagnostics rather than craft quotas or waiver triggers",
    "outline_gate": "contextual manuscript-budget safeguard judges scene-earned compression or expansion, adjacent cadence, delivered totals, remaining estimates, movement scale, and projected Final_Targets together",
    "estimated_words_obligation": "closed by supersession rather than performance; no ArcEntry estimate changes, and existing estimates retain movement-scale and same-POV run planning roles",
    "delivered_budget_evidence": "64 delivered files, 73604 declared Prose_Words; 55 normal chapters averaging 1142.7; current delivered class means projected across 109 normal, 10 microchapter, and 9 long-outlier outline entries give approximately 145400, inside 130000-150000",
    "chapter_118": "1215 observed and declared Prose_Words, normal, exploratory; local objective and editorial gates pass after craft expansion",
    "private_defense_gate": "GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-003 pass; all assigned craft criteria pass and the former governance blocker is resolved",
    "task_13_6": "complete; parent task 13 complete",
    "task_14": "still blocked by GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE and its 24 missing current chapter reviews, five batch reviews, movement re-verification, and objective reruns",
    "preserved_unchanged": [
      "Final_Targets of exactly 128 chapters and 130000-150000 Prose_Words",
      "Normal_Chapter_Range 700-1600 and Hard_Chapter_Maximum 2500",
      "at least 108 normal entries and no more than 20 outliers",
      "same-POV runs no longer than three chapters or 3600 combined Prose_Words",
      "all 128 ArcEntry values, including chapter 118 estimated_words 1400 and status exploratory",
      "POV-SAFIYA, TL-CODA-ACCOUNT, MOT-KETTLE-01, REVEAL-SAFIYA-TUESDAY-LOSS, and the 118-119 reveal window",
      "heritage_base unspecified_by_author and the describe-never-quote boundary",
      "the three never-revealed Reveal IDs and unresolved provenance",
      "four POVs, 56/32/33/7 loads, and 29/32/51/16 movement allocation",
      "no Chapter 62 prose or status change"
    ]
  },
  "rationale": "The historical bands repaired a real early shortfall, but the delivered manuscript now projects inside Final_Targets with margin and contains dramatically earned normal chapters on both sides of those bands. Cutting a load-bearing scene and padding a seventy-six-millisecond event would make the book more formulaic while improving no objective safeguard. The correct current rule is the one Requirement 15.9 already states: human review judges whether length varies for dramatic reasons in chapter, batch, movement, and manuscript context. Chapter 118 is different from the other departures because repeated literary review found its central account under-inhabited. Expanding it supplies domestic duration, bodily sequence, intact public competence, grief, and witnessed restraint without altering any continuity record or using arithmetic as the pass condition.",
  "affected_chapters": [118],
  "affected_documents": [
    "planning/decisions.md",
    "planning/arc-outline.md",
    "planning/arc-changes.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    ".kiro/specs/The-Final-Frontier-novel/tasks.md",
    "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/decisions.md",
      "required_change": "Record a later binding amendment that preserves objective limits, makes the historical bands diagnostic, retires waivers and fixed-mean gate logic, supersedes mass estimate normalization, and authorizes the bounded Chapter 118 craft repair.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-021 - Scene-earned chapter length under a contextual manuscript budget"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Extend current authority through DEC-021, replace the obsolete normal-band criterion with the contextual manuscript safeguard, and retain every ArcEntry value including chapter 118 estimated_words 1400.",
      "status": "complete",
      "evidence_ref": "planning/arc-outline.md, authority header, length-class budget current note, DEC-021 contextual manuscript-budget safeguard, and contextual gate criterion; no typed record changed"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Close the ARC-CHANGE-REVISION-001 mass re-budget obligation explicitly by supersession rather than by claiming the estimates were changed.",
      "status": "complete",
      "evidence_ref": "ARC-CHANGE-REVISION-001 synchronization_obligations now records complete with evidence 'Closed by supersession rather than performance'; the synchronization-progress note confirms no estimated_words value changed"
    },
    {
      "document": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
      "required_change": "Inhabit the Tuesday account through Safiya's domestic memory, body, intact interpreting work, and sole-survivor grief without crossing the Chapter 117/119, heritage, corpus, reconstruction, reveal, motif, or POV boundaries; synchronize the observed count and retain exploratory.",
      "status": "complete",
      "evidence_ref": "Chapter 118 now declares 1215 observed Prose_Words, normal, exploratory; EDITORIAL-AFTERMATH-CODA-118-REPAIR-001 and both local gates pass"
    },
    {
      "document": "planning/editorial-log.md",
      "required_change": "Attach structured resolutions to the open length finding and Chapter 118 follow-up, add current follow-up findings, and rerun the Chapter 118 local, nine-finding revision, and Private Defense movement editorial gates without editing historical verdicts.",
      "status": "complete",
      "evidence_ref": "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001, EDITORIAL-REVISION-009-FOLLOWUP-002, EDITORIAL-AFTERMATH-CODA-118-REPAIR-001, GATE-EDITORIAL-AFTERMATH-CODA-118-REPAIR-001, GATE-EDITORIAL-REVISION-PASS-003, and GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-003"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record a current Chapter 118 objective rerun after prose and header synchronization, and state why no adjacent Coda batch result is available.",
      "status": "complete",
      "evidence_ref": "GATE-CHAPTER-LOCAL-AFTERMATH-CODA-118-DEC-021-RERUN-001 pass; Chapters 117 and 119 remain undelivered"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
      "required_change": "Confirm Requirement 15.9 already prohibits chapter-length quotas as verdict logic and that objective length constraints remain unchanged; make no unnecessary text edit.",
      "status": "complete",
      "evidence_ref": "requirements.md reviewed: Requirement 15.9 requires contextual chapter-length judgment and forbids a chapter-length quota; Requirements 2, 11, and 12 retain objective limits"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/tasks.md",
      "required_change": "Mark task 13.6 and parent task 13 complete only after the Private Defense movement gate passes; leave task 14 unchecked because Discovery remains incomplete.",
      "status": "complete",
      "evidence_ref": "tasks.md: 13 and 13.6 checked; 14 remains unchecked; GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-003 pass and GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE retained"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm the amendment and prose repair change no CanonFact, NovelExtension, TimelineEntry, Reveal, heritage base, mechanism state, participant, or evidence boundary.",
      "status": "complete",
      "evidence_ref": "canon-bible.md reviewed with no value change required; Chapter 118 remains inside TL-CODA-ACCOUNT and REVEAL-SAFIYA-TUESDAY-LOSS"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm Chapter 118 still carries only MOT-KETTLE-01 and creates no second kettle event, MotifEvent, or LiteralPhraseConstraint.",
      "status": "complete",
      "evidence_ref": "motif-ledger.md reviewed with no value change required; chapter header and ArcEntry retain MOT-KETTLE-01 only"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm POV-SAFIYA, four-POV architecture, Anchor identity, chapter loads, and movement coverage remain unchanged.",
      "status": "complete",
      "evidence_ref": "pov-roster.md reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm the expanded direct-address prose delivers the existing Safiya register without changing voice guidance or entering Mara's interior.",
      "status": "complete",
      "evidence_ref": "voice-briefs.md reviewed with no value change required; EDITORIAL-AFTERMATH-CODA-118-REPAIR-001 passes current voice fidelity"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record exact prior and revised state, complete impact assessment, author authorization, and synchronization evidence in one typed ArcChange.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, ARC-CHANGE-LENGTH-GOVERNANCE-001"
    }
  ],
  "approval": {
    "approved_by": "Author instruction in Kiro session",
    "approved_at": "2026-09-18T22:10:00Z",
    "approval_record": "Author instruction: 'please repair the defects' and continue the current anti-formula, quality-first approach."
  },
  "status": "complete",
  "completed_at": "2026-09-18T22:10:00Z"
}
```

### Scope deliberately left open

This change does not complete `ARC-CHANGE-REVISION-001` or `ARC-CHANGE-REVISION-002`: their Discovery
review and rerun obligations remain open. It does not turn Chapter 118 from `exploratory` to `approved`,
claim a Coda drafting batch when Chapters 117 and 119 are absent, complete task 14, or begin Chapter 62.

## `ARC-CHANGE-VOICE-SEPARATION-001` — Discovery current evidence, voice repairs, and one house spelling standard

This change closes the Discovery evidence gap that `ARC-CHANGE-REVISION-001` left open, repairs the craft
defects that reading the current prose exposed, and fixes a manuscript-wide inconsistency that would
otherwise have propagated into sixty-four undrafted chapters. It changes no `ArcEntry`, canon fact,
timeline, reveal, motif, POV identity, or movement allocation.

Two of the repairs are continuity rather than polish and are recorded as such. Chapters 16 and 27 both
performed person-specific work without acknowledging the restraint memorandum Julian addressed to Mara in
Chapter 14 and the suspension still open at Chapter 25. Both now name the constraint they proceed
against. This increases the Anchor's culpability and removes an unearned innocence; it establishes no new
canon, because the memorandum and the suspension were already on the page.

```json record=ArcChange schema=1
{
  "arc_change_id": "ARC-CHANGE-VOICE-SEPARATION-001",
  "date": "2026-09-18",
  "prior_state": {
    "discovery_movement_evidence": "current craft evidence for 5 of 29 chapters; GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE reported the gap and asserted no verdict",
    "spelling_standard": "none recorded; mixed US and UK forms across the manuscript, including colour/color, neighbour/neighbor, licence/license, defence/defense, enrol/enroll, and mixed -ise/-ize inside the same word families",
    "shared_constructions": "the self-indictment marker in chapters 3, 5 and 6; a deliberation-formula ending in chapters 21, 22 and 28 across three narrators; the phrase 'I have not been able to' across three narrators; 'with the cap off the pen' in chapters 1, 5 and 10; a duplicated warmth-scene beat order in chapters 30 and 38; seven six-word phrases repeated across three or more chapters",
    "chapter_16_and_27_authorization": "person-specific build, transmission, and a consented session run without reference to the restraint memorandum or the open suspension",
    "chapter_13_participants": "four staff asked, then two refused plus three participants accounted for, which does not reconcile",
    "chapter_57_body": "an attempted unauthorized write into a refusing participant with no physical reaction from either person",
    "task_14": "blocked by missing Discovery evidence"
  },
  "revised_state": {
    "discovery_movement_evidence": "current craft evidence for all 29 chapters and all 6 batches, plus canon, shape, and voice movement findings; GATE-EDITORIAL-DISCOVERY-MOVEMENT-003 recorded",
    "spelling_standard": "one Oxford British house standard: -ize verb endings with colour, neighbour, licence as noun, defence, practised as verb, enrol, enrolment, labelled, travelled, towards, grey, metre",
    "shared_constructions": "self-indictment marker confined to one chapter; deliberation-formula ending broken in two of three; 'I have not been able to' assigned to the Anchor alone; the pen image left as one canonical instance with two varied callbacks; the Chapter 38 warmth scene rebuilt on a different beat order; cross-chapter six-word repetition reduced from seven to four, the survivors being technical terms and one assigned signature",
    "chapter_16_and_27_authorization": "both chapters name the constraint they proceed against, and Chapter 27 explicitly distinguishes the participant's consent from the chair's authorization",
    "chapter_13_participants": "four asked, one refused, three participants, three sessions",
    "chapter_57_body": "Mara's pulse in the hand that performs the send, and Nia taking her own pulse to check her body for a change a machine was asked to make in it",
    "task_14": "still blocked, now by EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE rather than by missing evidence",
    "preserved_unchanged": [
      "all 128 ArcEntry values, all 65 CrossCut records, and the approved Baseline",
      "receive-only December apparatus and the separate later temporary bench path",
      "receiver-owned reconstruction latency as a configuration-dependent cost",
      "unresolved causation, the DEC-007 asymmetry, and the three never-revealed Reveal IDs",
      "page nine as architectural capability only, absent from Discovery",
      "closed motif families with no new MotifEvent or LiteralPhraseConstraint",
      "four POVs and the 56/32/33/7 loads across 29/32/51/16",
      "every declared length class, including the Chapter 16 microchapter and the Chapter 13 and 17 long-outliers",
      "no Chapter 62 prose and no chapter returned to approved"
    ]
  },
  "rationale": "Reading all twenty-nine Discovery chapters against current text produced fifteen chapter revisions that no earlier record could have seen, because the earlier records evaluated pre-DEC-018 prose. Most were shared formulas rather than local faults: the same self-indictment marker in three chapters, the same closing construction in three narrators, the same warmth beat order in two chapters eight apart. Those are the signature of drafting at volume and they are invisible chapter by chapter, which is why a continuous read was required rather than another per-chapter audit. Two findings were continuity rather than craft and mattered more: the Anchor twice performed person-specific work inside a constraint the manuscript had already established, and the prose did not notice. The spelling standard was recorded now rather than later because half the manuscript is undrafted and an unrecorded standard guarantees the inconsistency returns. The voice-separation finding is left open and unresolved because it is real: local repairs removed the shared epigrams without producing the rhythm and paragraph-shape separation DEC-018 clause 7 requires, and passing the movement gate on the strength of the repairs would misrepresent the manuscript.",
  "affected_chapters": [1, 2, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 46, 47, 48, 49, 52, 53, 55, 56, 57, 58, 73, 118],
  "affected_documents": [
    "planning/arc-changes.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
    "planning/decisions.md",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    ".kiro/specs/The-Final-Frontier-novel/tasks.md"
  ],
  "synchronization_obligations": [
    {
      "document": "planning/editorial-log.md",
      "required_change": "Record current chapter findings for all 29 Discovery chapters, batch findings for all 6 batches, the repair follow-up, the canon, shape and voice movement findings, and the re-recorded movement gate, without editing any historical record.",
      "status": "complete",
      "evidence_ref": "EDITORIAL-DISCOVERY-CURRENT-001 through -029, EDITORIAL-DISCOVERY-CURRENT-BATCH-001-005 through -026-029, EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001, EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-CANON/-SHAPE/-VOICE, GATE-EDITORIAL-DISCOVERY-MOVEMENT-003"
    },
    {
      "document": "chapters/**",
      "required_change": "Repair the fifteen chapter revisions, rebuild one duplicated warmth scene, give Chapter 57 a physical body, and apply one spelling standard across all delivered files; resynchronize every header word count.",
      "status": "complete",
      "evidence_ref": "34 Chapter_Files changed prose; all 64 chapter-local gates and all 11 batch audits pass with zero errors; no declared length class changed"
    },
    {
      "document": "planning/gate-results.md",
      "required_change": "Record chapter-local reruns for every file whose prose changed and batch reruns for every delivered batch.",
      "status": "complete",
      "evidence_ref": "GATE-CHAPTER-LOCAL-*-VOICE-PASS-RERUN for 34 chapters and GATE-BATCH-*-VOICE-PASS-RERUN for all 11 delivered batches"
    },
    {
      "document": "planning/decisions.md",
      "required_change": "Record the Oxford British house spelling standard as binding editorial direction so the remaining 64 chapters inherit it.",
      "status": "complete",
      "evidence_ref": "planning/decisions.md, DEC-022 - House spelling standard and the voice-separation obligation"
    },
    {
      "document": "planning/canon-bible.md",
      "required_change": "Confirm that naming the restraint memorandum in Chapter 16 and the open suspension in Chapter 27 asserts no new CanonFact, since both were already established in Chapters 14 and 25.",
      "status": "complete",
      "evidence_ref": "canon-bible.md reviewed with no value change required; the memorandum is established at Chapter 14 and the suspension and deviation at Chapter 25"
    },
    {
      "document": "planning/motif-ledger.md",
      "required_change": "Confirm no MotifEvent or LiteralPhraseConstraint changed, and that removing the Chapter 13 metafictional motif-tag does not disturb MOT-CHAIN-01.",
      "status": "complete",
      "evidence_ref": "motif-ledger.md reviewed with no value change required; MOT-CHAIN-01 remains assigned to Chapter 13 and is now carried by the image rather than named in narration"
    },
    {
      "document": "planning/pov-roster.md",
      "required_change": "Confirm four profiles, one Anchor, and the 56/32/33/7 loads are unchanged, and record that the voice obligation falls on POV-NIA's narration rather than on her identity or load.",
      "status": "complete",
      "evidence_ref": "pov-roster.md reviewed with no value change required"
    },
    {
      "document": "planning/voice-briefs.md",
      "required_change": "Confirm the four Voice_Briefs already specify distinct registers, and record that the open finding is a failure of the prose to deliver VOICE-NIA rather than a defect in the brief.",
      "status": "complete",
      "evidence_ref": "voice-briefs.md reviewed with no value change required; EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE finds the guidance correct and undelivered"
    },
    {
      "document": "planning/arc-outline.md",
      "required_change": "Confirm no ArcEntry, CrossCut, or Baseline value changed and that no Discovery ArcEntry status moves out of revised.",
      "status": "complete",
      "evidence_ref": "arc-outline.md unchanged by this pass; all 29 Discovery ArcEntries and Chapter Headers remain revised"
    },
    {
      "document": ".kiro/specs/The-Final-Frontier-novel/tasks.md",
      "required_change": "Leave task 14 unchecked and record that its blocker has changed from missing evidence to an open craft finding.",
      "status": "complete",
      "evidence_ref": "tasks.md task 14 remains unchecked; GATE-EDITORIAL-DISCOVERY-MOVEMENT-003 result=revision"
    },
    {
      "document": "planning/arc-changes.md",
      "required_change": "Record this change with exact prior and revised state, the two authorization-continuity repairs, complete impact assessment across the reference system, author authorization, and per-document synchronization evidence in one typed ArcChange.",
      "status": "complete",
      "evidence_ref": "planning/arc-changes.md, ARC-CHANGE-VOICE-SEPARATION-001, and the updated active-record count in the initialization state"
    }
  ],
  "approval": {
    "approved_by": "Author instruction in Kiro session",
    "approved_at": "2026-09-18T23:40:00Z",
    "approval_record": "Author instruction: 'Please do everything you suggested' following the full status and quality review."
  },
  "status": "complete",
  "completed_at": "2026-09-18T23:40:00Z"
}
```

### What this change deliberately does not do

It does not return any Discovery chapter to `approved`, complete task 14, or begin Chapter 62. It does not
close the voice-separation finding, which requires a paragraph-scale pass on `POV-NIA`'s narration and is
recorded as the single remaining blocker. It does not alter the Mindwars or Coda plan, and it creates no
canon, motif, reveal, or cross-cut.
