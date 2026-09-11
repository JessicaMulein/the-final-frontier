# Editorial Log

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `EditorialFinding` and `GateResult`  
Workflow authority: Requirements 10.7, 10.8, and 13.5–13.10; the design's Editorial and Delivery Flow

This document is the active project log for evidence-bearing human editorial findings and editorial gate decisions. It records qualitative judgment; it is not a scoring sheet and does not duplicate the Manuscript Checker's objective audit.

## Initialization state

**Active `EditorialFinding` records: 0. Active editorial `GateResult` records: 0.**

No chapter or batch has yet received an editorial review under this log. That absence is intentional. It is stated in prose rather than represented by an empty or invented JSON record.

An actual project record exists here only when it appears in a schema-compatible typed JSON fence with one of these exact opening lines:

- `json record=EditorialFinding schema=1`
- `json record=GateResult schema=1`

The JSON body must be one object or a nonempty array of objects of the declared type. Typed fences are reserved for real, dated project records. Templates, placeholders, sample reviews, empty arrays, and `EXAMPLE` records must not appear in typed fences in this file. Commentary and tables outside typed fences are never parsed as record values.

The worked templates below therefore use untyped `json` fences and `EXAMPLE` identifiers. Because they carry no `record=` type, the parsing contract never treats them as project records. They are authoring aids with no review authority.

## Editorial authority boundary

Human Editorial Review exclusively decides subjective craft questions, including POV clarity and distinctness, Voice Brief fidelity, transition value, pacing, Cross Cut readability, Hook performance, originality, tenderness, restraint, tonal coherence, rhetorical force, emotional truth, human cost, and the Refused Swell.

The Manuscript Checker and its `CheckerDiagnostic` records decide only objective facts such as readability, metadata, identifiers, counts, status agreement, references, and ledgered literal constraints. A diagnostic must never produce, determine, or override an editorial finding. Conversely, an editorial pass must never waive an objective violation or incomplete objective prerequisite.

Numeric craft scores, weighted rubrics, synthetic voice ratings, sentiment values, sentence-length proxies, and numeric pass thresholds are prohibited. Chapter numbers and prose line numbers identify evidence; they are not craft scores.

## `EditorialFinding` record contract

Each finding addresses one qualitative criterion at a declared scope and cites representative prose evidence. It uses exactly the fields defined below and no additional fields.

| Field | Active-record rule |
|---|---|
| `editorial_finding_id` | A unique stable ID. It is never reused for another judgment. |
| `scope` | Exactly `chapter`, `batch`, `movement`, `calibration`, or `manuscript`. |
| `chapter_numbers` | Unique chapter numbers in ascending order. The array is nonempty for chapter and calibration findings. Batch findings identify the delivered chapters they evaluate. |
| `batch_id` | A stable Batch ID for `scope: batch`; otherwise `null` unless a governing record requires the batch association. |
| `criterion` | One nonblank qualitative criterion. It must name the craft question being judged rather than a numeric proxy. |
| `prose_locations` | A nonempty evidence array. Each item contains exactly workspace-relative `path`, positive `start_line`, ordered positive `end_line`, and a nonblank `note` explaining why the passage is evidence. |
| `finding` | Exactly `pass` or `revision`. No score, rank, percentage, or third craft outcome is permitted. |
| `rationale` | A nonblank explanation connecting the cited prose to the criterion and finding. |
| `requested_action` | A concrete nonblank action for `revision`; `null` is permitted for `pass`. |
| `reviewer` | The nonblank identity or role of the human reviewer. An automated checker is not an editorial reviewer. |
| `reviewed_at` | An RFC 3339 timestamp with an explicit offset. |
| `resolution` | `null` while unresolved. When resolved, an object containing exactly `resolved_at`, `action_taken`, and `follow_up_finding_id`; the follow-up record re-evaluates the criterion against current prose. |

A finding must not claim more scope than its evidence supports. A chapter finding cites that chapter. A batch, movement, calibration, or manuscript finding may cite multiple representative passages, but its rationale must explain how those locations support the scope-level conclusion.

A `revision` finding remains part of the audit trail. Resolution does not rewrite it into a pass: the original receives its resolution object, and a separate follow-up `EditorialFinding` records the new `pass` or further `revision` judgment.

## Editorial review workflow

1. **Establish current scope.** Identify the chapter numbers, batch when applicable, current Chapter Files, and current planning references. Evidence from text superseded by a substantive change cannot support a new gate pass.
2. **Assign required criteria.** Use the criteria required by the applicable chapter, calibration, first-appearance, batch, movement, Coda, or complete-manuscript gate. Record one or more evidence-bearing findings sufficient to make every assigned judgment explicit.
3. **Cite prose, then judge.** Capture exact file and line ranges, explain what the passage demonstrates, and record only `pass` or `revision`.
4. **Request a concrete change when needed.** A revision finding states the action sought without prescribing a numeric style target.
5. **Resolve without erasing history.** After the action is applied, add resolution evidence and a follow-up finding. Rerun every editorial gate affected by the change.
6. **Treat changed evidence as stale.** Author feedback or a Substantive Prose Change returns affected chapter and batch work to `revised`; affected editorial findings must be reviewed against the new prose before reapproval.
7. **Preserve exploratory freedom.** While a delivered batch remains `draft` or `revised` because findings are open, separately labeled `exploratory` drafting outside that batch may continue. It cannot be represented as approved continuity.

### Required review coverage by gate

- **Chapter approval/finalization:** current evidence must support passes for POV clarity, Voice Brief fidelity, continuity, and Hook effectiveness. The Arc Outline and Chapter Header must carry the same status only after the separate objective and editorial requirements pass.
- **Calibration:** findings must cover the assigned calibration criteria, including represented-POV Voice Brief evidence, voice separation, opening momentum, Cross Cut clarity, pacing, and Hook effectiveness. Any required tenderness, restraint, emotional truth, human cost, or Refused Swell criterion is also recorded for the delivered material.
- **First post-calibration POV appearance:** representative evidence and a current `pass` or `revision` finding against that POV's Voice Brief are required before the first containing batch can be approved.
- **Drafting batch:** every assigned chapter-level and batch-level craft gate is evaluated. The batch remains `draft` or `revised` while any required editorial or objective finding is unresolved.
- **Final Coda batch:** findings address whether the ending contracts through public consequence, intimate encounter, and outward obligation without using chapter length, room count, or any other numeric prose metric as a proxy.
- **Complete manuscript:** findings address POV distinctness, Cross Cut clarity, Hook effectiveness, tonal coherence, emotional truth, human cost, and the ending's unmet obligation and Refused Swell.

## Editorial `GateResult` contract

An editorial gate is a separate `GateResult` with the exact schema fields below.

| Field | Editorial-gate rule |
|---|---|
| `gate_result_id` | Unique stable ID for this evaluation. A rerun receives a new ID. |
| `gate_type` | Exactly `editorial`. |
| `scope` | An object containing exactly `chapter_numbers`, `documents`, and nonblank `description`; arrays contain the current scope without duplicates. |
| `prerequisite_state` | `complete` only when the current prose and references are available and every assigned editorial criterion has evidence; otherwise `incomplete`. |
| `objective_diagnostic_ids` | `[]`. Objective diagnostics belong to a separate objective Gate Result and do not determine this result. |
| `editorial_finding_ids` | Unique references to the findings supporting this gate, including the current follow-up evidence for any resolved revision. |
| `result` | `incomplete` when prerequisites are incomplete; `revision` when review is complete but one or more required findings still require revision; `pass` only when all required current findings pass and all earlier revision findings in the scope are resolved. |
| `checker_exit_status` | Always `null` for an editorial gate. |
| `timestamp` | RFC 3339 completion timestamp with an explicit offset. |

An editorial gate is incomplete rather than passing when required prose, Direct Planning References, assigned criteria, evidence locations, reviewer identity, or follow-up review is missing. A gate becomes stale when its prose or governing planning state changes substantively; the affected work remains or becomes `revised` until a new gate evaluates the current state.

## Worked templates

**The two blocks below are templates, not findings.** No chapter has been drafted and no review has occurred, so every identifier, path, line number, timestamp, and judgment in them is an illustrative fixture value. The paths reuse the fixture coordinates already used by `record-schemas.md` precisely so they cannot be mistaken for observations of real prose. Copy the shape, then write a real record into a typed fence under [Active records](#active-records).

The finding template shows the full revision lifecycle: an original `revision` finding, its resolution pointing at a follow-up, and the follow-up `pass` that re-evaluates the same criterion. The original is never rewritten into a pass.

```json
[
  {
    "editorial_finding_id": "EDITORIAL-EXAMPLE-TEMPLATE-001",
    "scope": "chapter",
    "chapter_numbers": [
      2
    ],
    "batch_id": null,
    "criterion": "Hook effectiveness at the chapter's final beat",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-ordinary-morning.md",
        "start_line": 44,
        "end_line": 52,
        "note": "Closing beat restates the measurement the previous chapter already delivered."
      }
    ],
    "finding": "revision",
    "rationale": "The last beat explains what the reader already holds, so the chapter ends on confirmation rather than on a pull into the next viewpoint.",
    "requested_action": "Rewrite the closing beat so the final action leaves an open obligation instead of summarizing the reception.",
    "reviewer": "Author/editor",
    "reviewed_at": "2026-09-12T10:00:00Z",
    "resolution": {
      "resolved_at": "2026-09-13T15:30:00Z",
      "action_taken": "Closing beat rewritten so the morning is interrupted rather than explained.",
      "follow_up_finding_id": "EDITORIAL-EXAMPLE-TEMPLATE-002"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-EXAMPLE-TEMPLATE-002",
    "scope": "chapter",
    "chapter_numbers": [
      2
    ],
    "batch_id": null,
    "criterion": "Hook effectiveness at the chapter's final beat",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-ordinary-morning.md",
        "start_line": 44,
        "end_line": 49,
        "note": "Revised closing beat ends on an unanswered interruption."
      }
    ],
    "finding": "pass",
    "rationale": "The revised beat withholds the explanation and hands the reader an unresolved arrival, so the pull now belongs to the chapter rather than to the summary.",
    "requested_action": null,
    "reviewer": "Author/editor",
    "reviewed_at": "2026-09-13T16:00:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-EXAMPLE-TEMPLATE-003",
    "scope": "batch",
    "chapter_numbers": [
      1,
      2,
      3,
      4,
      5
    ],
    "batch_id": "BATCH-EXAMPLE-TEMPLATE-01",
    "criterion": "Cross Cut clarity across the delivered batch without redundant replay",
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
        "note": "Source-side morning adds lived continuity instead of repeating the measurement."
      }
    ],
    "finding": "pass",
    "rationale": "Each side of the shared chronology contributes distinct material, and the reception delay reads as observation timing rather than as a break in the source-side morning.",
    "requested_action": null,
    "reviewer": "Author/editor",
    "reviewed_at": "2026-09-13T16:20:00Z",
    "resolution": null
  }
]
```

The gate template shows the same scope evaluated twice: once while a required criterion still needs revision, and once after the follow-up evidence exists. Both carry `checker_exit_status: null` because an editorial gate never reports a checker status, and both leave `objective_diagnostic_ids` empty because objective diagnostics belong to a separate objective Gate Result.

```json
[
  {
    "gate_result_id": "GATE-EXAMPLE-TEMPLATE-EDITORIAL-001",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [
        1,
        2,
        3,
        4,
        5
      ],
      "documents": [
        "planning/arc-outline.md",
        "planning/voice-briefs.md"
      ],
      "description": "Illustrative editorial evaluation of an opening delivery while one assigned criterion still requires revision."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [
      "EDITORIAL-EXAMPLE-TEMPLATE-001"
    ],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-12T11:00:00Z"
  },
  {
    "gate_result_id": "GATE-EXAMPLE-TEMPLATE-EDITORIAL-002",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [
        1,
        2,
        3,
        4,
        5
      ],
      "documents": [
        "planning/arc-outline.md",
        "planning/voice-briefs.md"
      ],
      "description": "Illustrative rerun of the same editorial scope after the revision was resolved and re-reviewed."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [
      "EDITORIAL-EXAMPLE-TEMPLATE-002",
      "EDITORIAL-EXAMPLE-TEMPLATE-003"
    ],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T17:00:00Z"
  }
]
```

Neither template contains a numeric craft score, and no real record may add one. The chapter numbers, line ranges, and timestamps above locate evidence in time and text; they never rate it.

## Independent approval gates

Objective and editorial gates are necessary, independent records:

- A chapter may become `approved` or `final` only after its Chapter Local objective gate has zero attributable violations **and** its editorial gate passes.
- A batch may become `approved` only after its current batch objective audit and current editorial gate both pass and every finding is resolved. Approval then synchronizes Chapter Status in every affected Chapter Header and Arc Outline entry, plus every Canon Bible, Motif Ledger, POV Roster, and Voice Brief record the batch changed or established.
- The complete Manuscript may become `final` only when a separate `manuscript-global` Gate Result and a separate final `editorial` Gate Result both pass.
- Objective success cannot substitute for editorial success. Editorial approval cannot override an objective violation, incomplete input, or failed synchronization.

When feedback changes prose or a planned arc beat, affected chapter and batch statuses become `revised`; all affected objective and editorial gates rerun before the work may return to `approved` or `final`. A post-baseline arc, continuity, motif, POV, or voice change additionally follows [`arc-changes.md`](arc-changes.md).

## Active records

There are no active records at initialization. Real records are appended below this heading only after the corresponding human review or editorial gate actually occurs.