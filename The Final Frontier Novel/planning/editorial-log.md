# Editorial Log

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `EditorialFinding` and `GateResult`  
Workflow authority: Requirements 10.7, 10.8, and 13.5–13.10; the design's Editorial and Delivery Flow

This document is the active project log for evidence-bearing human editorial findings and editorial gate decisions. It records qualitative judgment; it is not a scoring sheet and does not duplicate the Manuscript Checker's objective audit.

## Initialization state

**Active `EditorialFinding` records: 76. Active editorial `GateResult` records: 38.**

The 2026-09-18 author-commissioned `DEC-018` craft review of delivered Chapters 1–46 plus calibration Chapters 73, 118, and 124 is recorded last, in [`DEC-018` revision-pass review of delivered Chapters 1–46](#dec-018-revision-pass-review-of-delivered-chapters-146). It adds nine `revision` findings and one `revision` editorial gate, and it deliberately reverses several earlier passes at a larger scope without editing them: every earlier finding and gate stays in the audit trail as the honest record of the state it evaluated.

The first Calibration_Batch review and the corrective calibration reread are recorded below. The author asked for both while unable to read the chapters closely; the reviewer identity on each record is therefore an author-delegated agent reading, not a later author reread. The original revision findings remain in the audit trail with resolution objects, and separate dated follow-up findings evaluate the final revised prose. Objective checker success did not determine any verdict.

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

Calibration_Batch (chapters 1–5, 73, 118, 124), reviewed 2026-09-12. The gate result is `revision` because two required criteria still need a prose pass: the shared cancellation-field register between 73 and 118, and a generation tic that is making three voices sound like one careful log-keeper.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-CAL-001",
    "scope": "calibration",
    "chapter_numbers": [1, 3, 5, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Mara Voice_Brief fidelity",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 32,
        "end_line": 40,
        "note": "She names the apparatus before the feeling, then withholds the person-sentence on purpose."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 28,
        "end_line": 54,
        "note": "The recognition arrives in the body; appetite is logged as appetite; she chooses not to switch it off."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 26,
        "end_line": 48,
        "note": "The cathedral sentence dies in her mouth; the relay click and the kettle are the Coda_Turn."
      }
    ],
    "finding": "pass",
    "rationale": "Mara still sounds like Mara: experiment, result, then a human consequence she would rather not own. Chapter 5 is the best of her opening — attending to a stopped bell is a discovery, not a lecture. Chapter 124 does the Voice_Brief's cathedral-to-room-tone turn on the page instead of announcing it. The later-record tic in her log voice is hers; it only becomes a problem when Nia and Safiya borrow it.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-002",
    "scope": "calibration",
    "chapter_numbers": [2, 4, 73],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Nia Voice_Brief fidelity",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 16,
        "end_line": 32,
        "note": "Dispatch sequence, owned corrections, and a continuous morning she would never have reported."
      },
      {
        "path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "start_line": 18,
        "end_line": 36,
        "note": "Three clocks that do not belong to her; she refuses to invent a gap the story might want."
      },
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 12,
        "end_line": 54,
        "note": "Four conditions spoken standing up; yes has a time; the form is not her."
      }
    ],
    "finding": "pass",
    "rationale": "Nia's opening is the batch's cleanest writing. Clocks, headset, Fenn Street, the grey coat — she ends on what she can verify. Chapter 73 keeps that register when she is setting conditions and when she reports the missing sentence aloud. The Voice_Brief holds. What does not hold is the later habit of pausing to instruct the reader about how to read her, which is judged under voice separation rather than against this brief.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-003",
    "scope": "calibration",
    "chapter_numbers": [118],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Safiya Voice_Brief fidelity and DEC-003 describe-never-quote",
    "prose_locations": [
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 12,
        "end_line": 26,
        "note": "Eleven miles, kettle, invented private word used once, no real-language quote, no arrival."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 40,
        "end_line": 54,
        "note": "The lost name-for-her is described as function and empty access; public speech remains intact."
      }
    ],
    "finding": "pass",
    "rationale": "Safiya owns the Tuesday. *Oam* is one invented private-layer word and then she stops; there is no glossary and no performed aphasia. 'I have my other language' names nothing real-world. She is not an emblem. The Voice_Brief's dry close testimony is here. The cancellation-field sentences that reprint Nia are a different criterion.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-004",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Voice separation across Mara, Nia, and Safiya",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 30,
        "end_line": 36,
        "note": "Mara's log tic: temptation later, I want to be exact, produce this paragraph against me."
      },
      {
        "path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "start_line": 32,
        "end_line": 38,
        "note": "Nia using the same careful-log stance: I want to say the next part carefully."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 34,
        "end_line": 58,
        "note": "Safiya picking up I want you to sit with / I want that said plainly / I want to note that."
      }
    ],
    "finding": "revision",
    "rationale": "The three women are distinct in what they notice — cabinets, clocks, a kettle — and then they all explain themselves like the same scrupulous deposing witness. 'I want that noted', 'I want to be exact', 'I want you to understand', 'there will be a temptation later' is one model's throat. Mara can have the record-keeping self-consciousness; it is in her brief. Nia should restart a sentence when it claims too much, not host a seminar about future misreading. Safiya should get to the end of her own sentence without telling Mara how to sit with it. Until that tic is cut back, the batch sounds more generated than spoken.",
    "requested_action": "In chapters 2, 4, 73, and 118, cut or recast the reader-instruction sentences (I want that noted / I want to be exact / I want you to sit with / there will be a temptation later) so only Mara's log keeps that stance. Leave the observed facts. Do not add a new shared mannerism in their place.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": {
      "resolved_at": "2026-09-16T20:00:00Z",
      "action_taken": "Rewrote the eight calibration chapters so Mara keeps technical record language, Nia proceeds through dispatch sequence, correction, conditions, and consequences, and Safiya uses concrete domestic and bodily testimony. Removed the shared reader-instruction tics without replacing them with a new common formula.",
      "follow_up_finding_id": "EDITORIAL-CAL-013"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-005",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Opening momentum and DEC-002 receive-only facts",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 20,
        "end_line": 40,
        "note": "Weekday schedule; no transmit stage; no one to ask."
      },
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 28,
        "end_line": 32,
        "note": "Nia states there was no lost interval and no arrival."
      },
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 28,
        "end_line": 42,
        "note": "Eight seconds are in the receiving; the source may be unbroken; still no output path."
      }
    ],
    "finding": "pass",
    "rationale": "The opening does the job the calibration exists to do. Nia's morning is continuous. The offset is Mara's, on a receive-only rack, with no exciter and no path out of the building. Nothing in these five chapters hints at a December transmit. The Cross_Cut can wait a chapter; the pull from 1 into 2 is already there in the weekday-before-seven schedule meeting a woman who sits in a bell.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-006",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Cross_Cut clarity without redundant replay",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 26,
        "end_line": 28,
        "note": "A beat near two per second, then a barrier bell timed and discarded."
      },
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 12,
        "end_line": 20,
        "note": "Ridge Road crossing bell at about twice a second; the morning adds lived continuity, not the measurement."
      }
    ],
    "finding": "pass",
    "rationale": "Each side of the shared morning contributes what the other cannot see. Mara has a periodicity and a discarded candidate bell. Nia has the actual bell, the freight, and a dog that does not want to walk. Chapter 4 rebuilds the twenty minutes instead of replaying the crossing. The cut reads.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-007",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Hook variety and pacing",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 42,
        "end_line": 46,
        "note": "Ends on a bell she will not offer as evidence."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 54,
        "end_line": 56,
        "note": "Ends on who she tells, not on another measurement."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 60,
        "end_line": 64,
        "note": "Ends on a car going down the lane."
      }
    ],
    "finding": "pass",
    "rationale": "The hooks do different work: withheld person-sentence, unverifiable memory, a worse question, a closed notebook, a decision about disclosure, a missing phrase, a request not yet asked, a click and two cups. Chapter 73 is long because the brief asked it to be; the authorization scene earns the length and the last page (the wording traveling without her) is the actual ending, not another question gap. Pacing inside 1–5 is even to the point of sameness, but that is the voice-separation problem, not a missing beat.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-008",
    "scope": "calibration",
    "chapter_numbers": [73],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Chapter 73 Fluent_Pairing, local consent, and DEC-007 authority without provenance closure",
    "prose_locations": [
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 46,
        "end_line": 64,
        "note": "Did I say yes? spoken once; yes at eleven minutes past four; send-gate, pause, opaque metadata, no transcript."
      },
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 80,
        "end_line": 104,
        "note": "The missing sentence is reported aloud, not on the channel; usable judgment without settling origin."
      }
    ],
    "finding": "pass",
    "rationale": "The pairing is a switch, not a shared room. She tests unoffered mentation, pauses transport, and keeps the report of the loss off the channel so it cannot be filed as a contribution. Consent is specific, current, revocable, and spoken in the room. The corridor decision uses her judgment without forgiving anyone or validating an archive. The 'nobody was a villain' paragraph leans lecture; it does not undo the scene.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-009",
    "scope": "calibration",
    "chapter_numbers": [73, 118],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "DEC-017 delayed consent disclosure: shared cancellation-field register without narration",
    "prose_locations": [
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 70,
        "end_line": 88,
        "note": "The room went level; and it was clean; extractor fan as only texture; reach completed into an empty shelf."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 30,
        "end_line": 48,
        "note": "The same standalone sentence, the same clean, the same only-textured object, the same completed reach into an empty shelf."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 56,
        "end_line": 56,
        "note": "The recap restates 'the room going level and clean', which underlines the refrain a third time."
      }
    ],
    "finding": "revision",
    "rationale": "Reuse was required. Reprinting is what arrived. Chapter 118 copies Nia's two-sentence formula, her no-pain inventory, her one remaining textured sound, and her completed reach into a clean empty shelf. A reader does not assemble a parallel; the author knocks. Nobody names the connection, and 118 keeps authorization questions away — those halves are right. The shared register is not distinctive enough to be recognized later because it is not a register, it is a copied paragraph. This is the clearest mark of a weaker drafting pass: when asked to echo, it pasted.",
    "requested_action": "Keep the sensation family — flattening, no pain, one ordinary sound that continues, a finished reach into absence. Rewrite 118 so Safiya finds her own sentences for those facts. Remove the identical standalone 'The room went level.', the matching 'And it was clean', the empty-shelf formula, and the recap that repeats 'level and clean'. Do not have anyone gesture at Chapter 73.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": {
      "resolved_at": "2026-09-16T20:05:00Z",
      "action_taken": "Preserved only the sensory family of flattening, painless subtraction, one continuing ordinary sound, and a completed motion into absence. Rewrote Chapter 118 entirely in Safiya's domestic vocabulary and removed the copied standalone sentences, empty-shelf formula, recap, and any explicit Chapter 73 link.",
      "follow_up_finding_id": "EDITORIAL-CAL-014"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-010",
    "scope": "calibration",
    "chapter_numbers": [118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Safiya's ownership of loss; Mara's truth-based refusal and Coda_Turn",
    "prose_locations": [
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 50,
        "end_line": 60,
        "note": "The lost layer had no copy; she asks only after the Tuesday is finished."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 32,
        "end_line": 64,
        "note": "Your yes is good; I cannot; relay off; kettle; river talk; no comfort sentence."
      }
    ],
    "finding": "pass",
    "rationale": "Safiya is not used to make Mara careful. Mara says the yes is good and the no is about missing source truth, not ethics, and she puts the machine off before the second kettle. The refused swell is the unwritten species paragraph. What remains is two cups and a car on the lane. Tenderness is in the listening, not in a hand on an arm.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-011",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Tenderness, restraint, human cost, emotional truth, Refused_Swell, and absence of recognizable imitation",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 46,
        "end_line": 52,
        "note": "Receiving what was not given; she will not call it detection."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 24,
        "end_line": 30,
        "note": "A counterfeit would arrive as memory; the general-case paragraph is stopped."
      }
    ],
    "finding": "pass",
    "rationale": "The cost is specific: a weekday schedule that implies a person; a sentence Nia cannot get back; a mother's name-for-her with no copy; a house that only protects Mara. Nobody is comforted on the reader's behalf. Technical passages stay attached to a hand, a kettle, a corridor, a switch. I do not hear a named novelist's manner so much as a competent contemporary first-person default — which is the voice-separation tic already flagged, not a pastiche of one book.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-012",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Julian absent; Requirement 5.11 first-appearance gate left open",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 12,
        "end_line": 14,
        "note": "Opening cast is Mara alone with the array; Julian is not introduced."
      }
    ],
    "finding": "pass",
    "rationale": "Julian does not appear. That is correct for this batch. Requirement 5.11 remains unresolved and is owed to the first later Discovery batch that contains him; this review does not pretend to have heard his Voice_Brief on the page.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T02:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-013",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Corrective follow-up: voice separation across Mara, Nia, and Safiya",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 29,
        "end_line": 50,
        "note": "Mara corrects the archive-versus-output distinction in technical record language and limits the conclusion to the tested configuration."
      },
      {
        "path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "start_line": 20,
        "end_line": 32,
        "note": "Nia reconstructs the interval through stamps, sequence, correction, and consequence without instructing a future reader how to interpret her."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 22,
        "end_line": 54,
        "note": "Safiya testifies through kitchen objects, bodily access, interpreting work, and the private layer rather than borrowing Mara's log or Nia's dispatch syntax."
      }
    ],
    "finding": "pass",
    "rationale": "The corrective pass separates the three voices at the sentence-making level, not only by prop. Mara qualifies mechanisms and records controls; Nia orders facts and revises claims that outrun evidence; Safiya stays with household sound, bodily access, and the work of carrying meaning. The shared reader-instruction tics identified in EDITORIAL-CAL-004 are gone, and no replacement tic crosses all three voices.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:10:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-014",
    "scope": "calibration",
    "chapter_numbers": [73, 118],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Corrective follow-up: DEC-017 sensory-family echo without copied narration or explicit linkage",
    "prose_locations": [
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 65,
        "end_line": 90,
        "note": "Nia experiences a level interior, one textured extractor sound, and a completed speech motion with no accessible phrase."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 28,
        "end_line": 53,
        "note": "Safiya renders flattening as lost depth, keeps the kettle's road-sound granular, and completes a familiar inward motion without the word."
      }
    ],
    "finding": "pass",
    "rationale": "The two chapters now share only the concrete sensory family required by DEC-017: painless flattening, one ordinary continuing sound, and a familiar act completing into absence. Chapter 118 uses Safiya's own domestic and linguistic vocabulary, contains none of Chapter 73's copied standalone formulas, and never names the parallel or raises an authorization question.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:15:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-015",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "December chronology, receiver-owned variable reconstruction latency, and supporting-witness integration",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 16,
        "end_line": 44,
        "note": "Nia's alarm, shower, 6:31 road call with Kev, crossing, Dev interaction, and ten-to-seven console sequence remain continuous."
      },
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 18,
        "end_line": 50,
        "note": "Ravi independently checks acquisition timing and repeats the same-sample control; eight seconds belong after acquisition and vary when context, fidelity, or processing changes."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 15,
        "end_line": 49,
        "note": "The receiver-not-source result, coherence tradeoff, receive-only condition, and this particular ordinary morning's eight-second resolution are stated without a universal constant."
      }
    ],
    "finding": "pass",
    "rationale": "The opening now uses the canonical mechanism consistently. Raw field acquisition and timestamping are continuous; the early configured reconstruction produces legible experience eight seconds later; same-sample/same-settings reprocessing reproduces that latency; reduced context or processing buys speed by degrading coherence. Nia has no gap, there is no transmit stage, and no cabinet-based acquisition asymmetry remains. Ravi, Kev, and Dev are restrained continuity witnesses rather than new viewpoints or sources of cultural inference.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:20:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-016",
    "scope": "calibration",
    "chapter_numbers": [73],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Chapter 73 bounded consent, contemporaneous knowledge horizon, consequence reporting, and usable self-trust",
    "prose_locations": [
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 12,
        "end_line": 49,
        "note": "Nia originates four ordered conditions, asks the protected question once, and gives spoken consent for one bounded run at one time with the stop in her hand."
      },
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 52,
        "end_line": 94,
        "note": "Pairing remains gated and cancellable; the field ends; the missing phrase is reported aloud and Halloran records Nia's correction from recall to access."
      },
      {
        "path": "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "start_line": 94,
        "end_line": 123,
        "note": "The room cannot know whether the effect can be aimed, widened, or altered; Nia logs local success and consequence, then makes a usable present-tense judgment without provenance closure."
      }
    ],
    "finding": "pass",
    "rationale": "The revised scene preserves the ethical and procedural core while respecting DEC-017's horizon. Halloran transcribes and receives consent, but Nia originates every condition and correction. The chapter draws no scalable doctrine, retrospective deployment history, universal reverse claim, or future-machine law. Its close is local: provenance remains unsettled, Nia declines the console for that night, and she trusts that bounded judgment without absolving Mara or validating the archive.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:25:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-017",
    "scope": "calibration",
    "chapter_numbers": [118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Coda ownership, maternal-language continuity, truthful refusal, and two-event kettle progression",
    "prose_locations": [
      {
        "path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "start_line": 12,
        "end_line": 57,
        "note": "Safiya directly addresses Mara, fixes Tuesday and eleven miles, uses Oam once, preserves public language and interpreting competence, and identifies a partial private maternal-layer loss without drinking tea."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 34,
        "end_line": 64,
        "note": "Mara affirms consent, refuses only what cannot be made truthful, switches the relay off, then fills the kettle as the first present-day kettle act in her room."
      }
    ],
    "finding": "pass",
    "rationale": "Safiya owns both the loss and the request. Her public language remains intact while the private maternal layer is partly unavailable; the prose neither names a real heritage base nor performs generalized aphasia. Chapter 124 makes the no conditional on available apparatus and evidence rather than unsupported years of searching or a universal future claim. MOT-KETTLE-01 remains Safiya's past Tuesday event; MOT-KETTLE-02 begins only after Mara disables the present relay, with no already-cold water and no implied Chapter 118 tea consumption.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:30:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-CAL-018",
    "scope": "calibration",
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "batch_id": "BATCH-CALIBRATION-001",
    "criterion": "Current calibration opening momentum, Cross_Cut clarity, hook variety, restraint, human cost, and emotional truth",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 26,
        "end_line": 46,
        "note": "The acquisition fact leads through a discarded barrier-bell control to a receive-only log and a decisive matched-load test."
      },
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 20,
        "end_line": 47,
        "note": "The reciprocal morning contributes lived continuity rather than replaying Mara's measurement, and ends on a remembered bell Nia refuses to promote into evidence."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 45,
        "end_line": 62,
        "note": "Technical discovery becomes an ethical consequence and a bounded disclosure decision, with the final sent message occurring outside the receive-only apparatus."
      },
      {
        "path": "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
        "start_line": 42,
        "end_line": 64,
        "note": "The relay-off action contracts into kettle, chairs, ordinary talk, and a car leaving without absolution or renewed spectacle."
      }
    ],
    "finding": "pass",
    "rationale": "The final reread finds the calibration batch coherent and varied. Chapters 1–5 move from anomaly through lived counter-view, failed control, chronology reconstruction, and ethical recognition without redundant scene replay. Chapter 73 slows for consent and consequence rather than exposition. Chapters 118 and 124 contract the scale into testimony and refusal. Endings turn on different obligations, decisions, absences, and local actions; none supplies provenance closure, triumph, imitation of a named novelist, or a baseline approval verdict.",
    "requested_action": null,
    "reviewer": "Author-delegated corrective editorial review",
    "reviewed_at": "2026-09-16T20:35:00Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-CALIBRATION-001",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
    "documents": [
      "chapters/discovery-part/discovery-part-001-noise-floor.md",
      "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
      "chapters/discovery-part/discovery-part-003-the-failed-check.md",
      "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
      "chapters/discovery-part/discovery-part-005-not-a-message.md",
      "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
      "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
      "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md",
      "planning/arc-outline.md",
      "planning/canon-bible.md",
      "planning/motif-ledger.md",
      "planning/pov-roster.md",
      "planning/voice-briefs.md"
    ],
    "description": "Corrective Calibration_Batch editorial reread for task 8.7. Author-delegated while the author could not read closely. The original revision findings remain historical and are resolved by current follow-up passes; all required calibration criteria now pass. This result preserves exploratory chapter status and does not approve any chapter or the baseline."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": [
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
  "result": "pass",
  "checker_exit_status": null,
  "timestamp": "2026-09-16T20:40:00Z"
}
```

## Chapters 6–10 drafting-batch review and Julian first appearance

Author-delegated editorial review completed 2026-09-17 for `BATCH-DISCOVERY-006-010`. No prose revision was required. The first five findings establish current chapter-level approval evidence; the last two establish batch-level craft evidence. `EDITORIAL-DISCOVERY-006-010-001` is also the Requirement 5.11 first-appearance review carried by `VOICE-JULIAN.first_appearance_review`.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-001",
    "scope": "chapter",
    "chapter_numbers": [6],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Julian first-appearance Voice_Brief fidelity, POV clarity, continuity, and Hook effectiveness",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 21,
        "end_line": 22,
        "note": "Filters, amplifiers, digitisers, clocks, storage, heat, sealed outputs, and the safer noun establish Julian's documentary sensory field."
      },
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 39,
        "end_line": 44,
        "note": "The hardware audit becomes balanced review-facing distinctions and then a plain enterable finding that the December apparatus is receive-only."
      },
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 57,
        "end_line": 57,
        "note": "He treats Mara's insistence as ordinary caution and keeps the unasked future-apparatus question outside his instruction, demonstrating institutional distance and delayed notice."
      },
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 75,
        "end_line": 78,
        "note": "He makes restricted-fund approval faster, admits that his review cleaned the file, and only afterward hears the question the institution actually asked."
      }
    ],
    "finding": "pass",
    "rationale": "Julian's first chapter is recognizably his rather than a generic procedural narrator. Clauses anticipate future reviewers and define what each technical fact does and does not establish; sensory attention stays with binders, schedules, ledgers, sealed ports, margins, and clean copies; Mara and the unknown person remain bodies at the center of administrative categories. His evasion is credible because he confines himself to the instruction while using real competence to accelerate access. The Hearing chamber Reverb_Profile is active in every qualification, then empties into the unqualified admissions that the file was cleaner because of him and that he noticed the moral question late. The final reversal performs the declared Hook without changing the December receive-only fact or granting Julian knowledge outside his record horizon.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:00:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-002",
    "scope": "chapter",
    "chapter_numbers": [7],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Chapter 7 POV clarity, Nia Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 13,
        "end_line": 38,
        "note": "Nia resolves a map-versus-voice conflict through dispatch condition and consequence, then keeps the physical ticket after the ordinary call ends safely."
      },
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 52,
        "end_line": 55,
        "note": "Her sequence-correction-condition-consequence syntax keeps the shift continuous and explicitly excludes any source-side gap."
      },
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 69,
        "end_line": 74,
        "note": "The yellow strip enters her notebook as an over-complete ordinary detail and the final line fulfills the remembered-anyway Hook."
      }
    ],
    "finding": "pass",
    "rationale": "The chapter is unmistakably Nia: operational sequence, correction owned in the moment, material paper retained because systems erase what people need, and no retrospective claim beyond what she can verify. It preserves a continuous source-side shift and contributes the lived detail Chapter 8 cannot own. The closing action and repeated final sentence perform the declared Hook without coy withholding.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:01:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-003",
    "scope": "chapter",
    "chapter_numbers": [8],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Chapter 8 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 15,
        "end_line": 43,
        "note": "Mara moves through acquisition, external event alignment, falsification controls, and the qualified neural-timing result while keeping eight seconds at her receiver."
      },
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 45,
        "end_line": 50,
        "note": "She states the reconstruction tradeoff, limits the offset to tested conditions, and turns the result into her first deliberate institutional withholding."
      },
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 63,
        "end_line": 66,
        "note": "The supportable hypothesis is written while the source line remains empty, directly performing the chapter Hook."
      }
    ],
    "finding": "pass",
    "rationale": "Experiment, control, result, qualification, and human consequence arrive in Mara's established order. The chapter neither invents an identity nor turns receiver latency into a source discontinuity or channel constant. Her choice not to request identifying access is ethically pressured but not presented as protection, and the empty source line lands as action rather than exposition.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:02:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-004",
    "scope": "chapter",
    "chapter_numbers": [9],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Chapter 9 POV clarity, Julian Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 43,
        "end_line": 50,
        "note": "Institutional appetite appears through meeting invitations, publication holds, finance questions, option-preserving documents, and Julian's short admission that he made the accumulation efficient."
      },
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 57,
        "end_line": 58,
        "note": "He supplies the review-facing consent answer while withholding the shorter human answer because the circulated version seems more useful."
      },
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 65,
        "end_line": 74,
        "note": "His real restrictions become the route by which the briefing can move, and the empty evidentiary space acquires institutional value at the Hook."
      }
    ],
    "finding": "pass",
    "rationale": "The second Julian chapter deepens rather than repeats his first appearance. Its documentary field shifts from hardware disclosure to tracked changes, recipient lists, folders, approvals, and circulation. Balanced safeguards are both genuine constraints and mechanisms of access, which makes complicity active rather than merely confessed. The final empty-space valuation performs the appetite Hook and stays within Julian's limited knowledge.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:03:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-005",
    "scope": "chapter",
    "chapter_numbers": [10],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Chapter 10 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 13,
        "end_line": 33,
        "note": "Mara rejects location through physical controls, then recognizes a repeatable living-source address hypothesis while carefully withholding uniqueness claims."
      },
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 43,
        "end_line": 44,
        "note": "She converts Julian's procedural boundary into a personal decision and declines the briefing."
      },
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 67,
        "end_line": 78,
        "note": "The failed compliance form does not absolve ongoing acquisition; her narrow log statement and final sentence perform the no-form-is-not-permission Hook."
      }
    ],
    "finding": "pass",
    "rationale": "The chapter advances the planned reversal from place toward a person-specific channel without prematurely claiming a unique lock beyond the current controls. Mara's abstractions repeatedly meet the unknown person's lack of contact or consent. Declining the briefing does not become self-exoneration, and the final beat names institutional absence as responsibility rather than permission.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:04:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-006",
    "scope": "batch",
    "chapter_numbers": [6, 7, 8, 9, 10],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, technical-consequence staging, and originality",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 75,
        "end_line": 78,
        "note": "Julian ends on institutional acceleration and the question nobody commissioned."
      },
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 41,
        "end_line": 47,
        "note": "Nia owns the corrected open-o, arrow, and coffee crescent before those details become experimental evidence."
      },
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 27,
        "end_line": 39,
        "note": "Mara uses the same event as an external marker and falsification test without replaying Nia's shift or interior."
      },
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 43,
        "end_line": 50,
        "note": "A technical receive-only result immediately changes institutional review speed and commercial readiness."
      },
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 27,
        "end_line": 44,
        "note": "The location failure becomes a human consequence, address hypothesis, and decision to refuse the briefing."
      }
    ],
    "finding": "pass",
    "rationale": "Every transition adds Material_Narrative_Value: Julian's enterable hardware finding yields to Nia's unobserved competence; Nia's retained detail yields to Mara's ethically compromised use of it; Mara's provisional withholding yields to Julian's view of institutional appetite; Julian's efficient constraints yield to Mara's refusal and rights problem. Chapters 7 and 8 form a legible reciprocal Cross Cut with no redundant replay. The five endings vary across delayed moral notice, retained ordinary detail, an empty source line, institutional valuation, and a responsibility statement. Technical explanation consistently produces a human or institutional consequence in the same sequence. The prose uses original character-specific registers and shows no recognizable imitation, artificial cliffhanger pattern, lecture dialogue, provenance closure, or group-mind framing.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:05:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-006-010-007",
    "scope": "batch",
    "chapter_numbers": [6, 7, 8, 9, 10],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Tenderness, restraint, emotional truth, human cost, and Refused_Swell consistency",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 75,
        "end_line": 78,
        "note": "Julian's competence carries institutional risk without a melodramatic confession or acquittal."
      },
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 69,
        "end_line": 74,
        "note": "Nia's ordinary kept paper preserves a person and a working judgment without knowing she is evidence."
      },
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 45,
        "end_line": 50,
        "note": "Mara recognizes that administrative access would objectify an unknown live person and withholds a still-unverified human-source inference."
      },
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 57,
        "end_line": 69,
        "note": "The person absent from the file remains the moral center while Julian's safeguards become the means of circulation."
      },
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 67,
        "end_line": 78,
        "note": "The unavailable form, ongoing storage, lack of consent, and narrow log entry keep cost and responsibility unresolved."
      }
    ],
    "finding": "pass",
    "rationale": "The batch keeps the unknown observed person human without manufacturing intimacy or asking her to symbolize the mechanism. Tenderness resides in believing a working voice over a map and preserving an unremarkable detail; restraint resides in provisional claims, withheld access requests, and refusals that do not pretend to stop harm already underway. Human cost grows through observation, storage, administrative objectification, and institutional appetite rather than spectacle. No chapter offers absolution, victory, origin certainty, or anthemic escalation, so the material remains emotionally truthful and consistent with the Refused Swell.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T01:06:00Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-006",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [6],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter 6 editorial approval gate, including Julian's Requirement 5.11 first post-calibration appearance review."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:07:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-007",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [7],
      "documents": ["chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter 7 editorial approval gate."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:08:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-008",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [8],
      "documents": ["chapters/discovery-part/discovery-part-008-provisional-identity.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter 8 editorial approval gate."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-003"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:09:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-009",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [9],
      "documents": ["chapters/discovery-part/discovery-part-009-appetite-before-result.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter 9 editorial approval gate."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-004"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:10:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-010",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [10],
      "documents": ["chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter 10 editorial approval gate."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-005"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:11:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-006-010",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [6, 7, 8, 9, 10],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "chapters/discovery-part/discovery-part-008-provisional-identity.md", "chapters/discovery-part/discovery-part-009-appetite-before-result.md", "chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapters 6–10 Drafting_Batch editorial approval gate. All chapter-level and assigned batch-level findings pass, and no earlier revision finding exists in this scope."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-006-010-001", "EDITORIAL-DISCOVERY-006-010-002", "EDITORIAL-DISCOVERY-006-010-003", "EDITORIAL-DISCOVERY-006-010-004", "EDITORIAL-DISCOVERY-006-010-005", "EDITORIAL-DISCOVERY-006-010-006", "EDITORIAL-DISCOVERY-006-010-007"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T01:12:00Z"
  }
]
```

## Task 12.7 — Discovery_Part movement editorial gate

Author-delegated editorial review read the current Chapters 1–29 in sequence against the current Arc Outline, Canon Bible, Motif Ledger, POV Roster, Voice Briefs, Cross Cuts, Reveal Ledger, and prior batch evidence. One review finding required a planning correction: the Reveal Ledger placed first reader release of Nia's shared source/casualty identity in Chapter 24 under Nia, although Chapter 23 necessarily and explicitly verifies that identity in Mara's limited POV. `ARC-CHANGE-DISCOVERY-001` aligns the record with Chapter 23 rather than creating artificial withholding. No prose revision was required. The original revision remains below with a resolution; the follow-up finding and every other current finding pass.

### Current chapter-local findings

Each finding below covers the four chapter-approval craft gates against current prose: POV clarity, Voice Brief fidelity, continuity, and Hook effectiveness. Chapters 6–10 retain their existing current passes `EDITORIAL-DISCOVERY-006-010-001..005` and are not duplicated.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-001",
    "scope": "chapter",
    "chapter_numbers": [1],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "Chapter 1 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-001-noise-floor.md", "start_line": 35, "end_line": 46, "note": "Receive-only limits, person-sentence omission, written control, and the world-changing final alternative establish Mara's analytic voice and perform the Hook."}],
    "finding": "pass",
    "rationale": "Mara names apparatus before fear, limits knowledge to a receive-only anomaly, and ends on a concrete falsification test rather than a coy withheld noun. The current text agrees with the December timeline and its declared Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:01:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-002",
    "scope": "chapter",
    "chapter_numbers": [2],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "Chapter 2 POV clarity, Nia Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "start_line": 34, "end_line": 46, "note": "Nia verifies an unbroken sequence and ends on the remembered bell without promoting it into evidence."}],
    "finding": "pass",
    "rationale": "Dispatch sequence and self-correction distinguish Nia from Mara, preserve source-side continuity, and let the bell's unexplained availability perform the Hook without false mystery claims.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:02:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-003",
    "scope": "chapter",
    "chapter_numbers": [3],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "Chapter 3 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-003-the-failed-check.md", "start_line": 40, "end_line": 52, "note": "Mara confines eight seconds to configured reconstruction, preserves a continuous source, and turns to the next falsifiable question."}],
    "finding": "pass",
    "rationale": "The controls, qualifications, and plain final question are recognizably Mara's. The chapter never turns receiver latency into source delay or a universal constant, and its final beat advances the inquiry.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:03:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-004",
    "scope": "chapter",
    "chapter_numbers": [4],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "Chapter 4 POV clarity, Nia Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "start_line": 30, "end_line": 42, "note": "Nia separates finding from correction, protects the first sequence against later verbs, and closes on an ordinary coat."}],
    "finding": "pass",
    "rationale": "The chapter's procedural self-audit makes continuity human rather than technical. Its deliberately ordinary ending refuses melodrama while completing the no-gap Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:04:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-005",
    "scope": "chapter",
    "chapter_numbers": [5],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "Chapter 5 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-005-not-a-message.md", "start_line": 45, "end_line": 60, "note": "Technical recognition becomes overhearing, pleasure becomes culpability, and the only sent message remains outside the apparatus."}],
    "finding": "pass",
    "rationale": "Mara's experiment-result-consequence movement is intact, December remains receive-only, and the final ordinary message performs the disclosure Hook without implying any neural send.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:05:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-011",
    "scope": "chapter",
    "chapter_numbers": [11],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Chapter 11 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "start_line": 65, "end_line": 80, "note": "Mara qualifies what has and has not been read, writes the field hypothesis, and lands on a changed meaning of place."}],
    "finding": "pass",
    "rationale": "The chapter earns the mind-as-field canon beat through controls rather than assertion. Mara's analytic register and limited claim remain clear, and the final field-as-place reversal fulfills the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:11:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-012",
    "scope": "chapter",
    "chapter_numbers": [12],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Chapter 12 POV clarity, Nia Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "start_line": 78, "end_line": 92, "note": "The call's human load exceeds the formal fields, and Nia ends on the timestamp that cannot record her attention."}],
    "finding": "pass",
    "rationale": "Nia owns the call as labor and sequence, not as Mara's data. The chapter adds private human value to the Cross Cut and ends on evidentiary insufficiency rather than manufactured peril.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:12:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-013",
    "scope": "chapter",
    "chapter_numbers": [13],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Chapter 13 POV clarity, Mara Voice_Brief fidelity, continuity, motif function, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "start_line": 123, "end_line": 142, "note": "The receive-only lock becomes spectrum-to-bone, remains nonsemantic and unlocated, and survives return to the oldest sample."}],
    "finding": "pass",
    "rationale": "The long outlier earns its space through failed controls and cold-start proof. `MOT-CHAIN-01` gains its planned bodily function without inventing transmission, and the recovered address performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:13:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-014",
    "scope": "chapter",
    "chapter_numbers": [14],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Chapter 14 POV clarity, Julian Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-014-rights-before-names.md", "start_line": 82, "end_line": 102, "note": "Julian strips qualifications from the warning and accepts that sending it makes his knowledge enterable."}],
    "finding": "pass",
    "rationale": "Documentary detail, balanced clauses, and the final unqualified admission distinguish Julian. Rights consequences follow immediately from Mara's lock, and the send action fulfills the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:14:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-015",
    "scope": "chapter",
    "chapter_numbers": [15],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Chapter 15 POV clarity, Julian Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "start_line": 97, "end_line": 112, "note": "Julian distinguishes future stewardship claims from actual capability, states that page nine does not exist, and ends on holder pressure."}],
    "finding": "pass",
    "rationale": "Julian's safeguards become routes without making him omniscient. The chapter earns the somebody-alive certainty, preserves page-nine chronology, and closes on institutional possession rather than a repeated laboratory question.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:15:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-016",
    "scope": "chapter",
    "chapter_numbers": [16],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Chapter 16 POV clarity, Mara Voice_Brief fidelity, continuity, motif function, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-016-come-in.md", "start_line": 13, "end_line": 60, "note": "Mara visibly adds a separate temporary path, sends a content-free handshake, and recognizes that she alone defined knocking."}],
    "finding": "pass",
    "rationale": "The microchapter cleanly separates December reception from a later deliberate send. `MOT-COME-01` works as thought and scene structure without semantic payload, and the final ethical reversal performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:16:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-017",
    "scope": "chapter",
    "chapter_numbers": [17],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Chapter 17 POV clarity, Nia Voice_Brief fidelity, continuity, human consequence, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "start_line": 37, "end_line": 45, "note": "Ordinary practice and the resource table favor the collapse before Nia's nonverbal wanting chooses the road."}, {"path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "start_line": 163, "end_line": 178, "note": "Nia owns the routing act while finding no first half for the certainty, and the Hook lands on that missing beginning."}],
    "finding": "pass",
    "rationale": "The long outlier gives scarcity and one real death their needed sequence. Nia experiences wanting rather than words or command, and the final absence is epistemic fracture rather than a causal claim.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:17:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-018",
    "scope": "chapter",
    "chapter_numbers": [18],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Chapter 18 POV clarity, Mara Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-018-clean-silence.md", "start_line": 60, "end_line": 80, "note": "Mara distinguishes outgoing proof, ongoing reception, and absent effect evidence before ending on clean uncertainty."}],
    "finding": "pass",
    "rationale": "Mara's disappointment exposes contact as motive without converting silence into proof. Bench transmission remains one later act, and the final uncertainty exactly performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:18:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-019",
    "scope": "chapter",
    "chapter_numbers": [19],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Chapter 19 POV clarity, Nia Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "start_line": 92, "end_line": 124, "note": "Nia separates possible reasons from remembered causes and reaches the same blank place from both directions."}],
    "finding": "pass",
    "rationale": "Nia refuses both intuition and foreign-origin shortcuts. Her self-auditing sequence preserves uncertainty and the final failed trace performs the Hook without withholding a fact she knows.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:19:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-020",
    "scope": "chapter",
    "chapter_numbers": [20],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Chapter 20 POV clarity, Mara Voice_Brief fidelity, continuity, DEC-007 restraint, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "start_line": 85, "end_line": 112, "note": "Mara enters only temporal proximity, identifies guilt as appetite, and ends on her unsupported desire for centrality."}],
    "finding": "pass",
    "rationale": "The chapter begins Mara's high private conviction while explicitly denying it instrument, witness, or fact authority. The confession impulse remains characterization, not revelation, and the self-implicating final beat performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:20:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-021",
    "scope": "chapter",
    "chapter_numbers": [21],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 21 POV clarity, Nia Voice_Brief fidelity, continuity, reveal advancement, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-021-reconstruction.md", "start_line": 120, "end_line": 162, "note": "Nia refuses invented origins, signs responsibility separately from origin, and finds no beginning after complete reconstruction."}],
    "finding": "pass",
    "rationale": "Nia owns the casualty half without knowing the source match. The chapter fairly advances the reveal, preserves her agency and uncertainty, and the exhausted reconstruction performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:21:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-022",
    "scope": "chapter",
    "chapter_numbers": [22],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 22 POV clarity, Julian Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-022-fundable.md", "start_line": 95, "end_line": 120, "note": "Julian keeps retroactive authorization out of the proposal while the schedule outruns unresolved science."}],
    "finding": "pass",
    "rationale": "Julian's document-centered complicity remains distinct from Mara and Nia. He knows no casualty or handshake, and the proposal's finished schedule supplies a materially different institutional Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:22:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-023",
    "scope": "chapter",
    "chapter_numbers": [23],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 23 POV clarity, Mara Voice_Brief fidelity, continuity, fair reveal, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 65, "end_line": 85, "note": "Nia's independent sequence and pre-contact records verify shared identity while keeping December and the later bench path distinct."}, {"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 101, "end_line": 122, "note": "Mara labels her belief as hers, exposes her confession as self-centralizing, and ends by asking Nia to carry it."}],
    "finding": "pass",
    "rationale": "Current prose must release the verified identity here because Mara plainly knows it; `ARC-CHANGE-DISCOVERY-001` now records that fair release. The chapter still withholds only causation, which Mara does not know, and its self-indicting final beat performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:23:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-024",
    "scope": "chapter",
    "chapter_numbers": [24],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 24 POV clarity, Nia Voice_Brief fidelity, continuity, refusal ownership, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia tests both unsupported stories, rejects appropriation and case-zero reduction, and gives Mara no absolution."}],
    "finding": "pass",
    "rationale": "The microchapter belongs to Nia even though Chapter 23 released identity. She owns the meaning of the injury, refuses both origins, and ends on an exact boundary rather than a softened exchange.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:24:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-025",
    "scope": "chapter",
    "chapter_numbers": [25],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 25 POV clarity, Mara Voice_Brief fidelity, continuity, DEC-007 restraint, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "start_line": 74, "end_line": 120, "note": "Mara records effect as indeterminate, separates the two entries, retains private belief, and obeys Nia's boundary."}],
    "finding": "pass",
    "rationale": "Mara neither abandons nor promotes her conviction. The chapter gives Nia's instruction practical consequence without treating compliance as forgiveness or repair, and the final action performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:25:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-026",
    "scope": "chapter",
    "chapter_numbers": [26],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Chapter 26 POV clarity, Julian Voice_Brief fidelity, continuity, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 72, "end_line": 98, "note": "Julian's containment notice arrives after distributed knowledge and ends on who did not control disclosure."}],
    "finding": "pass",
    "rationale": "Version history, recipient logs, and late containment are recognizably Julian's. He remains ignorant of Nia and the bench act, while the final external-knowledge reversal performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:26:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-027",
    "scope": "chapter",
    "chapter_numbers": [27],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Chapter 27 POV clarity, Mara Voice_Brief fidelity, continuity, technical-consequence staging, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "start_line": 55, "end_line": 92, "note": "Nia's bounded terms govern the test; the receive address becomes a write condition, and Mara recognizes the door runs inward."}],
    "finding": "pass",
    "rationale": "Controls never substitute for consent or wisdom. The capability escalation changes authorization and bodily risk immediately, remains a temporary uncalibrated path, and the inward-door realization performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:27:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-028",
    "scope": "chapter",
    "chapter_numbers": [28],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Chapter 28 POV clarity, Nia Voice_Brief fidelity, continuity, human consequence, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-028-named-second.md", "start_line": 89, "end_line": 122, "note": "Nia limits the result, describes action-before-recognition without passivity, and names the live condition second."}],
    "finding": "pass",
    "rationale": "Nia owns consent, cutoff, correction, and interpretation. The test gives the earlier injury a possible mechanism but no origin, and the final naming order performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:28:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-LOCAL-029",
    "scope": "chapter",
    "chapter_numbers": [29],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Chapter 29 POV clarity, Mara Voice_Brief fidelity, continuity, movement turn, and Hook effectiveness",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 35, "end_line": 58, "note": "Mara records both origin accounts as unsupported and keeps private conviction non-admissible."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 81, "end_line": 92, "note": "The physical lock answers no field boundary and the final uninvited crossing turns Discovery into Private Defense."}],
    "finding": "pass",
    "rationale": "The chapter converts controlled capability into a boundary problem without resolving sender or handshake causation. The final mechanical lock is inadequate but humanly coherent, and the crossing reversal performs both Hook and movement turn.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:29:00Z",
    "resolution": null
  }
]
```

### Current drafting-batch findings

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-BATCH-001-005",
    "scope": "batch",
    "chapter_numbers": [1, 2, 3, 4, 5],
    "batch_id": "BATCH-DISCOVERY-001-005-RECONCILIATION",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, tenderness, restraint, emotional truth, human cost, technical consequence, originality, and Refused_Swell consistency",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-001-noise-floor.md", "start_line": 35, "end_line": 46, "note": "Mara's receive-only uncertainty turns into a control."}, {"path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "start_line": 34, "end_line": 46, "note": "Nia contributes continuous lived sequence rather than replay."}, {"path": "chapters/discovery-part/discovery-part-005-not-a-message.md", "start_line": 45, "end_line": 60, "note": "Technical success becomes unconsented overhearing and a bounded disclosure choice."}],
    "finding": "pass",
    "rationale": "The opening reconciliation retains the corrected calibration prose. Every POV change adds knowledge or moral pressure, the two Cross Cuts remain nonredundant, endings vary across experiment, memory, question, ordinary closure, and disclosure, and human cost prevents technical wonder from swelling into triumph or imitation.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:31:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-BATCH-011-015",
    "scope": "batch",
    "chapter_numbers": [11, 12, 13, 14, 15],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, tenderness, restraint, emotional truth, human cost, technical consequence, originality, and Refused_Swell consistency",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "start_line": 65, "end_line": 80, "note": "Field hypothesis and limited claim."}, {"path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "start_line": 78, "end_line": 92, "note": "Nia restores labor and privacy to the same interval."}, {"path": "chapters/discovery-part/discovery-part-014-rights-before-names.md", "start_line": 82, "end_line": 102, "note": "Person-specific proof produces immediate rights consequence."}],
    "finding": "pass",
    "rationale": "The two Cross Cuts move experiment to lived labor and lock to rights exposure without replay. Hook functions vary across conceptual reversal, evidentiary absence, reacquisition, knowledge entry, and institutional possession. The long proof is earned, every capability changes a person's legal position, and no voice or scene imitates a named novelist.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:32:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-BATCH-016-020",
    "scope": "batch",
    "chapter_numbers": [16, 17, 18, 19, 20],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, tenderness, restraint, emotional truth, human cost, technical consequence, originality, and Refused_Swell consistency",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-016-come-in.md", "start_line": 13, "end_line": 60, "note": "Separate content-free send and unilateral boundary."}, {"path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "start_line": 37, "end_line": 45, "note": "Nia's wanting has no words and changes a scarce human decision."}, {"path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "start_line": 85, "end_line": 112, "note": "Mara's guilt remains unsupported and self-centralizing."}],
    "finding": "pass",
    "rationale": "The temporal braid is legible without causal assertion; clean instrument silence and Nia's missing reason form a second nonconfirming handoff. Pacing expands only for the two-call consequence, hooks vary in kind, the single death remains human rather than spectacle, and no narrator converts chronology into proof or victory.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:33:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-BATCH-021-025",
    "scope": "batch",
    "chapter_numbers": [21, 22, 23, 24, 25],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, tenderness, restraint, emotional truth, human cost, reveal fairness, originality, and Refused_Swell consistency",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-021-reconstruction.md", "start_line": 120, "end_line": 162, "note": "Nia owns responsibility and uncertainty."}, {"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 65, "end_line": 122, "note": "Mara fairly releases verified identity and exposes confession as appropriation."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia owns refusal without replay or absolution."}],
    "finding": "pass",
    "rationale": "After `ARC-CHANGE-DISCOVERY-001`, the shared identity releases exactly where Mara knows it and Chapter 24 owns meaning rather than concealing fact. The delayed and contradiction cuts add distinct positions; the microchapter refuses explanatory aftermath; tenderness respects Nia's authority; and no confession, record, or technical belief supplies absolution or closure.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:34:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-BATCH-026-029",
    "scope": "batch",
    "chapter_numbers": [26, 27, 28, 29],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "POV transition value, Cross Cut clarity, pacing, Hook variety, tenderness, restraint, emotional truth, human cost, technical consequence, originality, and Refused_Swell consistency",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 72, "end_line": 98, "note": "Julian proves containment already lost."}, {"path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "start_line": 55, "end_line": 92, "note": "Mara ties capability to Nia's bounded terms and bodily risk."}, {"path": "chapters/discovery-part/discovery-part-028-named-second.md", "start_line": 89, "end_line": 122, "note": "Nia owns effect interpretation and limits the result."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 81, "end_line": 92, "note": "Mara's lock cannot answer the field-scale crossing."}],
    "finding": "pass",
    "rationale": "The four viewpoints turns—external knowledge, controlled capability, lived effect, failed containment—each add material value. Cross Cuts are legible, hooks move through disclosure, reversal, recognition, and threshold, and the final turn is restrained boundary dread rather than triumph, renewed threat spectacle, or provenance closure.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:35:00Z",
    "resolution": null
  }
]
```

### Movement findings, including revision history

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-001",
    "scope": "movement",
    "chapter_numbers": [1, 3, 5, 11, 13, 15, 16, 17, 23, 27, 28, 29],
    "batch_id": null,
    "criterion": "Discovery canon beats and canon-limited testimony",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "start_line": 65, "end_line": 80, "note": "Mind-as-field is earned through limited observation."}, {"path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "start_line": 97, "end_line": 112, "note": "Somebody alive will find the channel without page-nine capability yet."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 35, "end_line": 58, "note": "The channel is addressable and both first-wanting origins remain unsupported."}],
    "finding": "pass",
    "rationale": "The movement dramatizes the mind as a field, an inward channel initially unknown, certainty of rediscovery, one later uninvited arrival, and addressability. Nia is both source and casualty, one real death occurs, and all testimony remains bounded by what each witness can know.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-002",
    "scope": "movement",
    "chapter_numbers": [26, 27, 28, 29],
    "batch_id": null,
    "criterion": "Movement turn from discovery into private defense",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 72, "end_line": 98, "note": "External knowledge makes containment late."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 81, "end_line": 92, "note": "The physical lock cannot govern an inward channel."}],
    "finding": "pass",
    "rationale": "The turn is causal and moral: addressability becomes demonstrated effect, containment is already lost, and Mara's inadequate lock creates the need for a private boundary without drafting the copper-room answer or Chapter 30+.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:41:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-003",
    "scope": "movement",
    "chapter_numbers": [13, 16],
    "batch_id": null,
    "criterion": "Discovery motif progression",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "start_line": 123, "end_line": 142, "note": "MOT-CHAIN-01 turns spectrum into intimate bodily address without transmission."}, {"path": "chapters/discovery-part/discovery-part-016-come-in.md", "start_line": 45, "end_line": 60, "note": "MOT-COME-01 is a non-crossing thought attached to a unilateral content-free send."}],
    "finding": "pass",
    "rationale": "Both ledgered events gain distinct dramatic functions and no incidental copper foreshadowing is promoted. The chain begins in passive reception; invitation then exposes the missing boundary, preparing rather than spending later conditional entry.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:42:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-004",
    "scope": "movement",
    "chapter_numbers": [1, 2, 6, 7, 11, 12, 14, 17, 20, 22, 26, 28],
    "batch_id": null,
    "criterion": "POV distinction, Voice_Brief fidelity, transition Material_Narrative_Value, and prose originality",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "start_line": 78, "end_line": 92, "note": "Nia renders labor through route, breath, and timestamp."}, {"path": "chapters/discovery-part/discovery-part-014-rights-before-names.md", "start_line": 82, "end_line": 102, "note": "Julian renders complicity through document circulation and future review."}, {"path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "start_line": 85, "end_line": 112, "note": "Mara renders guilt through instrument limits and self-centralizing abstraction."}],
    "finding": "pass",
    "rationale": "Mara's analytic experiment-consequence register, Nia's dispatch sequence and self-audit, and Julian's qualified documentary chamber remain distinct across 29 chapters. Every transition changes knowledge, moral pressure, or institutional position. The prose has an original project-specific manner and does not imitate any named novelist's sentence-level voice, scenes, or phrasing.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:43:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-005",
    "scope": "movement",
    "chapter_numbers": [1, 2, 3, 4, 7, 8, 11, 12, 13, 14, 16, 17, 18, 19, 21, 23, 24, 26, 27, 28, 29],
    "batch_id": null,
    "criterion": "Cross Cut legibility without redundant replay",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "start_line": 65, "end_line": 80, "note": "Mara reads structure but not call content."}, {"path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "start_line": 78, "end_line": 92, "note": "Nia supplies the private labor, not Mara's measurement."}, {"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 101, "end_line": 122, "note": "Mara's confession position."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia's refusal position without replaying Mara's arrival."}],
    "finding": "pass",
    "rationale": "All eleven declared relations are readable and reciprocal in effect. Sensory matches add lived ownership, temporal braids preserve order without cause, causal cuts move capability into consequence, delayed returns add verified identity, and contradiction cuts preserve incompatible human positions without repeating scenes.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:44:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-006-REVISION",
    "scope": "movement",
    "chapter_numbers": [21, 23, 24],
    "batch_id": null,
    "criterion": "Reveal fairness and rejection of artificial withholding",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 65, "end_line": 85, "note": "Mara necessarily verifies and states the shared identity before Chapter 24."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia owns refusal and interpretation, not first factual disclosure."}],
    "finding": "revision",
    "rationale": "Current prose fairly releases the verified shared identity in Chapter 23, but REVEAL-NIA-SOURCE-CASUALTY recorded POV-NIA and Chapter 24. Making Mara suppress her verified knowledge would be coy and would contradict the design's ban on artificial withholding.",
    "requested_action": "Align the Reveal owner and reader release with Mara's Chapter 23 verification while explicitly preserving Nia's Chapter 24 ownership of refusal, injury interpretation, and causal uncertainty.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T02:00:00Z",
    "resolution": {
      "resolved_at": "2026-09-17T03:00:00Z",
      "action_taken": "Completed ARC-CHANGE-DISCOVERY-001: REVEAL-NIA-SOURCE-CASUALTY now releases through POV-MARA in Chapter 23; Chapter 24 remains Nia's refusal and neither origin account is promoted.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-006"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-006",
    "scope": "movement",
    "chapter_numbers": [21, 23, 24],
    "batch_id": null,
    "criterion": "Reveal fairness and rejection of artificial withholding after ARC-CHANGE-DISCOVERY-001",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-021-reconstruction.md", "start_line": 120, "end_line": 162, "note": "Nia advances the casualty half without Northline knowledge."}, {"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 65, "end_line": 122, "note": "Mara releases verified identity and exposes the limits of her belief."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia owns the contradiction cut and refuses origin closure."}],
    "finding": "pass",
    "rationale": "The plan now follows what each narrator actually knows. Verified identity lands in Chapter 23 without false coyness; Nia's Chapter 24 remains indispensable because it changes ownership and meaning rather than delaying a fact. The later dispatch-log exoneration remains fairly withheld until Chapters 50–55 because the logs are not yet available.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:45:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-007",
    "scope": "movement",
    "chapter_numbers": [1, 2, 5, 9, 12, 15, 16, 17, 20, 22, 24, 26, 28, 29],
    "batch_id": null,
    "criterion": "Hook performance and variety across Discovery",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-005-not-a-message.md", "start_line": 45, "end_line": 60, "note": "Disclosure decision."}, {"path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "start_line": 105, "end_line": 112, "note": "Institutional future-tense reversal."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 57, "end_line": 68, "note": "Boundary and refusal."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 81, "end_line": 92, "note": "Threshold and movement turn."}],
    "finding": "pass",
    "rationale": "Every final beat performs its header description. Pulls vary among test, sensory remainder, information reversal, decision, institutional consequence, absence, confession, refusal, recognition, and inadequate threshold action. Repetition of final phrasing provides testimony emphasis rather than a single manufactured-cliffhanger pattern.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:46:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-008",
    "scope": "movement",
    "chapter_numbers": [1, 2, 3, 4, 5, 6, 8, 10, 11, 13, 23, 25],
    "batch_id": null,
    "criterion": "Receive-only December source continuity and receiver-offset clarity",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-003-the-failed-check.md", "start_line": 18, "end_line": 51, "note": "Acquisition remains continuous; eight seconds belong after timestamped acquisition under tested settings; no transmit stage exists."}, {"path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "start_line": 18, "end_line": 38, "note": "Nia's road call, crossing, handover, and console form an unbroken source sequence."}, {"path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "start_line": 21, "end_line": 44, "note": "Julian independently audits the absent exciter, driver, and outward feed."}],
    "finding": "pass",
    "rationale": "The movement repeatedly and consistently keeps raw acquisition continuous, source experience gapless, and the reproducible eight seconds between acquisition and resolved output under one early configuration. No narrator treats it as transit time, a natural constant, or a December transmission.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:47:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-009",
    "scope": "movement",
    "chapter_numbers": [16, 18, 20, 23, 25, 27, 29],
    "batch_id": null,
    "criterion": "Later temporary bench-transmission separation from December reception",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-016-come-in.md", "start_line": 13, "end_line": 35, "note": "Mara explicitly adds visible synthesizer, attenuator, driver, relay, and load beside the unchanged receiver."}, {"path": "chapters/discovery-part/discovery-part-018-clean-silence.md", "start_line": 60, "end_line": 78, "note": "The act is one temporary path and one content-free envelope, not conversation or architecture."}, {"path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "start_line": 25, "end_line": 32, "note": "Mara keeps the December and handshake logs side by side but distinct in kind, evidence, and time."}],
    "finding": "pass",
    "rationale": "Every later write depends on deliberately added hardware and reuse of an address found by RECEIVE. The content-free handshake and controlled INTRUDE never retroactively supply December with an output stage, semantic payload, or pair calibration.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:48:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-010",
    "scope": "movement",
    "chapter_numbers": [15, 18, 26],
    "batch_id": null,
    "criterion": "April page-nine chronology and later-architecture separation",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "start_line": 97, "end_line": 101, "note": "Page nine explicitly does not exist and no Consortium transmitter has been proposed."}, {"path": "chapters/discovery-part/discovery-part-018-clean-silence.md", "start_line": 70, "end_line": 78, "note": "Mara calls the bench act one temporary path, not page-nine architecture that does not yet exist."}],
    "finding": "pass",
    "rationale": "Discovery foreshadows appetite and active-use liability without importing the April term sheet. Page nine remains a later architectural reveal and cannot function as evidence about December or Mara's one-off bench path.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:49:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-011",
    "scope": "movement",
    "chapter_numbers": [5, 8, 9, 11, 12, 13, 14, 16, 17, 20, 27, 28, 29],
    "batch_id": null,
    "criterion": "Technical scale attached immediately to human or institutional consequence",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "start_line": 65, "end_line": 80, "note": "Field hypothesis is limited to passive observation of someone's private attention."}, {"path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "start_line": 123, "end_line": 142, "note": "Person-specific lock becomes intimate address and rights exposure."}, {"path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "start_line": 55, "end_line": 92, "note": "Addressed write is bounded by Nia's consent and changes bodily risk."}, {"path": "chapters/discovery-part/discovery-part-028-named-second.md", "start_line": 89, "end_line": 122, "note": "Nia owns the effect as action-before-recognition rather than as a graph."}],
    "finding": "pass",
    "rationale": "Experiment-action-result-consequence staging governs the movement. Observation creates privacy debt, address creates legal exposure, a bench send creates a triage fear, and controlled write creates consent and self-trust consequences. No technical lecture is allowed to end before a person or institution must absorb the change.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:50:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-012",
    "scope": "movement",
    "chapter_numbers": [20, 21, 23, 24, 25, 28, 29],
    "batch_id": null,
    "criterion": "DEC-007 asymmetry without confirmation, appropriation, absolution, or archive validation",
    "prose_locations": [{"path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "start_line": 85, "end_line": 112, "note": "Mara's high conviction is guilt-shaped and unsupported."}, {"path": "chapters/discovery-part/discovery-part-023-the-match-holds.md", "start_line": 101, "end_line": 122, "note": "Mara's confession becomes a claim on Nia's injury."}, {"path": "chapters/discovery-part/discovery-part-024-not-case-zero.md", "start_line": 15, "end_line": 68, "note": "Nia refuses both stories, case-zero reduction, and absolution."}, {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 35, "end_line": 58, "note": "Later capability strengthens possibility but neither account becomes a finding."}],
    "finding": "pass",
    "rationale": "Mara remains highly convinced but non-authoritative; Nia accepts neither origin and keeps ownership; Julian does not yet possess the casualty facts and therefore cannot prematurely enter an adversary account. No instrument, narrator, test, record, or later capability confirms causation. Nia offers no forgiveness, and Mara's compliance does not become repair.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-17T03:51:00Z",
    "resolution": null
  }
]
```

### Current editorial gate results

```json record=GateResult schema=1
[
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-001-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [1], "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 1 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-001"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:01:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-002-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [2], "documents": ["chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 2 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-002"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:02:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-003-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [3], "documents": ["chapters/discovery-part/discovery-part-003-the-failed-check.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 3 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-003"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:03:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-004-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [4], "documents": ["chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 4 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-004"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:04:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-005-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [5], "documents": ["chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 5 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-005"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:05:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-011-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [11], "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 11 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-011"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:11:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-012-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [12], "documents": ["chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 12 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-012"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:12:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-013-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [13], "documents": ["chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 13 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-013"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:13:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-014-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [14], "documents": ["chapters/discovery-part/discovery-part-014-rights-before-names.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 14 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-014"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:14:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-015-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [15], "documents": ["chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 15 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-015"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:15:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-016-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [16], "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 16 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-016"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:16:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-017-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [17], "documents": ["chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 17 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-017"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:17:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-018-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [18], "documents": ["chapters/discovery-part/discovery-part-018-clean-silence.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 18 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-018"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:18:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-019-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [19], "documents": ["chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 19 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-019"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:19:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-020-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [20], "documents": ["chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 20 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-020"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:20:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-021-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [21], "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 21 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-021"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:21:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-022-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [22], "documents": ["chapters/discovery-part/discovery-part-022-fundable.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 22 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-022"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:22:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-023-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [23], "documents": ["chapters/discovery-part/discovery-part-023-the-match-holds.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 23 editorial approval gate after ARC-CHANGE-DISCOVERY-001."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-023"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:23:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-024-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [24], "documents": ["chapters/discovery-part/discovery-part-024-not-case-zero.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 24 editorial approval gate after ARC-CHANGE-DISCOVERY-001."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-024"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:24:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-025-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [25], "documents": ["chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 25 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-025"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:25:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-026-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [26], "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 26 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-026"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:26:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-027-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [27], "documents": ["chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 27 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-027"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:27:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-028-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [28], "documents": ["chapters/discovery-part/discovery-part-028-named-second.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 28 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-028"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:28:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-DISCOVERY-029-MOVEMENT-RERUN", "gate_type": "editorial", "scope": {"chapter_numbers": [29], "documents": ["chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter 29 editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-029"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:29:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-001-005-RECONCILIATION", "gate_type": "editorial", "scope": {"chapter_numbers": [1, 2, 3, 4, 5], "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 Discovery opening reconciliation batch editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-001", "EDITORIAL-DISCOVERY-LOCAL-002", "EDITORIAL-DISCOVERY-LOCAL-003", "EDITORIAL-DISCOVERY-LOCAL-004", "EDITORIAL-DISCOVERY-LOCAL-005", "EDITORIAL-DISCOVERY-BATCH-001-005"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:31:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-011-015", "gate_type": "editorial", "scope": {"chapter_numbers": [11, 12, 13, 14, 15], "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "chapters/discovery-part/discovery-part-014-rights-before-names.md", "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapters 11-15 drafting-batch editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-011", "EDITORIAL-DISCOVERY-LOCAL-012", "EDITORIAL-DISCOVERY-LOCAL-013", "EDITORIAL-DISCOVERY-LOCAL-014", "EDITORIAL-DISCOVERY-LOCAL-015", "EDITORIAL-DISCOVERY-BATCH-011-015"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:32:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-016-020", "gate_type": "editorial", "scope": {"chapter_numbers": [16, 17, 18, 19, 20], "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "chapters/discovery-part/discovery-part-018-clean-silence.md", "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapters 16-20 drafting-batch editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-016", "EDITORIAL-DISCOVERY-LOCAL-017", "EDITORIAL-DISCOVERY-LOCAL-018", "EDITORIAL-DISCOVERY-LOCAL-019", "EDITORIAL-DISCOVERY-LOCAL-020", "EDITORIAL-DISCOVERY-BATCH-016-020"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:33:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-021-025", "gate_type": "editorial", "scope": {"chapter_numbers": [21, 22, 23, 24, 25], "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapters 21-25 drafting-batch editorial approval gate after ARC-CHANGE-DISCOVERY-001."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-021", "EDITORIAL-DISCOVERY-LOCAL-022", "EDITORIAL-DISCOVERY-LOCAL-023", "EDITORIAL-DISCOVERY-LOCAL-024", "EDITORIAL-DISCOVERY-LOCAL-025", "EDITORIAL-DISCOVERY-BATCH-021-025", "EDITORIAL-DISCOVERY-MOVEMENT-006"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:34:00Z"},
  {"gate_result_id": "GATE-EDITORIAL-BATCH-DISCOVERY-026-029", "gate_type": "editorial", "scope": {"chapter_numbers": [26, 27, 28, 29], "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapters 26-29 drafting-batch editorial approval gate."}, "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-026", "EDITORIAL-DISCOVERY-LOCAL-027", "EDITORIAL-DISCOVERY-LOCAL-028", "EDITORIAL-DISCOVERY-LOCAL-029", "EDITORIAL-DISCOVERY-BATCH-026-029"], "result": "pass", "checker_exit_status": null, "timestamp": "2026-09-17T04:35:00Z"},
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-MOVEMENT-001",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
      "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "chapters/discovery-part/discovery-part-008-provisional-identity.md", "chapters/discovery-part/discovery-part-009-appetite-before-result.md", "chapters/discovery-part/discovery-part-010-no-form-for-this.md", "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "chapters/discovery-part/discovery-part-014-rights-before-names.md", "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "chapters/discovery-part/discovery-part-016-come-in.md", "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "chapters/discovery-part/discovery-part-018-clean-silence.md", "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.7 final Discovery_Part movement Editorial_Gate after resolving the sole Reveal-planning revision through ARC-CHANGE-DISCOVERY-001. All current chapter, batch, and movement findings pass; no Chapter 30+ prose is in scope."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-LOCAL-001", "EDITORIAL-DISCOVERY-LOCAL-002", "EDITORIAL-DISCOVERY-LOCAL-003", "EDITORIAL-DISCOVERY-LOCAL-004", "EDITORIAL-DISCOVERY-LOCAL-005", "EDITORIAL-DISCOVERY-006-010-001", "EDITORIAL-DISCOVERY-006-010-002", "EDITORIAL-DISCOVERY-006-010-003", "EDITORIAL-DISCOVERY-006-010-004", "EDITORIAL-DISCOVERY-006-010-005", "EDITORIAL-DISCOVERY-LOCAL-011", "EDITORIAL-DISCOVERY-LOCAL-012", "EDITORIAL-DISCOVERY-LOCAL-013", "EDITORIAL-DISCOVERY-LOCAL-014", "EDITORIAL-DISCOVERY-LOCAL-015", "EDITORIAL-DISCOVERY-LOCAL-016", "EDITORIAL-DISCOVERY-LOCAL-017", "EDITORIAL-DISCOVERY-LOCAL-018", "EDITORIAL-DISCOVERY-LOCAL-019", "EDITORIAL-DISCOVERY-LOCAL-020", "EDITORIAL-DISCOVERY-LOCAL-021", "EDITORIAL-DISCOVERY-LOCAL-022", "EDITORIAL-DISCOVERY-LOCAL-023", "EDITORIAL-DISCOVERY-LOCAL-024", "EDITORIAL-DISCOVERY-LOCAL-025", "EDITORIAL-DISCOVERY-LOCAL-026", "EDITORIAL-DISCOVERY-LOCAL-027", "EDITORIAL-DISCOVERY-LOCAL-028", "EDITORIAL-DISCOVERY-LOCAL-029", "EDITORIAL-DISCOVERY-BATCH-001-005", "EDITORIAL-DISCOVERY-006-010-006", "EDITORIAL-DISCOVERY-006-010-007", "EDITORIAL-DISCOVERY-BATCH-011-015", "EDITORIAL-DISCOVERY-BATCH-016-020", "EDITORIAL-DISCOVERY-BATCH-021-025", "EDITORIAL-DISCOVERY-BATCH-026-029", "EDITORIAL-DISCOVERY-MOVEMENT-001", "EDITORIAL-DISCOVERY-MOVEMENT-002", "EDITORIAL-DISCOVERY-MOVEMENT-003", "EDITORIAL-DISCOVERY-MOVEMENT-004", "EDITORIAL-DISCOVERY-MOVEMENT-005", "EDITORIAL-DISCOVERY-MOVEMENT-006", "EDITORIAL-DISCOVERY-MOVEMENT-007", "EDITORIAL-DISCOVERY-MOVEMENT-008", "EDITORIAL-DISCOVERY-MOVEMENT-009", "EDITORIAL-DISCOVERY-MOVEMENT-010", "EDITORIAL-DISCOVERY-MOVEMENT-011", "EDITORIAL-DISCOVERY-MOVEMENT-012"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-17T04:40:00Z"
  }
]
```

## `DEC-018` revision-pass review of delivered Chapters 1–46

Author-commissioned craft review, completed 2026-09-18, of the delivered manuscript — Chapters 1–46 plus the calibration Chapters 73, 118, and 124. The reviewer identity on every record below is an author-commissioned agent reading rather than an author reread, recorded honestly for the same reason the calibration records are.

The result is nine `revision` findings and no passes. That is a heavier verdict than any earlier gate in this log, and it deliberately contradicts several current passes rather than quietly replacing them. `EDITORIAL-DISCOVERY-MOVEMENT-007` read the repeated final-line phrasing as testimony emphasis and passed hook performance across Discovery; `EDITORIAL-DISCOVERY-MOVEMENT-004` and `EDITORIAL-CAL-013` passed POV distinctness and sentence-making; `EDITORIAL-CAL-011` passed tenderness, human cost, and emotional truth. Those findings stay in the audit trail exactly as written. They were honest readings of five to twenty-nine chapters at a time. Across forty-nine delivered files the same features stop reading as emphasis and start reading as a template, which is a judgment only the larger scope could reach.

The author has directed that all nine findings be fixed, and `DEC-018` records the binding craft rules the fixes are measured against. Every criterion below is a human Editorial_Gate criterion carrying no automated score, under global invariant 25 of [`arc-outline.md`](arc-outline.md) and Requirement 12.12. No numeric craft score appears in any record here; chapter numbers, line ranges, and Prose_Word counts locate and size evidence rather than rating it.

Three of the nine findings correct the brief that commissioned them, and the corrections are recorded in the rationales rather than smoothed over: the closed-loop shape extends to Chapters 43–46 and not only 30–42; the dissolved-irony defect belongs to the `contradiction-cut` pairs 32/34, 40/42, and 44/45, because 33/35 is declared a `causal-cut`; and the technician in Chapter 30 already held Character ID `CHAR-011` before this pass, so his canon addition is a surname and a consequence rather than a new identity.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-REVISION-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 33, 34, 35, 37, 39, 42, 43, 45, 46],
    "batch_id": null,
    "criterion": "Closed-loop chapter shape: thesis openings and final lines that restate the ArcEntry hook",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 112, "end_line": 114, "note": "Final line 'I began drawing a cage a few pages after I had drawn the door.' against the header hook 'She turns back to the notebook that found the field and begins drawing a cage in it, a few pages after the door.'"},
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 12, "end_line": 14, "note": "Opening 'I separated the matter into three acts because the documents kept trying to make them one.' states the chapter's whole argument before any scene begins."},
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 114, "end_line": 116, "note": "Final line 'The enrollment form had already answered on everyone's behalf.' against the hook's 'the enrollment form he is handed has already answered it on everyone's behalf.'"},
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 92, "end_line": 94, "note": "Final two lines reproduce both halves of the hook, including the phrase 'settle a question it could not reach'."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 106, "end_line": 108, "note": "Final line 'That was how I knew the thing that took my judgment was not one.' against the hook's 'which is how she knows the thing that took her judgment was not one.'"},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 102, "end_line": 104, "note": "Final line 'The protection I had negotiated was a careful sentence about a thing that could not be switched off.' against the hook's 'a careful sentence about a thing that cannot be switched off.'"}
    ],
    "finding": "revision",
    "rationale": "Every delivered chapter from 30 to 46 closes on a restatement of its own header hook, and most open on a sentence that states the chapter's conclusion. The final line is frequently reconstructible from the ArcEntry alone, which means the prose is labelling itself rather than ending. The consequence is architectural rather than local: a unit that announces its thesis and then restates it has closed, so nothing crosses the chapter boundary and the rotation loses its pull. This corrects the commissioning brief in one respect and worsens the count. The pattern is not confined to 30-42: Chapters 43, 44, 45, and 46 do it too, so it is seventeen of seventeen delivered Private_Defense chapters rather than thirteen of thirteen, and the same shape is visible in Discovery.",
    "requested_action": "Under DEC-018 clauses 1 and 2, rewrite every delivered chapter's first and last sentence. Openings begin inside action, sensation, object, or speech whose significance is not yet named. Closings may not restate, paraphrase, or near-verbatim echo the ArcEntry hook; the hook stays planning metadata and never appears as prose. Where the current final line is the only statement of a needed fact, move that fact earlier and end on its consequence instead.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:00:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-002",
    "scope": "manuscript",
    "chapter_numbers": [1, 34, 35, 37, 42, 46],
    "batch_id": null,
    "criterion": "Forward pressure: legitimate dread and reluctant retrospection, distinct from artificial withholding",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-001-noise-floor.md", "start_line": 14, "end_line": 14, "note": "The authorized model: 'That is the sentence I would take back if I were allowed one.' It conceals no fact Mara holds and promises a cost. Nothing like it recurs across the following forty-five chapters."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 88, "end_line": 92, "note": "The chapter answers its own question in its last three lines and leaves nothing owed to the next chapter."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 116, "end_line": 118, "note": "A genuine unanswered arrival at the gate is immediately resolved into a summary statement about what the arrivals are for."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 100, "end_line": 104, "note": "Julian names the exhaustion of his own options and closes on it, so the movement's largest reversal generates no obligation."}
    ],
    "finding": "revision",
    "rationale": "The manuscript discloses where it should also press. It is correct to forbid artificial withholding, and ARC-CHANGE-DISCOVERY-001 was right to align the reveal with what Mara actually knows in Chapter 23. But the same discipline has been applied until legitimate dread disappeared with the coyness. Chapter 1 shows the register the book is entitled to and then abandons it: a retrospective first-person narrator may signal that a decision cost something without naming the later fact, and that costs the reader no information at all. Chapter 35 is the clearest waste. An unrecognized car at the gate with no entry on Mara's calendar is real dread, and the chapter spends it in one sentence of summary before the boundary.",
    "requested_action": "Under DEC-018 clauses 3 and 4, give every chapter at least one question that survives its boundary, generated by consequence, obligation, dread, or a fixed-time event, and restore reluctant retrospection on the Chapter 1 model. Requirements 2.13 and 2.14 and the DEC-016 question-gap limit are unchanged: no narrator may withhold a fact they hold, and no more than two adjacent chapters may end on a question-gap.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:05:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-003",
    "scope": "manuscript",
    "chapter_numbers": [32, 34, 40, 42, 44, 45],
    "batch_id": null,
    "criterion": "Dramatic irony in declared contradiction-cut relationships",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 76, "end_line": 80, "note": "Nia states the CUT-SEALED-ROOM-AND-A-LIFE contradiction directly: safety is purchased by removing the decisions that could matter to anyone else."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 88, "end_line": 92, "note": "'I could be safe or I could take the call. / The room was very clear that I could not do both.' The cross-cut's shared consequence is delivered as a conclusion rather than assembled from two positions."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 100, "end_line": 108, "note": "Nia states the CUT-CALIBRATION-AND-THE-UNCALIBRATED contrast in her own prose: she can now describe a consented sentence, which is how she knows the thing that took her judgment was not one."}
    ],
    "finding": "revision",
    "rationale": "A contradiction-cut exists so that two accounts stand side by side and the reader carries the incompatibility neither narrator can see. Where the participating narrator states the contradiction, the architecture has been spent and the second chapter becomes a summary of the relationship rather than one side of it. The declarations are precise about this. CUT-SEALED-ROOM-AND-A-LIFE says the decision that keeps the room a room is the decision that makes it unusable, and Chapter 34 says exactly that in its own voice. CUT-CALIBRATION-AND-THE-UNCALIBRATED says the vocabulary gives them no evidence about origin, and Chapter 42 states the comparison outright. Two corrections to the commissioning brief belong here. The affected pairs are 32/34, 40/42, and 44/45; Chapters 33 and 35 are joined by CUT-CONSENT-AS-DEFAULT, which is declared a causal-cut, so 35 is not part of this finding. Sixteen contradiction-cut relationships exist across the outline, so the criterion has scope well beyond the delivered range.",
    "requested_action": "Under DEC-018 clause 5, remove every explicit statement of the contradiction from the participating narrators in 32/34, 40/42, and 44/45, leaving each chapter to hold only its own position. Preserve the declared replay_boundary of each record: the fix is subtraction from the second chapter, not new material in the first, and no CrossCut record changes.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:10:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-004",
    "scope": "manuscript",
    "chapter_numbers": [30, 34, 39, 42, 118],
    "batch_id": null,
    "criterion": "POV distinctness: shared syntax, shared tics, and voice separation carried by vocabulary alone",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 68, "end_line": 72, "note": "Mara: 'No words had crossed. No proposition had arrived. No voice had used my name.'"},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 12, "end_line": 16, "note": "Nia: 'No live console. No radio. No county network.'"},
      {"path": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "start_line": 54, "end_line": 58, "note": "Julian: 'No default recording. No inferred consent from use. No transfer of calibration.'"},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 36, "end_line": 40, "note": "Nia again: 'There had been no sentence. No voice. No proposition. No partner. No current answer.'"},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "Safiya's register is the target quality: second-person address to a listener in the room, a paper map, a kettle with a whistle, and a private word arriving inside an ordinary errand."}
    ],
    "finding": "revision",
    "rationale": "Mara, Nia, and Julian share one sentence-making habit and are separated only by domain nouns. Each of the three uses the same enumerated-absence construction, a run of short negative sentences standing alone; it appears eleven times across the delivered files and in all three registers, and it is doing the work of a shrug rather than of an absence. All three also default to the isolated one-sentence paragraph and to a terminal epigram, so their chapters have the same shape on the page regardless of whose head they are in. Safiya's single delivered chapter is the counterexample and the standard: her syntax, her address to a listener, and what she chooses to notice are hers, and none of it depends on specialist vocabulary. EDITORIAL-DISCOVERY-MOVEMENT-004 and EDITORIAL-CAL-013 passed distinctness at movement and calibration scope and were reasonable at that scope; the manuscript-scope reading reverses them.",
    "requested_action": "Under DEC-018 clauses 6 and 7, cut the enumerated-absence construction to at most one instance per chapter and only where that absence is the chapter's subject; ration the terminal aphorism; and rebuild separation from syntax, rhythm, paragraph shape, and what each narrator notices rather than from domain vocabulary. Safiya's Chapter 118 register is the reference for distinctness, not a register for the others to copy. Voice Brief guidance itself needs no change: the briefs already specify distinct registers that the prose is not delivering.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:15:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-005",
    "scope": "manuscript",
    "chapter_numbers": [34, 36, 38, 41],
    "batch_id": null,
    "criterion": "Human cost, tenderness, and warmth: leads rendered flatter than the supporting cast",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 38, "end_line": 42, "note": "The warmest and funniest beat in the delivered manuscript belongs to two non-viewpoint characters: 'Lena laughed before she spoke. \"You said the left chair squeaks.\"'"},
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 70, "end_line": 78, "note": "Tomas and Cora get the only unguarded human exchange and the only domestic object used for comfort: 'Cora drank half a cup of cold coffee.'"},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 12, "end_line": 16, "note": "Nia brings water and lunch into the copper room and eats alone, and the meal is an instrument of self-audit rather than a pleasure."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 12, "end_line": 16, "note": "Ada and Lena again carry the human interest, this time through the ordinary dignity of an invoice."}
    ],
    "finding": "revision",
    "rationale": "Across the delivered chapters no POV lead has a family on the page, shares a meal for pleasure, makes a joke that is not a professional riposte, or touches another person. The four leads narrate themselves as case files, and every warm or funny moment in the manuscript belongs to a non-viewpoint supporting character. That ordering is backwards: the reader is asked to carry a book about mental sovereignty through four people who are never shown having private lives worth protecting. Nia's lunch in Chapter 34 is the sharpest instance, because food is present and is converted immediately into evidence about her own reliability. EDITORIAL-CAL-011 passed tenderness and human cost on eight chapters; at manuscript scope the absence is structural rather than incidental.",
    "requested_action": "Under DEC-018 clause 9, give every movement at least one scene of non-professional warmth between named characters, one instance of food, rest, or physical comfort offered and accepted, and one instance of humor that is not a professional riposte, and ensure no POV lead is lonelier or flatter than the supporting cast. The DEC-018 supporting canon supplies CHAR-015 Joss Calder for Nia and CHAR-016 Ruth Venn for Mara. Julian receives no new relationship: his isolation is characterization, and clause 9 reaches him inside scenes he shares. Neither new relationship may become an exposition audience, a confession chamber, or a route to absolution.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:20:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-006",
    "scope": "manuscript",
    "chapter_numbers": [30, 35, 37, 43],
    "batch_id": null,
    "criterion": "Personal cost for the Anchor POV inside Discovery and Private_Defense",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 68, "end_line": 78, "note": "Mara's cost is entirely epistemic and entirely inside her own head; she notices that her relief makes Nia's injury useful and pays nothing for it."},
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 92, "end_line": 94, "note": "The chapter's reversal costs her a hypothesis rather than anything she can lose."},
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 54, "end_line": 54, "note": "The only concrete pressure in the delivered range is institutional: Northline rationing shield-mesh replacements and postponing tests that need a second technician after six. Nothing is charged to Mara personally."}
    ],
    "finding": "revision",
    "rationale": "Mara holds the largest chapter load in the book and, through Chapter 46, incurs no personal cost at all. Her guilt is abstract, her convictions are private, and her losses are her institution's. Every cost scheduled for her arrives later: the instruments at Chapter 55, the Mindwars accounting, and the shutdown at Chapter 112. That leaves seventy-five percent of the delivered manuscript resting on a protagonist who has not yet been charged for anything, which drains the moral weight from the very decisions the book exists to examine.",
    "requested_action": "Under DEC-018 clause 8, give Mara at least one personal, non-abstract cost inside Private_Defense, and confirm the same for every lead in every movement in which they hold chapters. The DEC-018 supporting canon supplies the Private_Defense cost: CHAR-011 Ravi Anand requests reassignment off the project because Mara entered his name on the exposed-persons list over his objection, and she continues the shielded-room programme without him. Keep it small and keep it hers. It must not collide with or pre-empt the Chapter 55 loss of instruments or the Chapter 112 shutdown, and Ravi's departure is not an injury, a casualty, or a consequence of the Foreign_Signal.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:25:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-007",
    "scope": "manuscript",
    "chapter_numbers": [30, 32, 35, 36],
    "batch_id": null,
    "criterion": "Dropped threads: the exposed-persons list and the car at the Northline Array gate",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 78, "end_line": 86, "note": "The exposed-persons list is established with three names, the technician objects, and he supplies the line 'Then everyone at Northline belongs there.' Neither the list nor the line returns anywhere."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 108, "end_line": 118, "note": "An unrecognized car, no Northline tag, an appointment with development, and nothing entered on Mara's calendar. The chapter ends there."},
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 12, "end_line": 14, "note": "The next chapter opens inside a Consortium demonstration room already arranged, and never refers to the arrival, the gate, the missing calendar entry, or who booked the visit."}
    ],
    "finding": "revision",
    "rationale": "Two of the strongest openings in Private_Defense are abandoned. The exposed-persons list is a genuine moral object: Mara writes down three people including one who objects, and the technician's answer that on that logic everyone at Northline belongs on the list is the sharpest challenge to her method in the movement. It is never mentioned again. The car at the gate is a bigger loss, because the reader is given a specific unanswered fact and then finds the next chapter standing inside the answer without noticing. A booked visit that appears on nobody's calendar in Mara's group is not a mystery to be dropped; it is an institutional fact about who may schedule access to Northline, and it is more damning for being ordinary.",
    "requested_action": "Develop both threads with the DEC-018 supporting canon, which now records what each of them is. The exposed-persons list is a pre-Trust private working record carrying no authority about causation, and the technician's objection has a consequence: CF-PRIVATE-EXPOSED-PERSONS-LIST, CF-PRIVATE-TECHNICIAN-REPORT, and CF-PRIVATE-TECHNICIAN-REASSIGNMENT. The car is the Open Channel Consortium advance party arriving to set up the Chapter 36 demonstration, booked through the institute's development group rather than Mara's, per CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY, with personnel consistent with Chapters 36 and 43. One correction to the commissioning brief: the technician is not unidentified. He already held Character ID CHAR-011 before this review, so the addition is the surname Anand plus a consequence, not a new character.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:30:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-008",
    "scope": "manuscript",
    "chapter_numbers": [36, 41, 118],
    "batch_id": null,
    "criterion": "Preparation for the Coda's emotional payload before Safiya's first chapter",
    "prose_locations": [
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "The book's emotional payload, carried by a character the reader meets at 115: the kettle, the private word she and her mother had for the sound it makes, and a layer that stayed usable while she remained."},
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 38, "end_line": 42, "note": "A private two-person idiom already exists on the page here, in the Ferris pair, and is never named as the kind of thing it is."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 12, "end_line": 16, "note": "The same pair again, with years of shared working practice, and again no recognition that such a layer is a thing that can be lost."}
    ],
    "finding": "revision",
    "rationale": "Chapters 115 to 128 carry the novel's emotional payload, and Safiya holds no chapter before 115. DEC-016 is right that her absence is what lets Chapter 118 land, and moving her earlier would either make her a bystander to her own injury or spend the subtraction before the Coda can receive it as testimony. The defect is not her entrance; it is that nothing prepares the ground for it. Chapter 118 has to introduce a category, establish that it can be lost, and grieve the loss in one account. Meanwhile the manuscript already has a private two-person layer on the page in the Ferris pair and never says what kind of thing it is, and it has no uncounted civilian loss anywhere before 118 to give the class weight.",
    "requested_action": "Do not move Safiya and do not add a Safiya chapter. Instead, establish the class in Private_Defense through Ada and Lena Ferris under CF-PRIVATE-TWO-PERSON-LAYER-CLASS, keeping their layer intact and drawing no connection between the Ferris pair and Safiya; and make the class of uncounted private civilian loss vivid inside Chapters 109 to 114, per the DEC-018 planning obligations now recorded in the Mindwars and Coda sections of arc-outline.md. That work proceeds without Safiya's POV, without entering her home, without naming or foreshadowing her particular loss, and without pre-empting REVEAL-SAFIYA-TUESDAY-LOSS, which still releases at 118 inside its unchanged 118-119 window with POV-SAFIYA as owner. DEC-003 is unweakened: heritage_base stays unspecified_by_author and no corpus of Safiya's layer exists anywhere.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:35:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-009",
    "scope": "manuscript",
    "chapter_numbers": [4, 24, 31, 34, 118],
    "batch_id": null,
    "criterion": "Chapter scale: scenes ending before they have earned their length, against the approved Final_Targets",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 24, "end_line": 28, "note": "The two-calls memory arrives, is named in five words, and is closed in the next line. The chapter's most loaded moment is given three short paragraphs."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 98, "end_line": 102, "note": "Nia's first measured silence, the largest experiential change in the movement, resolves into a two-line aphorism instead of being inhabited."},
      {"path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "start_line": 30, "end_line": 42, "note": "A chapter at the floor of the normal class, ending on an ordinary coat, with room for the human material it gestures at."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "The book's most important account is one of its shortest chapters."}
    ],
    "finding": "revision",
    "rationale": "The delivered chapters are systematically ending before their scenes are finished. Forty-five delivered chapters declare 41,020 Prose_Words for a mean of 912, which across 128 chapters projects roughly 117,000 against approved Final_Targets of 130,000 to 150,000. The objective total is the Manuscript_Checker's business and it already reports it; the craft judgment recorded here is what the shortfall is made of. It is not that the chapters are too short in the abstract. It is that loaded moments are named and then left: a remembered death gets a line, an hour of first quiet gets an epigram, and a Tuesday that carries the whole Coda gets fewer words than a due-diligence chapter. Chapters that state their thesis and restate their hook do not need length, which is why findings one and nine share a cause.",
    "requested_action": "Under DEC-018 clause 10, draft normal-class chapters into the 1,050 to 1,200 Prose_Word band with a planning mean near 1,125, and inhabit the loaded moments rather than padding around them. Microchapters and long-outliers keep the compression or expansion named in their outlier_purpose and are not inflated to reach a total. The 700-1,600 class band, the 2,500-word Hard_Chapter_Maximum, the 108-entry normal floor, the 20-outlier cap, and the 3,600-word same-POV run limit are unchanged.",
    "reviewer": "Author-commissioned craft review, author-delegated agent reading",
    "reviewed_at": "2026-09-18T09:40:00Z",
    "resolution": null
  }
]
```

### Editorial gate for the revision pass

One editorial gate covers the pass. It is `revision`, its `checker_exit_status` is `null` because editorial gates never carry one, and it does not supersede any earlier gate: `GATE-EDITORIAL-DISCOVERY-MOVEMENT-001`, the batch gates, and the calibration gate all remain in the audit trail as historical records of the state they evaluated. What this gate establishes is that the current delivered prose does not pass at manuscript scope, so no delivered chapter or batch may be treated as approved on the strength of an earlier gate once its prose changes under `DEC-018`.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-REVISION-PASS-001",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 73, 118, 124],
    "documents": ["planning/decisions.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/motif-ledger.md"],
    "description": "Author-commissioned DEC-018 craft review of the delivered manuscript: Chapters 1-46 plus calibration Chapters 73, 118, and 124. Nine revision findings, no passes. Scope covers the prose of all 49 delivered Chapter_Files and the planning documents that govern them; it evaluates craft only and makes no objective determination."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-REVISION-001", "EDITORIAL-REVISION-002", "EDITORIAL-REVISION-003", "EDITORIAL-REVISION-004", "EDITORIAL-REVISION-005", "EDITORIAL-REVISION-006", "EDITORIAL-REVISION-007", "EDITORIAL-REVISION-008", "EDITORIAL-REVISION-009"],
  "result": "revision",
  "checker_exit_status": null,
  "timestamp": "2026-09-18T09:45:00Z"
}
```

### What this gate does and does not decide

- It decides craft only. Objective facts about the delivered files remain the Manuscript_Checker's, and this gate waives none of them. Two are worth naming because they are visible in the same scope and are **not** editorial findings: Chapters 43 through 46 carry prose bodies while declaring `words: 0`, and their Chapter_Header status of `draft` disagrees with their `ArcEntry` status of `planned`. The checker reports both as errors at chapter scope. They belong to whichever wave finishes delivering those four chapters.
- It does not demote any chapter. Status changes belong to the waves that touch each file, under `ARC-CHANGE-REVISION-001`.
- It does not invalidate `VOICE-JULIAN.first_appearance_review`. That Requirement 5.11 review is carried by `EDITORIAL-DISCOVERY-006-010-001` on Chapter 6 and remains valid: none of the nine findings concerns Julian's first appearance, and revision under `DEC-018` does not change the fact that his register was established there.
- It creates no numeric score of any kind, and no `ArcEntry` or `ChapterHeader` field may be added to carry one.
