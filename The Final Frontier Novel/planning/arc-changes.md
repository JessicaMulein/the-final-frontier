# Arc Changes

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `ArcChange`  
Workflow authority: Requirements 1.16–1.18, 10.7, 10.8, and 13.5–13.10; the design's Baseline, Arc Change, status, and delivery rules

This document is the active audit trail for changes proposed after the Approved Baseline. It makes an arc, continuity, motif, POV, voice, or related reference change atomic across every affected project record.

## Initialization state

**Active `ArcChange` records: 0.**

No Approved Baseline exists yet, so no post-baseline project change can honestly be recorded. That absence is intentional. It is stated in prose rather than represented by an empty or invented JSON record.

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

**The two blocks below are templates, not proposals.** No Approved Baseline exists, nothing here is approved, and every identifier, path, date, and value is an illustrative fixture. The chapter path in the second template is a placeholder for a Chapter File the Arc Outline has not yet named. Copy the shape, then write a real proposal into a typed fence under [Active records](#active-records).

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