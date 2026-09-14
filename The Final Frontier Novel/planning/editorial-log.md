# Editorial Log

Schema version: **1**  
Normative schema: [`record-schemas.md`](record-schemas.md), especially `EditorialFinding` and `GateResult`  
Workflow authority: Requirements 10.7, 10.8, and 13.5–13.10; the design's Editorial and Delivery Flow

This document is the active project log for evidence-bearing human editorial findings and editorial gate decisions. It records qualitative judgment; it is not a scoring sheet and does not duplicate the Manuscript Checker's objective audit.

## Initialization state

**Active `EditorialFinding` records: 183. Active editorial `GateResult` records: 85.**

These totals were measured by parsing every typed fence in this file. The `DEC-021` policy repair added three findings and three editorial rerun gates, resolving the length-governance conflict, passing the expanded Chapter 118, and passing task 13.6. The subsequent voice-separation pass added twenty-nine current Discovery chapter findings, six Discovery batch findings, one repair follow-up, three movement findings, and `GATE-EDITORIAL-DISCOVERY-MOVEMENT-003`.

That movement gate is `revision`, and it is the honest state of the manuscript rather than a bookkeeping gap: every prerequisite is now complete and every criterion passes except `DEC-018` clause 7, where `POV-MARA` and `POV-NIA` still share one syntactic register. `EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE` scopes the remaining work and records why local sentence repairs cannot close it. Task 14 therefore remains blocked by a craft finding rather than by missing evidence.

The 2026-09-18 author-commissioned `DEC-018` craft review of delivered Chapters 1–46 plus calibration Chapters 73, 118, and 124 is recorded below, in [`DEC-018` revision-pass review of delivered Chapters 1–46](#dec-018-revision-pass-review-of-delivered-chapters-146). It adds nine `revision` findings and one `revision` editorial gate, and it deliberately reverses several earlier passes at a larger scope without editing them: every earlier finding and gate stays in the audit trail as the honest record of the state it evaluated.

The Chapters 56–61 task-13.5 review adds eight findings, six chapter editorial gates, and one batch editorial gate. The separate task-13.6 prerequisite audit adds one `incomplete` movement gate: it records missing earlier Private Defense coverage and unresolved movement-wide debt without representing the movement as approved.

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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Every delivered chapter's first and last sentence was rewritten during the DEC-018 revision wave. A direct check of all ten cited chapters found no thesis opening and no closing that restates its ArcEntry Hook; the four originally quoted final lines no longer exist in the prose.",
      "follow_up_finding_id": "EDITORIAL-REVISION-001-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Chapter 1's reluctant-retrospection register was preserved rather than restored, and every cited chapter now carries an obligation, dread, or consequence past its boundary. Chapter 35's abandoned car and Chapter 37's withheld report are the clearest cases: both leave a real unanswered fact without concealing anything either narrator holds.",
      "follow_up_finding_id": "EDITORIAL-REVISION-002-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "The explicit contradiction statements were removed from Chapters 34 and 42, which now hold only their own positions and dramatize the incompatibility through action. Chapter 45 retains Mara's recognition of the gap between clause and specification, and that retention is reasoned rather than overlooked, because she is holding both documents and suppressing her reading would be the artificial withholding this project forbids.",
      "follow_up_finding_id": "EDITORIAL-REVISION-003-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "The enumerated-absence construction was counted across the delivered files and now appears twice in Chapters 30 through 61 rather than eleven times, in each case where the absence is the chapter's subject. The criterion also caught a recurrence during this pass: the reserved reader-instruction formula had crossed into Julian's narration five times and was removed from Chapters 44, 49, and 53 under EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-001 and EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001.",
      "follow_up_finding_id": "EDITORIAL-REVISION-004-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Ruth Venn and Joss Calder were brought onto the page under CHAR-015 and CHAR-016, and warmth now appears across the movement in Chapters 30, 34, 38, 40, 42, and 43 through food offered and accepted, non-professional humour, and questions deliberately not asked. Neither relationship became an exposition audience or a route to absolution, and Julian received no new relationship, as the finding required.",
      "follow_up_finding_id": "EDITORIAL-REVISION-005-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Ravi Anand's departure was written as the Anchor's personal cost under CF-PRIVATE-TECHNICIAN-REASSIGNMENT: he objects in Chapter 30, asks for his name off the page in Chapter 35, files a handwritten transfer request in Chapter 40 that indicts Mara accurately, and the shielded-room programme drops to one qualified operator. The cost compounds in Chapter 48, where refusing the money also refuses the second operator, and it neither collides with nor pre-empts the Chapter 55 instrument loss.",
      "follow_up_finding_id": "EDITORIAL-REVISION-006-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Both threads were developed. The exposed-persons list is contested by Ravi at creation, dated and annotated at Nia's insistence in Chapter 31, carries his dated objection in Chapter 32, and produces his transfer in Chapter 40. The car at the gate is answered in Chapter 36 through the gate visitor book as the Consortium advance party booked by development, under CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY, with the point being that nobody needed Mara's permission.",
      "follow_up_finding_id": "EDITORIAL-REVISION-007-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "The private two-person layer class was established through Ada and Lena Ferris in Chapters 36 and 41 under CF-PRIVATE-TWO-PERSON-LAYER-CLASS, with their layer intact, no surviving corpus, and no connection of any kind drawn to Safiya. Safiya was not moved and no Safiya chapter was added. The second half of the requested action, making uncounted private civilian loss vivid inside Chapters 109 through 114, remains a forward planning obligation on undrafted chapters and is carried rather than closed.",
      "follow_up_finding_id": "EDITORIAL-REVISION-008-FOLLOWUP-001"
    }
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
    "resolution": {
      "resolved_at": "2026-09-13T21:32:24Z",
      "action_taken": "Chapters 1 through 49 were redrafted into the clause 10 band and the loaded moments the finding named are now inhabited rather than named, with Chapter 4 at 1,181 and Chapter 31 at 1,148 Prose_Words and Chapter 34's remembered death given a scene rather than a line. The manuscript projects roughly 143,900 Prose_Words across 128 chapters, inside Final_Targets. The finding does not close: Chapter 118 remains 756 Prose_Words and exploratory, which is the specific defect the finding identified, and thirteen normal chapters now sit outside the band in both directions.",
      "follow_up_finding_id": "EDITORIAL-REVISION-009-FOLLOWUP-001"
    }
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

## Chapters 50–55 review and repair pass

Task 13.4 delivered Chapters 50–55 as the record sequence: the softened April minutes, Mara's preservation demand and the founding of the Civic Record Trust, Nia's conditioned deposit and the documentary exoneration, Julian's accession and adversary heading, the transfer of pre-Trust Discovery material, and the loss of the instruments. The batch was read continuously as prose and audited separately against the Arc Outline, Canon Bible, and Motif Ledger. Two findings could not be repaired in prose alone and are carried by [`ARC-CHANGE-REVISION-003`](arc-changes.md).

Every criterion below is a human Editorial_Gate criterion and carries no automated score, under global invariant 25 of [`arc-outline.md`](arc-outline.md) and Requirement 12.12. Chapter numbers and line references locate evidence; they do not rate it.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-001",
    "scope": "batch",
    "chapter_numbers": [52],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Narrator record horizon agreement with authoritative reveal ownership and release",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "start_line": 17, "end_line": 41, "note": "Nia receives the closed review as a party, reads it herself, and states that her routing did not cause the death and that no available routing would have prevented it."}
    ],
    "finding": "revision",
    "rationale": "REVEAL-CASUALTY-CONSEQUENCE is owned by POV-NIA and releases in Chapter 52, and CF-CASE-ZERO-LOGS makes the documentary exoneration her attributed first-person account. The Chapter 52 record_horizon still carried pre-task-5.6 wording saying she knew only that the logs existed and had not been told what the timestamps established. No draft can both release the finding and be barred from knowing it, so this was a planning contradiction rather than a prose error. The prose is correct: nobody explains the review to her, she does the arithmetic herself, and the finding stays confined to outcome causation.",
    "requested_action": "Synchronize the Chapter 52 record_horizon to Nia's ownership of the documentary release while preserving the review's silence on authorship, her inability to compel release of the county's copy, and her refusal of both origin accounts. Do not move the reveal owner, release chapter, or payoff window.",
    "reviewer": "Author-delegated editorial review and independent canon audit",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Resolved by ARC-CHANGE-REVISION-003. The horizon now records that she reads the closed review herself and establishes outcome causation only."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-002",
    "scope": "batch",
    "chapter_numbers": [51, 52, 53, 54],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Institutional credibility: the Trust must apply its depositor-ownership rule to every witness including the sympathetic one",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "start_line": 76, "end_line": 80, "note": "Mara is told she cannot deposit the Consortium's specification because it is not hers."},
      {"path": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "start_line": 24, "end_line": 46, "note": "The archivist refuses Ravi Anand's notebook from Mara's hands because the conditions belong to whoever's account it is."}
    ],
    "finding": "revision",
    "rationale": "As first drafted, Chapter 52 let Nia deposit the county's dispatch review and write release conditions on it, while Chapters 51 and 54 enforced the opposite rule against Mara twice. The review is a third party's record containing a dead man's clinical details, and his family agreed to nothing. An institution that suspends its founding rule for the witness the reader likes is not an institution, and the whole record thread depends on that rule being real. The Arc Outline requires the timestamped record to sit beside her account, so the mechanism had to change rather than the outcome.",
    "requested_action": "Have the archivist refuse the review from Nia on the record, obtain a certified copy issued direct to the Trust by the county records office under its own authority as a separate accession, and reduce Nia's condition four to negative control: her account does not open unless the certified copy is released beside it, and she cannot compel the county's copy to open. Reflect the two accessions and two depositors in Chapter 53.",
    "reviewer": "Author-delegated editorial review and independent canon audit",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Resolved by ARC-CHANGE-REVISION-003. Nia is refused once on the page, keeps only the power to refuse being read alone, and says so."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-003",
    "scope": "batch",
    "chapter_numbers": [47, 52, 53],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Release conditions must not be already satisfied by events the manuscript has delivered",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 23, "end_line": 35, "note": "The circulated pilot expansion pack already characterizes Nia's incident as consistent with unauthorized channel effect on volitional certainty."},
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 13, "end_line": 19, "note": "Julian describes the holding as sealed and withheld, which assumes the trigger has not fired."}
    ],
    "finding": "revision",
    "rationale": "Nia's release trigger originally fired on any product document identifying her incident as mental intrusion. Chapter 47 had already put exactly such a product document into circulation, so on the ordinary reading her deposit was open the moment she signed it, which contradicted Chapter 53 and would have pre-empted the post-null conditioned-release chronology. Nia is the most precise narrator in the book and would not have missed this, so the fix belonged inside her own reasoning rather than in a silent narrowing.",
    "requested_action": "Have Nia define the trigger herself as published or laid before a public body and identified as hers by name or by particulars amounting to it, name the binder as the thing the limit deliberately excludes, and accept the cost aloud.",
    "reviewer": "Author-delegated editorial review and independent canon audit",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Resolved by ARC-CHANGE-REVISION-003. She spends longer on the word publicly than on the other five conditions and states what it lets through."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-004",
    "scope": "batch",
    "chapter_numbers": [52, 53],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Causal-cut viewpoint shift must add a new position rather than re-prove the released finding",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 21, "end_line": 31, "note": "Julian re-derived the access time, unit position, and pre-call arrest one chapter after Nia established them, delaying the field-eight problem that is his actual material."}
    ],
    "finding": "revision",
    "rationale": "CUT-DEPOSIT-AND-THE-TIMESTAMPS gives Chapter 52 the release and Chapter 53 the institutional consequence. Repeating the proof made the second chapter feel like a summary of the relationship and competed with Nia's plainer emotional beat, which is the stronger of the two. Julian needs the conclusion, not the arithmetic.",
    "requested_action": "Compress Chapter 53's restatement to the conclusion and its effect on Julian, remove the duplicated review-field enumeration, and reach field eight sooner.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Resolved in the same pass. Chapter 53 now states the finding in one paragraph and keeps its own material."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-005",
    "scope": "batch",
    "chapter_numbers": [51, 53, 54],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Institutional and technical mechanics must be plausible rather than arranged to produce the intended moral result",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "start_line": 48, "end_line": 70, "note": "The Trust arrived complete in six days with recruited custodians, secure custody, and live intake, none of it accounted for."},
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 33, "end_line": 39, "note": "A local heading was described as invisible to every possible search, which made the catalogue trap authored rather than institutional."},
      {"path": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "start_line": 18, "end_line": 20, "note": "The archivist compared eleven of sixty-four checksum characters and the result was called better than a date."}
    ],
    "finding": "revision",
    "rationale": "The book's authority rests on getting institutional and technical procedure right, so three shortcuts stood out precisely because everything around them is exact. A trust cannot be recruited, housed, insured and made operational in six days without explanation; a local archival heading is not invisible to a direct enquiry; and a partial visual checksum comparison is not verification. The last one also conflated content corroboration with dating in a chapter whose subject is that distinction.",
    "requested_action": "Ground the six days in reused existing structures and name the fragility that follows. Replace the absolute invisibility claim with the authority-heading export constraint. Have the archivist run the checksum herself, match all sixty-four characters, and record that corroboration is not a date.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Resolved in the same pass. The Trust is assembled from a dormant charitable company, a retired records officer's fitted strongroom, and a paid encryption service, and Julian names that as the reason it could be taken apart."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-006",
    "scope": "batch",
    "chapter_numbers": [51, 52, 53, 54, 55],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Voice separation under DEC-018 clause 7: shared aphoristic cadence flattening three distinct narrators",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "start_line": 70, "end_line": 76, "note": "The closing beat resolved into a procedural footnote about the conditions folder rather than an ending, then into a polished maxim about whose yes is worth having."},
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 25, "end_line": 49, "note": "Relief arriving at the wrong address, and an archive abhorring a hole, are more decorated than Julian's flat professional register."}
    ],
    "finding": "revision",
    "rationale": "The batch is specific and convincing at the level of objects, procedure, and professional knowledge, which is where machine-written prose usually fails. The weakness is the sentence engine: too many paragraphs end on a balanced antithesis or a finished maxim, so Mara, Nia, and Julian sound equally polished even though their minds remain distinct. Individually these lines are strong; in accumulation they read as one authorial brief and they crowd the endings that should land hardest.",
    "requested_action": "Thin the intermediate aphorisms rather than the best terminal reversals. Keep Chapter 51's held-versus-answered close, Chapter 53's final self-indictment, Chapter 54's recording, and Chapter 55's final reversal. Give Nia an ending that lands on the dead man rather than on procedure, and return Julian to plainer diction where the ornament is doing the work.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Partly resolved in the same pass; the specific lines above were replaced or plainer versions substituted. The general cadence risk remains a standing craft criterion for Chapters 56–61 rather than a closed finding."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-007",
    "scope": "batch",
    "chapter_numbers": [50, 51, 54, 55],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Chapters that may be kept substantially as delivered",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "start_line": 13, "end_line": 40, "note": "Continuous desk scene: the softened minute, five failed searches, the private file, and the four headings, with no narrator naming the contradiction."},
      {"path": "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "start_line": 48, "end_line": 70, "note": "The forty-one-second recording and Mara's reason for leaving it in, which is the batch's strongest emotional turn."},
      {"path": "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "start_line": 13, "end_line": 72, "note": "Badge refusal, the two bare affirmatives that make Mara complicit, the retained-versus-lost accounting, and the test strips behind the glass."}
    ],
    "finding": "pass",
    "rationale": "Chapter 50 holds the declared contradiction-cut without either narrator explaining it. Chapter 54 escalates through objects rather than argument and finds the one item whose date rests on nothing but Mara's word, which dramatizes provenance-not-truth without stating it. Chapter 55 pays off the April arithmetic with no villain, no broken rule, and Mara supplying the load-bearing step herself, and it leaves the parallel programme genuinely opaque as its horizon requires. Chapter 51's opening exchange and its held-versus-answered close are the strongest writing in the record thread.",
    "requested_action": null,
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Kept. Only the mechanics findings above touched these chapters."
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-008",
    "scope": "batch",
    "chapter_numbers": [55, 56],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Handoff integrity into the Chapters 56–61 protocol batch",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "start_line": 60, "end_line": 72, "note": "Mara loses the test source, calibrated probe, array time, anechoic hours, and the interior of the room, and therefore the ability to measure."}
    ],
    "finding": "revision",
    "rationale": "Chapter 55 removes Mara's instruments, and Chapter 56 requires the movement's first sustained instrumented pairing conversation. The batch cannot quietly restore array access without cancelling the cost that Chapter 55 exists to impose, and DEC-018's Anchor-cost obligation depends on that cost holding.",
    "requested_action": "Chapter 56 must establish on the page where the equipment, space, and authorization for the protocol sessions come from after the transfer, or place the work somewhere Mara does not need Northline's provisioning. Do not silently reissue her badge.",
    "reviewer": "Author-delegated editorial review",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": {
      "resolved_at": "2026-09-13T18:13:54Z",
      "action_taken": "Chapter 56 opens on a written, time-bounded research-operations booking for Calibration Room C, the retained PAIR console, and two contact bands. It expressly excludes the transferred array room, test source, calibrated probe, and every transfer-schedule instrument; Mara's array-room badge still returns one red refusal, while the separately retained calibration room opens under research-operations authority.",
      "follow_up_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001"
    }
  }
]
```

Chapters 50, 51, 54, and 55 are `revised` and carry no open finding except the standing cadence criterion. Chapters 52 and 53 are `revised` with their two blocking findings resolved and evidenced. Finding 008 is deliberately left open, because it is an obligation on Chapters 56–61 rather than a defect in this batch. No chapter in this batch is `approved`: approval requires the movement Editorial_Gate at task 13.6, which has not run.

## `DEC-020` propulsion review of the delivered 55 chapters

The author directed a review of the whole delivered arc against the recorded Brown/Richards class bar, with the instruction that the book have its own feel, real class and quality, no machine-signature prose, and nothing pointless. The review read Chapters 1–15, 17–22, 24–35, 37, 38, and 43–55 closely, and extracted the actual opening and closing beat of every delivered chapter including the exploratory 73, 118, and 124. Chapters 16, 23, 36, and 39–42 were judged only from their boundaries and are recorded as unread.

Two conclusions frame everything below. The prose and the premise meet or exceed the class bar; nothing in this review asks for better sentences. The propulsion machinery does not meet it, and every cause identified is mechanical and fixable without touching Requirements 2.13 or 2.14. `DEC-020` records the binding rules and Requirements 15.9 through 15.12 gate them for every future batch.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-001",
    "scope": "manuscript",
    "chapter_numbers": [19, 21, 22, 25, 26, 28, 29, 38],
    "batch_id": null,
    "criterion": "Clock kind: deliberation deadlines used as the manuscript's dominant forward device",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-021-reconstruction.md", "start_line": 160, "end_line": 162, "note": "'I do not know which one is honest, and I have until the twentieth to find out.'"},
      {"path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "start_line": 96, "end_line": 98, "note": "Original close: 'Eleven days to find a record that can hold a belief without promoting it, or an answer I am willing to give her instead.'"},
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 60, "end_line": 62, "note": "Original close: 'I have a week to work out which nomination I would be able to defend afterward.'"},
      {"path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "start_line": 100, "end_line": 102, "note": "Original close: 'Twelve days to decide how much of this apparatus I am willing to describe to three lines on a list I could not place.' This discarded the strongest closing image in Discovery, the latch going into the frame, which sat in the paragraph above it."}
    ],
    "finding": "revision",
    "rationale": "Eight chapters close on time remaining until the narrator must choose what to write, say, or defend. Each is characterful and the accumulation is one chord: by Chapter 26 a reader hears it coming. The deeper problem is kind rather than repetition. A deliberation deadline has no consequence attached to its expiry, so nothing irreversible happens when the date arrives, and the book's entire forward mechanism was resting on a device that cannot cost anybody anything. Both named inspirations run on clocks whose expiry is physical.",
    "requested_action": "Under DEC-020 clauses 1 and 2, attach an irreversible external consequence to declared clocks and cap the deliberation form at two chapters per drafting batch. Vary ending kind: interrupted act, arriving object, answer given aloud, unglossed physical image, consequence landing on somebody else, refusal.",
    "reviewer": "Author-directed arc review, author-delegated agent reading",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Partly resolved. Chapter 25 now ends on the bagged relay with UNASKED underlined twice; Chapter 26 now ends on a briefing that proceeds with the development contact already on file whether Julian nominates anyone or not; Chapter 29 now states the irreversible fact that papers go out on the nineteenth and ends on the latch. Four instances remain at 19, 21, 22, and 28, which is inside the clause 2 per-batch cap, and Chapter 28's is retained because it is the strongest chapter in its stretch."
  },
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-002",
    "scope": "manuscript",
    "chapter_numbers": [14, 15, 22, 26],
    "batch_id": null,
    "criterion": "Viewpoint allocation: consecutive document and deliberation chapters producing a momentum trough",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-022-fundable.md", "start_line": 44, "end_line": 46, "note": "'By the end of the day the proposal carried twenty-seven comments and one schedule.' The chapter's own summary of itself is accurate and is the finding."},
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 22, "end_line": 26, "note": "Revision-history walkthrough presented as escalation: 'The phrase persistent human-associated pattern appears in revision three... In revision eight somebody adds a clause I have now read eleven times.'"}
    ],
    "finding": "revision",
    "rationale": "Roughly 4,700 words across four chapters in which one man reads drafts, revises his own sentences, takes one telephone call each, and receives a deadline. Chapters 15, 22, and 26 are near-interchangeable in architecture. Chapter 14 earns its place because the category failure is fresh there and it contains the line the novel rests on, that the fact she cannot feel the receiver does not make her absent from the act; the other three largely re-stage that argument. Across Chapters 11 to 29 the strongest dramatic narrator holds two chapters and both are the best in the movement, while the flattest four belong to one viewpoint. The prose is competent throughout. The defect is arrangement, and no line editing repairs three consecutive chapters of one shape.",
    "requested_action": "Under DEC-020 clause 8, no three consecutive chapters may be document, drafting, or deliberation chapters regardless of viewpoint. A dedicated later pass may compress 15, 22, and 26 or redistribute their material; that pass is not authorized here because it would alter delivered arc beats rather than prose.",
    "reviewer": "Author-directed arc review, author-delegated agent reading",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": {
      "resolved_at": "2026-09-13T17:26:29Z",
      "action_taken": "A direct continuous reread rejected percentage compression and corrected the finding's arrangement premise: Chapters 14, 15, 22, and 26 are not consecutive, and intervening chapters materially change viewpoint, action, and stakes. Chapters 15 and 26 retain distinct functions and full scene architecture. Chapter 25/26 received only the confirmed knowledge-horizon repair, and Chapter 26's planning-hook echo was removed without cutting its load-bearing receive-only boundary.",
      "follow_up_finding_id": "EDITORIAL-PROPULSION-002-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-003",
    "scope": "manuscript",
    "chapter_numbers": [12, 27, 28],
    "batch_id": null,
    "criterion": "Interrupted cut and bodily stakes: the techniques the book already performs well and rations",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "start_line": 13, "end_line": 15, "note": "'He's on the floor by the table,' the girl said. Then, 'He's breathing.' Then, 'I don't know if that's breathing.'"},
      {"path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "start_line": 96, "end_line": 98, "note": "'I was still deciding when the tone sounded in the test room.' The only interrupted cut in fifty-five delivered chapters."},
      {"path": "chapters/discovery-part/discovery-part-028-named-second.md", "start_line": 34, "end_line": 38, "note": "'My finger pressed. / Then I knew. Not before.'"}
    ],
    "finding": "pass",
    "rationale": "Recorded as a pass so the standard is preserved rather than argued. Chapter 12 is the benchmark for the whole manuscript: real time, a clock the reader feels, physical jeopardy, competence dramatized rather than asserted, and an outcome withheld because dispatch genuinely never receives it, which satisfies Requirements 2.13 and 2.14 exactly. Chapter 27 proves the interrupted cut is available and costs nothing under the withholding ban. Chapter 28 delivers the premise from inside a body. The finding against the manuscript is that these appear three times in fifty-five chapters, and after Chapter 12 no character is in physical danger anywhere in the delivered arc.",
    "requested_action": "Under DEC-020 clauses 3 and 5, every batch of four or more chapters carries at least one interrupted cut, and Chapters 62-112 must contain physical danger to a named person, a place someone should not be, movement between locations under pressure, and a consequence arriving in a body rather than in a file.",
    "reviewer": "Author-directed arc review, author-delegated agent reading",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Standard recorded. Forward obligation carried by DEC-020 and Requirements 15.9 and 15.10."
  },
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-004",
    "scope": "manuscript",
    "chapter_numbers": [11, 13, 14, 18, 22, 25, 26, 27, 28, 29],
    "batch_id": null,
    "criterion": "Machine-signature register: named tics accumulating across three distinct viewpoints",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "start_line": 30, "end_line": 32, "note": "Self-correcting sentence: 'A field with a body, I wrote, and crossed out body.'"},
      {"path": "chapters/discovery-part/discovery-part-014-rights-before-names.md", "start_line": 60, "end_line": 62, "note": "Complicity subordinate clause: 'I am good at preserving room. It is most of what I am paid for, and I am aware that saying so is not the same as declining to do it.'"},
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 40, "end_line": 44, "note": "Restated technical disclaimer: 'no exciter, no driver, no outgoing feed', repeated from 13 and 22."}
    ],
    "finding": "revision",
    "rationale": "The manuscript is specific and convincing at the level of objects, procedure, and professional knowledge, which is where machine-written prose usually fails. Its actual exposure is the sentence engine. Five habits recur often enough to read as one authorial reflex rather than three minds: the self-correcting sentence across 11, 13, 14, 22, 25, 27 and 28; bad faith confessed in a dependent clause rather than enacted; the negative finding as climax at 13, 18, 25 and 29; the technical disclaimer restated for a reviewer rather than a reader; and the paragraph that closes on a finished maxim. Each is good once per viewpoint. In accumulation they flatten voice separation that DEC-018 clause 7 requires the prose to carry.",
    "requested_action": "Under DEC-020 clause 10, keep the strongest terminal reversals and let intermediate paragraphs remain observational, partial, or unresolved. Say each technical protection once, where a character needs it; the canon records already hold it and prose is not the place to reassure a reviewer.",
    "reviewer": "Author-directed arc review, author-delegated agent reading",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": "Superseding rule recorded. DEC-019 clause 12's withdrawn counting rule is replaced by DEC-020 clause 10, which states the criterion as a human judgment about consecutive finished paragraphs rather than a ratio."
  },
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-005",
    "scope": "manuscript",
    "chapter_numbers": [33, 43, 48],
    "batch_id": null,
    "criterion": "Adversary agency and setting variety",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 36, "end_line": 44, "note": "Dalby's strongest scene is an argument she wins on the merits and then loses on the record; she takes no action against anyone."}
    ],
    "finding": "revision",
    "rationale": "Imogen Dalby is the best adversary in the delivered book and has never done anything. She argues, concedes, and asks for the ninety-one words directly. Nobody in the manuscript is followed, threatened, coerced, hired away, outbid, published against, or reported. Institutional power appears almost exclusively as persuasion, when its real form is the ability to proceed without you. Chapter 55 is the first time that power acts, through an access list reissued on the fourth, and it is the most propulsive Mara chapter in the movement for exactly that reason. The delivered settings are also almost entirely institutional interiors.",
    "requested_action": "Under DEC-020 clauses 6 and 7, the counterforce takes actions with material consequence — procurement, access, hiring, publication, referral, filing, proceeding in absence — while creating no concealed villain, no sender connection, no unmasking and no adversary POV. Each batch places at least one scene somewhere nobody is being professional.",
    "reviewer": "Author-directed arc review, author-delegated agent reading",
    "reviewed_at": "2026-09-12T00:00:00Z",
    "resolution": {
      "resolved_at": "2026-09-13T21:42:42Z",
      "action_taken": "The counterforce now takes repeated actions with material consequence across Chapters 30 through 61: booking a room at Northline through a group entitled to book it, withholding the interface specification, refusing a hardware interlock on grounds of product identity, harvesting Nia's incident into an appendix under an information-sharing agreement that required nobody to ask her, closing enrollment so a non-enrolled dispatcher loses her console, and reissuing an access list that removes Mara's instruments. Setting variety followed from character rather than from quota: Ruth's kitchen and porch, Joss's workbench and his van with the heater running, a corridor floor, a benefits office, a car park.",
      "follow_up_finding_id": "EDITORIAL-PROPULSION-005-FOLLOWUP-001"
    }
  }
]
```

Chapters 25, 26, and 29 were revised in this pass and their Chapter_Local_Gates re-run clean; they remain `revised`, as does the 26–29 batch. Findings 002 and 005 are deliberately left open: the document trough is an arrangement problem whose repair would alter delivered arc beats, and adversary agency is an obligation on Chapters 56 onward rather than a defect repairable inside delivered prose. Finding 003 is recorded as a `pass` so that Chapters 12, 27, and 28 stand as the manuscript's own benchmark rather than as an outside comparison.
### Prospective application after the `DEC-020` anti-formula amendment

`ARC-CHANGE-DEC-020-ANTI-FORMULA-001` withdraws the numeric, adjacency, and fixed-occurrence remedies in `DEC-020` clauses 1–4, 7, and 8 for future gate decisions. The evidence, rationale, and historical requested actions in `EDITORIAL-PROPULSION-001` through `EDITORIAL-PROPULSION-005` are not rewritten. Their observations about repeated deliberation endings, the document-architecture trough, scarce physical consequence, named tics, adversary passivity, and setting monotony remain evidence. Future Drafting_Batch and Story_Movement gates apply amended Requirement 15.9 through contextual Editorial Review and do not treat the old counts as pass/fail thresholds.

The amendment itself resolves no prose finding. A repeated local shape may be earned, while a superficially varied batch may still feel mechanical. Future findings must make that distinction from representative prose rather than from a required interrupted cut, short chapter, location excursion, or ending rotation.
## Existing-chapter retention and Chapter 25–26 horizon repair

A continuous reread of Chapters 14–16 and 25–27 under amended `DEC-020` rejected percentage compression. It also found one actual defect: Chapter 25 had disclosed Nia's identity and Mara's temporary path directly to Julian even though Chapter 26 and the approved horizon require him not to know either fact. The repair changed that disclosure route, not Chapter 26's load-bearing technical boundary.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-002-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [14, 15, 22, 26],
    "batch_id": null,
    "criterion": "Viewpoint allocation and recurring document architecture: whether Chapters 14, 15, 22, and 26 create a redundant momentum trough that warrants compression or redistribution",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-014-rights-before-names.md", "start_line": 55, "end_line": 75, "note": "Julian turns a category analysis into a sent warning, and the warning is forwarded outside its distribution within seven minutes."},
      {"path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "start_line": 69, "end_line": 78, "note": "His safeguards materially create the meeting and give the nascent Consortium institutional form rather than merely reconsidering the rights question."},
      {"path": "chapters/discovery-part/discovery-part-022-fundable.md", "start_line": 47, "end_line": 63, "note": "The proposal becomes a schedule, produces three immediate institutional actions, and forces the distinct continued-collection question."},
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 43, "end_line": 58, "note": "The dispersed proposition defeats containment and produces a national briefing that proceeds whether Julian participates or not."}
    ],
    "finding": "pass",
    "rationale": "The original finding correctly noticed a recurring institutional form but incorrectly described four nonconsecutive chapters as consecutive and treated distinct state changes as interchangeable. Chapters 16–21 and 23–25 intervene with other viewpoints, technical action, bodily consequence, refusal, and disclosure. Chapter 15 changes an informal group into a scheduled actor; Chapter 22 converts principle into funded procedure; Chapter 26 converts leakage into an unavoidable external briefing. Removing a fixed percentage would cut function to satisfy arithmetic. No compression or redistribution is warranted now.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T17:26:29Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-025-HORIZON-RERUN-001",
    "scope": "chapter",
    "chapter_numbers": [25],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Chapter 25 POV clarity, Mara Voice_Brief fidelity, continuity with Julian's knowledge horizon, honest disclosure, and Hook effectiveness after the repair",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "start_line": 38, "end_line": 47, "note": "Mara sees the broad distribution risk and enters the factual bench act in a restricted hardware-safety deviation without making her causal belief or Nia's identity part of Julian's legal matter."},
      {"path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "start_line": 72, "end_line": 77, "note": "The manual related-matter routing confirms no legal-file alert, while the sealed UNASKED relay still performs the chapter Hook."}
    ],
    "finding": "pass",
    "rationale": "The revised route is recognizably Mara: mechanism and record fields expose both the ethical limit and her chosen delay. The reader receives every fact she holds, the unauthorized act remains reviewable, Nia's identity does not travel under Mara's unsupported causal belief, and Julian can truthfully remain ignorant in Chapter 26 until the later approved reveal boundary.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T17:26:29Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-026-HORIZON-RERUN-001",
    "scope": "chapter",
    "chapter_numbers": [26],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Chapter 26 POV clarity, Julian Voice_Brief fidelity, continuity, prose economy, and Hook effectiveness after the repair",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 43, "end_line": 52, "note": "Julian's receive-only audit now functions as a first-person knowledge boundary and dramatic irony: the insurer prices an active use his disclosed record cannot support."},
      {"path": "chapters/discovery-part/discovery-part-026-already-outside.md", "start_line": 55, "end_line": 58, "note": "The planning-hook echo is gone; the chapter instead lands on a briefing that proceeds and the narrowed agency of who will speak."}
    ],
    "finding": "pass",
    "rationale": "The disputed audit sentence is not dispensable recap. It distinguishes the unchanged December receiver from Mara's undisclosed later path, establishes exactly what Julian has personally verified, and makes the insurer's anticipation alarming. Removing the near-verbatim Hook echo improves economy without compressing a scene whose inquiry, custody, failed containment, and forced-briefing turns are all distinct.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T17:26:29Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-025-HORIZON-RERUN-001",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [25],
      "documents": ["chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/decisions.md", "planning/voice-briefs.md"],
      "description": "Current chapter editorial rerun after synchronizing Mara's disclosure route with Julian's approved Chapter 26 knowledge horizon."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-025-HORIZON-RERUN-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T17:26:29Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-026-HORIZON-RERUN-001",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [26],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "planning/arc-outline.md", "planning/decisions.md", "planning/voice-briefs.md"],
      "description": "Current chapter editorial rerun after removing the Hook echo while retaining the necessary receive-only knowledge boundary."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-DISCOVERY-026-HORIZON-RERUN-001", "EDITORIAL-PROPULSION-002-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T17:26:29Z"
  }
]
```
## Task 13.5 — Chapters 56–61 editorial review and task 13.6 prerequisite audit

The six chapters were read continuously after the final narrow prose pass. The batch keeps the Chapter 55 loss intact, makes consent current and act-specific, distinguishes operational proof from testimony, exposes integrity failure without guessing, and reaches the edge of Mindwars through secondhand institutional reports rather than a comparable firsthand pattern. The seven task-13.5 editorial gates below pass. They do not approve the Private_Defense_Part movement.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-056",
    "scope": "chapter",
    "chapter_numbers": [56],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 56 POV clarity, Nia Voice_Brief fidelity, Chapter 55 continuity, current-consent mechanics, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-056-ask-first.md", "start_line": 15, "end_line": 17, "note": "The written booking names the retained calibration room, PAIR console, contact bands, exclusions, and unchanged red badge refusal before any pairing begins."},
      {"path": "chapters/private-defense-part/private-defense-part-056-ask-first.md", "start_line": 188, "end_line": 210, "note": "Nia pauses a deliberate contribution, the trace ends without buffering or completion, metadata retains no language or reason, and the ending separates custody of paper, export, and pause."}
    ],
    "finding": "pass",
    "rationale": "Nia begins from three concrete permissions and tests each rule through an act rather than lecturing from a finished protocol. Her internal completion remains honestly available to the reader because she narrates it, while Mara and the apparatus receive only the offered fragment. The Chapter 55 cost survives intact, the long scene earns its space as the first sustained fluent exchange, and the final custody split performs the Hook without repeating its planning sentence.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-057",
    "scope": "chapter",
    "chapter_numbers": [57],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 57 POV clarity, Mara Voice_Brief fidelity, stale-state continuity, zero-transport evidence, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 40, "end_line": 49, "note": "Mara performs the unauthorized send act; the session layer accepts the request, the independent live gate rejects it, and trace plus participant testimony establish zero transport without becoming one another."},
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 87, "end_line": 92, "note": "The unglossed interface lines hold current session authorization beside rejected live consent and leave the ethical contradiction active at the close."}
    ],
    "finding": "pass",
    "rationale": "The chapter is recognizably Mara because technical curiosity becomes an act she records against herself instead of a rationale that acquits her. It preserves the closed PAIR model: no unconsented semantic transport occurs, yet the stale interface still solicits an act it had no authority to solicit. The final display lets the reader assemble the failure and cleanly performs the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-058",
    "scope": "chapter",
    "chapter_numbers": [58],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 58 POV clarity, Julian Voice_Brief fidelity, metadata and custody limits, institutional consequence, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "start_line": 12, "end_line": 25, "note": "Julian reconstructs only consent state, timing, request, rejection, and zero transport, then keeps each participant's possible testimony separate from apparatus metadata."},
      {"path": "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "start_line": 28, "end_line": 54, "note": "The evidentiary distinction produces immediate resignation, nonprejudicial file transfer, direct institutional deposit, and separate ownership of testimony."},
      {"path": "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "start_line": 71, "end_line": 72, "note": "The ending corrects 'what happened' to 'what the apparatus did' and files the narrower rule rather than echoing the ArcEntry Hook."}
    ],
    "finding": "pass",
    "rationale": "Julian's timestamps, custody questions, and balanced limiting clauses remain distinct from Mara's mechanism and Nia's operational sequence. The chapter does not inflate metadata into content or credibility; its legal and institutional state changes are consequential rather than decorative. The revised opening withholds the conclusion until the fields establish it, and the filed correction is a stronger, plainer Hook than the prior summary ending.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-059",
    "scope": "chapter",
    "chapter_numbers": [59],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 59 POV clarity, Mara Voice_Brief fidelity, current authorization, integrity-failure handling, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "start_line": 16, "end_line": 25, "note": "A fresh five-minute scope, separate confirmations, recording off, and the clipped retained-asset authorization establish the lawful test without replaying Chapter 56."},
      {"path": "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "start_line": 55, "end_line": 77, "note": "The interface supplies an incomplete integrity state and zero semantic volume, permits only sender-controlled retry, then closes when Nia chooses ordinary speech."},
      {"path": "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "start_line": 92, "end_line": 102, "note": "The repaired rule makes retry a new act and spoken fallback a new statement; the failed-content field remains empty at the close."}
    ],
    "finding": "pass",
    "rationale": "Mara's attention stays with measured delay, endpoint state, and the temptation to infer from context. She rejects that temptation in action: the machine proposes no candidate, the receiver asks once, and the sender controls retry or speech. The final empty field performs the Hook without pretending that absence reconstructs Nia's failed contribution.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-060",
    "scope": "chapter",
    "chapter_numbers": [60],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 60 POV clarity, Nia Voice_Brief fidelity, unoffered-thought privacy, evidence restraint, warmth, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "start_line": 16, "end_line": 55, "note": "Nia holds a complete argument and a second objection while the fluent exchange continues; she offers only the narrow sentence, and Mara receives no sign of either retained thought."},
      {"path": "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "start_line": 69, "end_line": 80, "note": "The delivery-driver account arrives through two intermediaries, is not entered as a case, contact remains the driver's choice, and the nearest shielded room has no timely opening."}
    ],
    "finding": "pass",
    "rationale": "Nia's distinction between a useful claim and an overbroad word is carried through choice, correction, and consequence rather than technical reassurance. The mixer story and Joss's soup give her a private life without turning him into an exposition audience. The external report is explicitly secondhand and unowned, so it creates need and pressure without spending Chapter 62's first comparable firsthand pattern. The Thursday answer lands the Hook on material access rather than on a thesis.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-061",
    "scope": "chapter",
    "chapter_numbers": [61],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Chapter 61 POV clarity, Mara Voice_Brief fidelity, MOT-COME-02 function, protocol ownership, evidence horizon, movement turn, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "start_line": 30, "end_line": 72, "note": "The invitation becomes an ordered operating rule, fresh current answers expose the send fields, and Nia's local pause removes the field and Mara's control without explanatory replay."},
      {"path": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "start_line": 85, "end_line": 122, "note": "Operational consequences arrive only through supervisors' documents; no affected operator gives an account, compatible times prove neither sender nor common experience, and Mara remains barred from the array."},
      {"path": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "start_line": 152, "end_line": 164, "note": "Nia separately authorizes issue of the ordinary revision history, PAIR content remains unrecorded, institutional room requests grow, and the corridor alert continues after the booking ends."}
    ],
    "finding": "pass",
    "rationale": "Mara converts `MOT-COME-02` from unilateral invitation into a current two-person question with a local handle at each endpoint. The chapter repeatedly refuses to promote institutional summaries into firsthand mental evidence and preserves the Chapter 62 boundary, while the denied asset request keeps Chapter 55's cost active. The protocol is correct but physically inadequate to the public consequences; the ending lets that inadequacy sound in the corridor rather than explaining the planned Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061",
    "scope": "batch",
    "chapter_numbers": [56, 57, 58, 59, 60, 61],
    "batch_id": "BATCH-PRIVATE-DEFENSE-056-061",
    "criterion": "Continuous batch judgment: transition value, Cross Cut clarity, pacing, Hook effectiveness, voice separation, technical action-result-consequence, originality, Chapter 62 boundary, and amended DEC-020 anti-formula quality",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-056-ask-first.md", "start_line": 188, "end_line": 210, "note": "Sustained fluent pairing ends in a participant-controlled pause and split records rather than a generalized safety claim."},
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 40, "end_line": 49, "note": "The next chapter breaks the protocol through Mara's act while preserving zero neural transport."},
      {"path": "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "start_line": 28, "end_line": 54, "note": "Julian converts the limited record into resignation, transfer continuity, and provenance-separated deposits."},
      {"path": "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "start_line": 55, "end_line": 102, "note": "A later practical test exposes degradation and reaches ordinary speech without machine completion."},
      {"path": "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "start_line": 51, "end_line": 80, "note": "Fluent pairing gives way to humor, soup, an unowned report, and the material scarcity of rooms."},
      {"path": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "start_line": 85, "end_line": 164, "note": "The completed private rule meets multiple public operational consequences that remain evidentially limited and physically outside the room."}
    ],
    "finding": "pass",
    "rationale": "The six chapters form one escalation without becoming six versions of one test: authorization and fluent exchange; an ethically failed blocked act; forensic limitation and resignation; exposed integrity failure; retained private thought amid ordinary warmth; then a correct protocol overtaken by public demand. Nia, Mara, and Julian remain distinct in sequence, mechanism, and custody. The two long chapters are long because they hold the first sustained conversation and the movement-closing negotiation/public turn; the other four stop at their earned consequence. No interrupted cut, microchapter, noninstitutional scene, ending kind, or setting change has been inserted as a quota token. The Joss scene and varied endings arise from character and consequence, not rotation. Technical claims remain attached to acts and costs, no background thought leaks, no guessed completion or transcript appears, and Chapter 62 retains the first comparable firsthand pattern. The batch has its own morally exact institutional-thriller register and shows no recognizable imitation or machine-signature recipe.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001",
    "scope": "batch",
    "chapter_numbers": [55, 56],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Follow-up on handoff integrity from Chapter 55's instrument loss into the Chapters 56–61 protocol batch",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "start_line": 60, "end_line": 72, "note": "The prior chapter removes the source, probe, array time, anechoic hours, room interior, and measurement capacity."},
      {"path": "chapters/private-defense-part/private-defense-part-056-ask-first.md", "start_line": 15, "end_line": 17, "note": "The next chapter uses only a written time-bounded booking for the separately retained calibration room, PAIR console, and contact bands; all transferred assets remain excluded and the array reader remains red."}
    ],
    "finding": "pass",
    "rationale": "The handoff now distinguishes property authorization from participant consent and preserves the full Chapter 55 cost. Research operations can lawfully book its retained room and conversation equipment without restoring Mara's array badge, source, probe, array time, anechoic hours, second operator, measurement capacity, or visibility into Emergency Preparedness.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T18:13:54Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-056",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [56], "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 56 editorial gate after resolving the Chapter 55 asset-and-authorization handoff."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-056", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-057",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [57], "documents": ["chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 57 editorial gate for the blocked stale-consent send request and zero-transport record."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-057"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-058",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [58], "documents": ["chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 58 editorial gate for metadata limits, resignation, custody, and the repaired five-part rule."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-058"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-059",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [59], "documents": ["chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 59 editorial gate for incomplete-integrity handling, sender-controlled retry, and ordinary speech."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-059"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-060",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [60], "documents": ["chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 60 editorial gate for unoffered thought, voluntary contact, secondhand evidence, and inaccessible public defense."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-060"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-061",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [61], "documents": ["chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapter 61 editorial gate for MOT-COME-02, joint protocol ownership, access continuity, limited reports, and the movement turn."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-061"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-PRIVATE-DEFENSE-056-061",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [56, 57, 58, 59, 60, 61], "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 13.5 current Chapters 56–61 drafting-batch editorial gate. All assigned local and batch criteria pass under amended DEC-020 without a quota or rotation; this result does not approve the Private Defense movement."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-056", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-057", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-058", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-059", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-060", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-061", "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T18:13:54Z"
  }
]
```

### Task 13.6 movement-gate prerequisite result

The current Chapters 56–61 evidence is sufficient for its own batch, but not for the movement gate. Current chapter and batch editorial gates are absent for Chapters 30–55; objective records are absent for Chapters 43–49; the nine `DEC-018` revision findings and `EDITORIAL-PROPULSION-005` remain unresolved; and `ARC-CHANGE-REVISION-001` and `ARC-CHANGE-REVISION-002` remain in progress. The record below therefore says `incomplete`, not `pass` or `revision`, and task 13.6 remains unchecked.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001-INCOMPLETE",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61],
    "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "chapters/private-defense-part/private-defense-part-045-page-nine.md", "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "chapters/private-defense-part/private-defense-part-056-ask-first.md", "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/decisions.md", "planning/editorial-log.md", "planning/gate-results.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
    "description": "Task 13.6 Private_Defense_Part movement Editorial_Gate prerequisite audit. Chapters 56–61 pass their current local and batch review, but required current chapter/batch editorial coverage for Chapters 30–55, objective coverage for Chapters 43–49, DEC-018 resolutions and reruns, propulsion follow-up, and completion of two governing ArcChanges are missing. No movement craft verdict or approval is asserted."
  },
  "prerequisite_state": "incomplete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-REVISION-001", "EDITORIAL-REVISION-002", "EDITORIAL-REVISION-003", "EDITORIAL-REVISION-004", "EDITORIAL-REVISION-005", "EDITORIAL-REVISION-006", "EDITORIAL-REVISION-007", "EDITORIAL-REVISION-008", "EDITORIAL-REVISION-009", "EDITORIAL-PROPULSION-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061"],
  "result": "incomplete",
  "checker_exit_status": null,
  "timestamp": "2026-09-13T18:13:54Z"
}
```
## Private Defense Chapters 30–35 editorial review

No editorial finding or gate of any kind existed for Chapters 30 through 35. Task 13.1 recorded objective passes only, and the `DEC-018` gate later put the prose under revision at manuscript scope. The six chapters have since been revised: they now sit in the clause-10 band, open on action or object rather than thesis, and no longer close on their own ArcEntry Hook. The review below is the first craft evaluation of that current prose and supplies the chapter-approval coverage the movement gate requires.

One accumulation defect was found and repaired inside this pass, and it is recorded as a `revision` with its own follow-up rather than as a silent correction.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-030",
    "scope": "chapter",
    "chapter_numbers": [30],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 30 POV clarity, Mara Voice_Brief fidelity, continuity with the DEC-002 and DEC-004 arrival canon, DEC-007 restraint, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 12, "end_line": 15, "note": "The chapter opens on a running tap, clouded steam, and a hand stopped inside a cup, so the arrival is sensation before it is argument."},
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 50, "end_line": 53, "note": "No words, proposition, or voice; two non-contradicting entries; and the admission that the instrument log and the notebook can both be true is the chapter's actual problem."},
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 106, "end_line": 112, "note": "The cage and the earlier address lock sit three pages apart in one hand, and the chapter ends on a half-true facilities request rather than on its Hook sentence."}
    ],
    "finding": "pass",
    "rationale": "The certainty arrives finished and wordless, which keeps `DEC-004` intact and supplies no sender. Mara is recognizably herself: she refuses the certainty, records the time before moving, asks Ravi for evidence she was wrong, and then names the relief that Nia's injury would no longer stand alone, which is `DEC-007` conviction held without authority. The exposed-persons list is established as a real moral object with Ravi's objection spoken on the page, and the closing beat is an action with a cost rather than a restatement of the planned Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-031",
    "scope": "chapter",
    "chapter_numbers": [31],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 31 POV clarity, Nia Voice_Brief fidelity, MOT-COPPER-01 function, evidentiary restraint, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 12, "end_line": 14, "note": "Contact fingers meeting the frame in an ascending sequence, the baffle winding down, and the sound of her own sleeve open the chapter in the body."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 36, "end_line": 39, "note": "Relief arrives as anger at how long she has been braced, which is the motif's cost rather than its comfort."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 80, "end_line": 83, "note": "She makes Mara date the page and write on it that it proves nothing, and declines to improve the resulting sentence."}
    ],
    "finding": "pass",
    "rationale": "`MOT-COPPER-01` performs its ledgered double function: the quiet is the best thing she has felt in months and simultaneously measures how open every previous room was. Nia's restraint is exact and professional rather than decorative, because she states what the absence does not establish before her shoulders drop, and Mara's cards are shown to claim only what the probes measured. Her intervention on the notebook is the chapter's strongest act: she cannot get her name off a page that is not hers, so she attacks how it will read to a stranger in five years. The ending on the closed car doors admits the boundary does not travel with her.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-032",
    "scope": "chapter",
    "chapter_numbers": [32],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 32 POV clarity, Mara Voice_Brief fidelity, technical action-result-consequence staging, consent architecture, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "start_line": 19, "end_line": 20, "note": "The seam map indicts the door and produces the chapter's governing engineering fact about the worst joint."},
      {"path": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "start_line": 29, "end_line": 33, "note": "She draws the sealed enclosure, then refuses it because it converts an occupant into stored equipment, so the ethical choice is made against the better measurement."},
      {"path": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "start_line": 71, "end_line": 90, "note": "She releases the latch herself, renames the closure assembly a handle, dates Ravi's objection, then writes her own name in the keyholder box and keeps the key for eleven weeks."}
    ],
    "finding": "pass",
    "rationale": "Every technical decision produces a human or institutional consequence in the same movement: the failed tape yields checkable torque bonds, the accessibility failure yields a flush threshold and an occupant-run test strip, the network line is removed rather than filtered, and the intercom becomes an acoustic tube whose function a person can understand. The chapter earns its central rule by refusing the stronger sealed design. The final beat is genuine forward pressure rather than a Hook echo: she takes custody of the one key that defeats her own principle and names the eleven weeks she will have to answer for.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-033",
    "scope": "chapter",
    "chapter_numbers": [33],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 33 POV clarity, Julian Voice_Brief fidelity, DEC-012 register discipline, adversary agency, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 12, "end_line": 12, "note": "Dalby arrives early with two identical folders and leaves the operative one face down for fifty minutes, so the scene opens on withheld intent rather than on Julian's thesis."},
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 48, "end_line": 51, "note": "Dalby defeats the taxonomy on operability, names the woman who cannot speak, and extracts a structural concession Julian will not defend in front of a policy director."},
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 88, "end_line": 88, "note": "He forwards the shaded box to Mara without argument, partly to learn whether she will answer counsel's question about the named-individuals record before he must."}
    ],
    "finding": "pass",
    "rationale": "Julian's three nouns are sound and the chapter's point is that soundness is not operability. His characteristic evasion is active rather than confessed: he concedes the bounded-class structure to avoid admitting ignorance, then copies the concession into his own file so the record shows he offered it. Dalby is at last an adversary who does things — she wins on the merits, writes the hinge into her own margin, plants the enrollment default, and opens the line of inquiry that will reach Mara's notebook. The default-enabled box absorbs all three nouns without naming transmission, which dramatizes the failure instead of asserting it, and the ending transfers an obligation rather than restating the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-034",
    "scope": "chapter",
    "chapter_numbers": [34],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 34 POV clarity, Nia Voice_Brief fidelity, unspoken contradiction under CUT-SEALED-ROOM-AND-A-LIFE, human warmth, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 20, "end_line": 23, "note": "The binder reaches simultaneous incidents and she closes it with her hands on the cover; the memory is not made foreign by the room."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 44, "end_line": 47, "note": "She leaves the enclosure and works the solvent call from the corridor floor, so the cost of the room is paid in action rather than stated as a dilemma."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 54, "end_line": 60, "note": "The vending-machine vote and shared pretzels give her four unverified minutes, and the colleague she nearly adds to the list stays unnamed."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 76, "end_line": 76, "note": "The chapter ends on her brother, the kitchen radio, and a switch, with nothing asked of her."}
    ],
    "finding": "pass",
    "rationale": "The declared contradiction is now carried entirely by events. Nia never says she must choose between safety and the call; she opens the door, sits on the floor, and does the work, then logs the openings so a later reader sees them. The chapter also supplies what the delivered manuscript previously lacked: ordinary human warmth between named people, food accepted rather than analyzed, and a joke that is not a professional riposte. Her near-naming of the console colleague creates a real unrecorded moral remainder, and the closing question about where an unspoken decision goes survives the chapter boundary without withholding any fact she holds.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-035",
    "scope": "chapter",
    "chapter_numbers": [35],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Chapter 35 POV clarity, Mara Voice_Brief fidelity, scale limit of the private answer, thread continuity, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 80, "end_line": 80, "note": "The written result separates physical possibility from social availability without claiming anything about the signal."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 90, "end_line": 90, "note": "Ravi asks for his name off the page, states he will file a formal request, and then withholds something he does not trust the notebook to hold."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 109, "end_line": 113, "note": "Twelve counted cases, a woman in a grey coat studying the roof of the new room, and Ravi gone with his log left rolled on the bench."}
    ],
    "finding": "pass",
    "rationale": "The chapter performs the movement's central inadequacy: a working boundary at the scale of one door against a field that does not stay at that scale, argued through cycle counts, gasket sets, and who can afford a lined bedroom rather than through declaration. Both previously abandoned threads now carry forward. Ravi's departure is the Anchor's personal cost, small and specifically hers, and it is left unresolved because what he wanted to tell her is never said. The arrival at the gate is answered with counted objects rather than explained, and it hands Chapter 36 a room already furnished. The Consortium remains an institution that proceeds rather than a villain, and nothing here identifies a sender.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-001",
    "scope": "batch",
    "chapter_numbers": [31, 34],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Voice separation under DEC-018 clause 7: recurrence of the reader-instruction construction that EDITORIAL-CAL-004 required be confined to Mara's log register",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 28, "end_line": 28, "note": "'I knew that at the time, and I want it in the account that I knew it.'"},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 34, "end_line": 34, "note": "'I waited. I want that in the record too: I waited, deliberately, and timed it.'"},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 40, "end_line": 40, "note": "Original text: 'That mattered. I want that in the record as well.' Nine lines after the previous instance and adding emphasis only."}
    ],
    "finding": "revision",
    "rationale": "The construction is defensible once in Nia's mouth, because entering and defending records is her profession and each instance marks that she understood a limit contemporaneously. It is not defensible three times across two chapters, twice inside nine lines of one chapter. The second Chapter 34 instance carries no new information: the preceding 'That mattered.' already performs the judgment, and the addition converts a dispatcher's precision into the reader-instruction tic that EDITORIAL-CAL-004 identified and required be reserved to Mara. Left in accumulation it re-opens the voice-separation defect the revision pass was supposed to close.",
    "requested_action": "Cut the redundant second instance in Chapter 34 and leave the two that do specific work. Do not substitute another shared formula in its place, and do not remove Nia's professional insistence on the record where it marks contemporaneous knowledge.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": {
      "resolved_at": "2026-09-13T19:42:37Z",
      "action_taken": "Deleted 'I want that in the record as well.' from Chapter 34, leaving the bare 'That mattered.' The Chapter 31 instance and the first Chapter 34 instance were retained because each marks knowledge held at the time rather than emphasis. Chapter 34's declared count was corrected from 1,124 to the observed 1,116 and its Chapter_Local_Gate rerun clean.",
      "follow_up_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002",
    "scope": "batch",
    "chapter_numbers": [31, 34],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Follow-up: voice separation under DEC-018 clause 7 after removing the redundant reader-instruction instance",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 40, "end_line": 40, "note": "The beat now reads only 'That mattered.', which states the judgment without instructing a future reader."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 28, "end_line": 28, "note": "The retained instance still does load-bearing work: it fixes that Nia understood the measurement's limits before her relief arrived."}
    ],
    "finding": "pass",
    "rationale": "Two remaining instances across six chapters, each marking contemporaneous knowledge rather than emphasis, read as Nia's professional register rather than as a borrowed authorial reflex. No replacement formula was introduced, and the surrounding beats are stronger bare. A separate measurement supports the wider judgment: the enumerated-absence construction that once appeared eleven times across the delivered files now appears twice in Chapters 30 through 61, once in Chapter 30 and once in Chapter 42, and in both the absence is the subject of the chapter.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003",
    "scope": "batch",
    "chapter_numbers": [30, 31, 32, 33, 34, 35],
    "batch_id": "BATCH-PRIVATE-DEFENSE-030-035",
    "criterion": "Batch judgment: POV transition value, Cross Cut clarity, pacing, Hook variety, chapter shape, human cost and warmth, adversary agency, technical consequence staging, originality, and amended DEC-020 anti-formula quality",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 54, "end_line": 76, "note": "The list is created and immediately contested by the person added last, so the batch's governing moral object is challenged at birth."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 80, "end_line": 83, "note": "Nia acts on that same object from the other side, changing what the page will mean to a stranger without replaying Mara's scene."},
      {"path": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "start_line": 29, "end_line": 33, "note": "The sealed-room refusal converts the shielding result into a rule about who owns an opening."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 44, "end_line": 47, "note": "The rule is then priced in a corridor, by a woman who leaves the protection in order to do her job."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 109, "end_line": 113, "note": "The batch closes on institutional arrival and a technician's withheld report rather than on a finished argument."}
    ],
    "finding": "pass",
    "rationale": "The six chapters escalate through distinct kinds of change rather than six versions of one demonstration: an unrecordable arrival, a measured private interval, an engineering refusal, a legal category defeated on operability, the lived cost of the protection, and the limit of its scale. Every viewpoint change adds knowledge or moral pressure, and the two Cross Cut relationships are readable without replay, with Chapter 34 holding only its own position now that the safety-versus-usefulness contradiction is dramatized instead of spoken. Endings vary in kind across a half-true request, a car with the doors shut, custody of a key, a transferred obligation, a brother's radio, and counted freight; none reproduces its ArcEntry Hook. Warmth is present without becoming an exposition audience, since Ruth asks nothing and Joss asks nothing. Dalby finally acts, and the Consortium's power appears as its ability to proceed and to furnish a room on somebody else's calendar. Technical material always lands on a person, an authorization, or a cost. Nothing is inserted for compliance: there is no interrupted-cut token, no manufactured microchapter, no rotation of ending kinds, and the one noninstitutional scene exists because Mara had nowhere else to go at eleven at night. One deviation is recorded rather than waived: Chapter 35 stands at 1,210 Prose_Words against the `DEC-018` clause 10 per-chapter ceiling of 1,200. It is not an objective violation, it remains inside the `normal` class, and the Private Defense normal-class mean across Chapters 30 through 49 is 1,139.6, inside the operative window; the ten-word overage is left for author discretion rather than trimmed, because cutting functioning prose to satisfy arithmetic is the practice this project already rejected.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T19:42:37Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-030",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [30], "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 30, covering POV clarity, Voice_Brief fidelity, arrival-canon continuity, and Hook effectiveness."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-030"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-031",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [31], "documents": ["chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 31, including MOT-COPPER-01 function and the resolved voice-separation criterion."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-031", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-032",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [32], "documents": ["chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 32, covering technical-consequence staging and the occupant-owned opening."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-032"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-033",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [33], "documents": ["chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 33, covering Julian's register, DEC-012 discipline, and adversary agency."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-033"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-034",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [34], "documents": ["chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 34, covering the unspoken contradiction cut, human warmth, and the resolved voice-separation criterion."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-034", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-035",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [35], "documents": ["chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 35, covering the scale limit, both recovered threads, and the Anchor's personal cost."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-035"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-PRIVATE-DEFENSE-030-035",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [30, 31, 32, 33, 34, 35], "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First Chapters 30–35 drafting-batch editorial gate. All chapter findings pass, and the one voice-separation revision raised in this pass is resolved with follow-up evidence. Chapter 35's ten-word clause-10 overage is recorded as an author-discretion deviation, not waived. This gate does not approve the Private_Defense_Part movement."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-030", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-031", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-032", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-033", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-034", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-035", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T19:42:37Z"
  }
]
```
## Private Defense Chapters 36–42 editorial review

Task 13.2 recorded objective passes for this batch and left the required human review open; the `DEC-018` gate then put the prose under revision at manuscript scope. The seven chapters have since been revised. This is their first craft evaluation, and it is the batch that carries `DEC-018` clause 9 warmth, the freely chosen benefit required by task 13.6, and the two threads recovered from Chapter 35.

All seven findings pass. Two matters are recorded explicitly rather than passed over in silence: the near-restatement of the Chapter 41 Hook inside that chapter's penultimate paragraph, and the question of whether Chapter 42 spends the irony of its own contradiction cut.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-036",
    "scope": "chapter",
    "chapter_numbers": [36],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 36 POV clarity, Julian Voice_Brief fidelity, thread continuity from Chapter 35, DEC-012 register discipline, freely chosen benefit, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 12, "end_line": 18, "note": "The visitor book answers Chapter 35's unidentified car with four ordinary entries, and the finding is the flatness: a group entitled to book the room did so on a page where Mara's group does not appear."},
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 26, "end_line": 34, "note": "The Ferris private layer is established as several hundred unwritten words that the calibration holds none of, and the first crossing is a joke about a squeaking chair."},
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 52, "end_line": 66, "note": "Ada states her own reasons for demonstrating, the clinical director demands he sign the cost of his own safeguards, and he leaves undecided whether the man and his daughter are an argument or a lever."}
    ],
    "finding": "pass",
    "rationale": "The dropped thread is recovered in the least melodramatic way available, which is also the most damning: no conspiracy, just a booking. The benefit is genuine and freely chosen, and Ada holds authority over it rather than serving as its illustration, because she gives professional reasons and refuses the word miracle. `DEC-012` discipline holds precisely: the `ESP` misnomer is spoken by a communications director beneath a screen, not by the narration. The private two-person layer is established as a class of thing that exists and could be lost, with no corpus, no notebook, and no connection drawn to any other character, so it prepares the Coda without pre-empting it. Julian's evasion is active: he answers the clinical director with a panel-ready sentence and hears its thinness himself.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-037",
    "scope": "chapter",
    "chapter_numbers": [37],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 37 POV clarity, Mara Voice_Brief fidelity, unoffered-mentation boundary, DEC-007 restraint, Chapter 62 boundary preservation, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 12, "end_line": 12, "note": "She unbolts the content recorder and puts it on the bench with its cable capped, so the protection is a physical object before it is a promise."},
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 42, "end_line": 46, "note": "Ada asks whether she is observing them or the channel, and Mara concedes she had conflated two permissions, lowers the resolution, and re-consents at a cost of twelve minutes."},
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 66, "end_line": 92, "note": "Ravi's Thursday is reported without a name for it, matched by nothing in the records, and Mara names her own wish that his account make hers less alone before refusing to use it."}
    ],
    "finding": "pass",
    "rationale": "The strongest beat is the participant catching the operator: a send gate keeps unoffered mentation out of transport and authorizes nothing about what an instrument may resolve around it, and that distinction is discovered by Ada rather than explained by Mara. The adversarial controls are honestly bounded, recorded as four hours of provocation rather than proof of absence. `DEC-007` is exact: Mara wants the corroboration, says so, and states that wanting it does not make it available. The chapter also protects Chapter 62 by naming what one account of one Thursday is not, and it ends on Ravi's shortened answer rather than on the planned Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-038",
    "scope": "chapter",
    "chapter_numbers": [38],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 38 POV clarity, Nia Voice_Brief fidelity, bounded operational benefit, consequence-bearing clock, human warmth, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 12, "end_line": 24, "note": "The consent card is timed and read in full, then the pairing's actual gain is one silent correction that Cora still speaks aloud for the floor."},
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 72, "end_line": 84, "note": "Tomas wants recording because an inquest read his silence as indifference, Nia refuses to invent an answer, and she tears the sample form un-ticking the box."},
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 94, "end_line": 98, "note": "Joss feeds her in the van without asking what she does, and the chapter closes on a Thursday deadline attached to the console she cannot keep without signing."}
    ],
    "finding": "pass",
    "rationale": "The benefit is real and strictly bounded: the fire still burns, a resident is hospitalized, the chained door stays chained, and what the channel buys is that neither dispatcher abandons a voice. Tomas supplies the best argument against Nia's own position, and the chapter's integrity rests on her declining to defeat it, distinguishing his right to make the argument from the operator's right to make it his default. The closing clock is the kind `DEC-020` asked for: a dated external consequence with a real cost attached, since refusal means losing the console from which she supervises. Warmth arrives without becoming an audience for exposition.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-039",
    "scope": "chapter",
    "chapter_numbers": [39],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 39 POV clarity, Julian Voice_Brief fidelity, calibration-as-relationship continuity, adversary agency, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "start_line": 12, "end_line": 12, "note": "A green flag pressed flat on page four tells him where the document wants him to look before he has read a word."},
      {"path": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "start_line": 22, "end_line": 22, "note": "Calibration is shown to be a relationship that no employee record, replacement partner, or onboarding budget can transfer, against a financial model treating it as an amortizable cost."},
      {"path": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "start_line": 48, "end_line": 62, "note": "The clinical director calls his five definitions a superb set of rules for the fortunate, counsel accepts them without amendment, and the withheld interface specification leaves with him unread."}
    ],
    "finding": "pass",
    "rationale": "The chapter tracks a benefit becoming a platform through nouns rather than villainy: named pairs become enrolled users, sessions become continuity, deliberate sends become frictionless exchange. Julian's competence is genuine and is exactly what makes the system fundable, which he states plainly. The counterparty's frictionless acceptance of all five definitions is correctly read as ominous rather than victorious, and the refusal to supply the specification is an institutional act with consequence that sets up the later page-nine reveal without importing it. The ending carries an unmet obligation instead of restating the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-040",
    "scope": "chapter",
    "chapter_numbers": [40],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 40 POV clarity, Mara Voice_Brief fidelity, deliberate-send and no-guessed-completion mechanics, Anchor personal cost, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 12, "end_line": 12, "note": "The chapter opens inside the consent exchange itself, spoken aloud and remade for this session only."},
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 24, "end_line": 44, "note": "Mara's unsent apology stays hers and she names the privacy as architecture rather than mercy; the first crossing is one sentence Nia chose, with the reason withheld."},
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 62, "end_line": 86, "note": "Ravi's handwritten transfer reason indicts her accurately, she countersigns without arguing, the programme drops to one qualified operator, and Monday's run sheet carries two operator lines she cannot fill."}
    ],
    "finding": "pass",
    "rationale": "The mechanics are dramatized rather than asserted: ninety-one trials in which attention alone never opens transport, an insufficient-integrity result marked as insufficient instead of rounded up, and a retry treated as a second act rather than a repetition. The Anchor cost lands here and is specifically hers, caused by her own unprovable reason, and she declines the argument that would have let her keep him because it would not have been honest. The consequence is material and forward-facing, since losing the second operator is what makes the Consortium's money the only route to a working programme. Ruth's scene supplies warmth that asks nothing, and the chapter ends on an undecided Monday rather than on the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-041",
    "scope": "chapter",
    "chapter_numbers": [41],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 41 POV clarity, Julian Voice_Brief fidelity, participant agency and paid work, overclaim correction, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 12, "end_line": 12, "note": "The opening fact that they charged for the first hour corrects the brochure before anyone speaks."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 36, "end_line": 58, "note": "The work stays visible as work through written corrections, requested repetitions, and a pause to read a paragraph, and Ada authorizes the result without the sentences."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 98, "end_line": 98, "note": "He keeps the invoice in his own file and never shows it to the people writing the brochure, because it would complicate a sentence already agreed."}
    ],
    "finding": "pass",
    "rationale": "This is the batch's clearest statement of what the technology actually is, and it arrives as an invoice rather than an argument: two professionals doing paid work, neither substituting for the other. The four brochure claims are each defeated on a specific mechanism instead of a general objection. Julian's closing self-indictment is the strongest available ending, because his failure is not an act but a withheld document. One matter is recorded rather than waived: the penultimate paragraph restates the declared Hook closely. It is retained because the chapter does not end there, the final beat is the withheld invoice, and the sentence performs a real institutional act rather than labelling the chapter.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-042",
    "scope": "chapter",
    "chapter_numbers": [42],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Chapter 42 POV clarity, Nia Voice_Brief fidelity, DEC-007 refusal of both origin accounts, unspoken irony under CUT-CALIBRATION-AND-THE-UNCALIBRATED, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 38, "end_line": 42, "note": "The single enumerated absence describes the uncalibrated event, and the comparison is allowed to yield a vocabulary and explicitly not a source."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 94, "end_line": 102, "note": "She refuses the enrollment without denying the benefits, tells the representative to write the need as a need, and reads two idle bands as privacy rather than failure."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 106, "end_line": 106, "note": "The closing beat moves the irony onto everyone who questions her and hopes the vocabulary will become evidence."}
    ],
    "finding": "pass",
    "rationale": "Nia's new precision about consented speech is exactly what lets her refuse the form without denying that the Ferris, dispatch, and calibration results are real, which is what makes the offer difficult rather than deceptive. The enumerated absence appears once and is the chapter's subject, satisfying `DEC-018` clause 6. On the contradiction cut: her statement that the comparison gave her no source is retained deliberately. It is not the cut's irony being spent but `DEC-007` being obeyed, since a Nia who let the vocabulary drift toward proof would contradict her refusal of both accounts. The irony is preserved and relocated to the final line, where other people are the ones hoping her fluency will settle the winter.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-036-042",
    "scope": "batch",
    "chapter_numbers": [36, 37, 38, 39, 40, 41, 42],
    "batch_id": "BATCH-PRIVATE-DEFENSE-036-042",
    "criterion": "Batch judgment: freely chosen benefit and calibration, POV transition value, Cross Cut clarity, pacing, Hook variety, warmth and human cost, adversary agency, technical consequence staging, originality, and amended DEC-020 anti-formula quality",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 34, "end_line": 52, "note": "The benefit enters as a joke and a professional reason, not as temptation."},
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 72, "end_line": 82, "note": "A participant argues for recording from his own injury, and the default is refused on the order of the answers rather than on the merits of his wish."},
      {"path": "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "start_line": 48, "end_line": 50, "note": "The counterforce concedes every protection and keeps the queue, which is institutional power in its real form."},
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 62, "end_line": 78, "note": "The Anchor loses her only corroborating operator through her own recorded act."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 12, "end_line": 12, "note": "An invoice reframes clinical participants as paid professionals."}
    ],
    "finding": "pass",
    "rationale": "The batch discharges task 13.2's substantive obligation: medical, linguistic, and emergency benefits are dramatized as work people choose for stated reasons, and calibration is built through voluntary repeated sessions that visibly belong to the two people who built them. Deliberate sends and private mentation hold from the first useful exchange, including the moment a participant catches the operator resolving more field than transport requires. The cross-cut against saleable language is carried by documents that exist in the scene rather than by narration, and no chapter overclaims metadata or invents a transcript. Momentum is generated by consequence: a torn form and a Thursday deadline, a withheld specification, a transfer request, a queue nobody's rules reach. Viewpoint changes always add position, and endings differ in kind across an undecided drive, a shortened answer in a doorway, a dated ultimatum, an unread document, an unfilled run sheet, a withheld invoice, and a noticed hope. Warmth appears four times through Ruth, Joss, a vending-machine vote, and a squeaking chair, and never once functions as an exposition audience or a route to absolution. Nothing is present for compliance: no interrupted cut, short chapter, or location excursion is inserted as a token, and the aphorism habit is thinned enough that lines like `Directions are not participants` are shown failing in later rooms rather than landing as authorial wisdom. The register remains this project's own, and Chapter 62's first reported pattern is protected because Ravi's single Thursday is explicitly not a series.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:07:07Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-036",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [36], "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 36, covering the recovered arrival thread, the two-person layer class, and DEC-012 register discipline."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-036"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-037",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [37], "documents": ["chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 37, covering the unoffered-mentation boundary, observation-permission correction, and Chapter 62 boundary."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-037"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-038",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [38], "documents": ["chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 38, covering bounded operational benefit, the recording-default refusal, and the consequence-bearing clock."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-038"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-039",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [39], "documents": ["chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 39, covering calibration as relationship, the five definitions, and the withheld specification."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-039"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-040",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [40], "documents": ["chapters/private-defense-part/private-defense-part-040-first-calibration.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 40, covering deliberate-send mechanics, refusal of guessed completion, and the Anchor's personal cost."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-040"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-041",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [41], "documents": ["chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 41, covering participant agency, paid professional work, and the four corrected overclaims."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-041"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-042",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [42], "documents": ["chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 42, covering DEC-007 refusal of both origin accounts and the preserved contradiction-cut irony."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-042"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-PRIVATE-DEFENSE-036-042",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [36, 37, 38, 39, 40, 41, 42], "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First Chapters 36–42 drafting-batch editorial gate, discharging the human review task 13.2 left open. All chapter and batch findings pass. This gate does not approve the Private_Defense_Part movement."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-036", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-037", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-038", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-039", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-040", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-041", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-042", "EDITORIAL-PRIVATE-DEFENSE-BATCH-036-042"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:07:07Z"
  }
]
```
## Private Defense Chapters 43–49 editorial review

This batch had neither objective nor editorial records until now; the objective set was recorded as backfill immediately before this review. It carries the April term sheet, the page-nine reveal, Mara's refusal, and Nia's appearance as an illustrative harm case. One voice-separation defect was found across it and repaired inside the pass.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-043",
    "scope": "chapter",
    "chapter_numbers": [43],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 43 POV clarity, Mara Voice_Brief fidelity, canon fidelity of the April arrival, adversary agency, temptation without villainy, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 12, "end_line": 12, "note": "The canonical April arrival is stated plainly as a term sheet and a pen, with the aligned pen becoming the chapter's recurring physical object."},
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 50, "end_line": 50, "note": "The offer's most seductive sentence is delivered by the least invested person in the room, and Mara records that it did not repel her."},
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 122, "end_line": 134, "note": "Dalby argues that both rules have a body in them, nobody helps Mara with it, and she neither signs nor leaves."}
    ],
    "finding": "pass",
    "rationale": "The chapter earns its long-outlier length because it is the movement's hinge and because the temptation is argued at full strength rather than summarized. Dalby's ambulance hypothetical is the strongest argument made against Mara anywhere in the delivered book, and the chapter's integrity rests on leaving it unanswered. Mara's honesty is exact and costly: she names the money, the unpaid hours Anand has been absorbing, and the fact that funding was not the whole reason, then admits she wanted the promise to be true. `DEC-002` holds, since the December morning is recalled as reception of an ordinary living field and the later bench path remains a separate act whose effect she cannot establish. The closing beat is self-documentation rather than Hook restatement, and it is damning: nobody stopped her reading the binder.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-044",
    "scope": "chapter",
    "chapter_numbers": [44],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 44 POV clarity, Julian Voice_Brief fidelity, unspoken irony under CUT-CONSTRAINABLE-CLAUSE, adversary agency, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "start_line": 12, "end_line": 12, "note": "The opening admits the chapter's error as a working assumption rather than announcing its conclusion: he negotiated as if the problem had agreed to fit inside the clause."},
      {"path": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "start_line": 44, "end_line": 46, "note": "The paragraph becomes ugly and useful, and Julian records that he and Dalby were enjoying each other while assembling something neither would defend alone."},
      {"path": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "start_line": 78, "end_line": 108, "note": "He notes that he should have followed the product director's eyes, and the chapter ends on the specification eighteen inches away that Mara opened and he did not."}
    ],
    "finding": "pass",
    "rationale": "The chapter dramatizes competence as the failure mode, which is a harder and better choice than incompetence or bad faith. Its irony is carried by staging rather than commentary: the clause tightens, the initials accumulate, and the binder sits within reach the entire time. Retrospective narration marks his blind spot without disclosing what page nine says, so the reveal remains Chapter 45's to make and nothing is coyly withheld from a reader. Dalby is a genuine counterpart who repairs his cross-reference before using it, which makes the courtesy between them part of the indictment. The closing three sentences are the strongest available ending and do not restate the Hook.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-045",
    "scope": "chapter",
    "chapter_numbers": [45],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 45 POV clarity, Mara Voice_Brief fidelity, MOT-CHAIN-02 function, page-nine canon discipline, microchapter compression, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 12, "end_line": 22, "note": "The specification's own structure hides the finding, and the canonical line arrives as one printed control halfway down a receive-state table."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 28, "end_line": 38, "note": "The page is explicitly barred from reaching backward into December, and the danger is relocated to a present architectural intention."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 58, "end_line": 58, "note": "The chapter ends on Julian stopping writing rather than on any explanation of what that means to him."}
    ],
    "finding": "pass",
    "rationale": "The microchapter compression is earned: a single printed line is the event, and expansion would dilute it. Canon discipline is exact, since the chapter states three times over that page nine proves neither December transmission nor causation of Nia's wanting, and it names guilt as the thing that would like to treat a specification as evidence. `MOT-CHAIN-02` performs its ledgered escalation by turning the spectrum-to-bone chain bidirectional without asserting that anyone has been written to. On the declared contradiction cut: Mara does state the gap between Julian's clause and the specification's waiting state, and that is retained deliberately. She is holding both documents, and requiring her not to recognize what she is reading would be the artificial withholding this project forbids. The cut's irony belongs to Julian and is preserved, because the chapter ends by letting the reader watch him understand instead of explaining him.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-046",
    "scope": "chapter",
    "chapter_numbers": [46],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 46 POV clarity, Julian Voice_Brief fidelity, capability-versus-use reversal, December apparatus continuity, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 12, "end_line": 46, "note": "The five-item list traces shared clock, address resolution, outbound modulation, software suppression, and controller-initiated state change, ending in the admission that he negotiated a rule for a switch and called it a lock."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 74, "end_line": 74, "note": "Both machines are called receivers and only one is, which preserves Mara's December apparatus as physically incapable of the act."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 102, "end_line": 110, "note": "The margin note admits no clause can produce the remedy, and the chapter closes on nodes already in manufacture while four people agree about permission."}
    ],
    "finding": "pass",
    "rationale": "This is the movement's central argument delivered as mechanism: the write path is not an optional module, so a promise cannot make a node incapable, and the protection Julian obtained governs use of an architecture already built for entry. The chapter is careful in exactly the places it must be, stating that the binder supplies no retroactive event, changes nothing about the December machine, identifies no source for Nia's certainty, and makes neither origin account more enterable. Dalby's reply that they never represented the absence of capability is institutional power at its most ordinary and least villainous. Mara's observation that these people read her bench work and drew the opposite conclusion from it is the batch's best single line, and it belongs to her rather than to Julian.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-047",
    "scope": "chapter",
    "chapter_numbers": [47],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 47 POV clarity, Nia Voice_Brief fidelity, DEC-007 refusal of both origin accounts, institutional consequence, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 12, "end_line": 28, "note": "She reads the binder in her coat, records the training-desk consequence of not enrolling, and counts the forty-one words of Case B."},
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 58, "end_line": 58, "note": "The de-identification that removed the need to ask her is the same one that removes her standing to object, and she explicitly declines to call it a trick."},
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 70, "end_line": 76, "note": "Dev laminates the yellow strip, and she cannot work out how to claim Case B without handing over the rest of herself."}
    ],
    "finding": "pass",
    "rationale": "The chapter converts the enrollment refusal into a material cost — a console lost, four steps further from where units move — so Chapter 38's clock expires with consequence rather than commentary. Her forensic separation of the first four accurate sentences from the fifth is the most precise piece of evidentiary reasoning in the movement, and *consistent with* doing the work of *caused by* while keeping its coat on is her own idiom rather than an authorial epigram. `DEC-007` holds without softening: two accounts, neither with evidence inside her decision, and no relief from either. The stile image refuses villainy while describing a mechanism that harms, and the laminated strip is a small human act that will outlive the ticket. The closing question is genuinely unresolved and costs the reader nothing in withheld fact.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-048",
    "scope": "chapter",
    "chapter_numbers": [48],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 48 POV clarity, Mara Voice_Brief fidelity, refusal with real cost, adversary agency, institutional record behavior, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 12, "end_line": 26, "note": "She drafts and times the ninety-one words in advance, then delivers a refusal built entirely from mechanism, including her own unestablished bench act."},
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 42, "end_line": 52, "note": "Dalby makes the two-in-the-morning argument and Mara concedes she is probably right; the clinical director prices the refusal in her patient and asks for it in the summary."},
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 62, "end_line": 70, "note": "She performs the cost arithmetic aloud so it is a decision rather than a gesture, then ends holding an accurate dated page with no custodian."}
    ],
    "finding": "pass",
    "rationale": "The refusal is dramatized as expensive rather than admirable. Mara concedes the adversary's argument on the merits and proceeds anyway on a stated preference about which error she can live with, which is character rather than principle. The chapter also makes institutional power visible in its quietest form: a minute-taker producing a summary, a screen angled away, nothing read back. The Anchor cost from Chapter 40 compounds correctly here, since refusing the money is also refusing the second operator, and she says so in the room. The closing image of an unfiled, uncustodied page is the strongest ending in the batch and directly seeds the Trust thread without naming it.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-LOCAL-049",
    "scope": "chapter",
    "chapter_numbers": [49],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Chapter 49 POV clarity, Julian Voice_Brief fidelity, honest accounting of unused remedies, DEC-007 professional-inference split, and Hook effectiveness",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 12, "end_line": 22, "note": "The file is assembled item by item, including his own architecture note and Mara's refusal in her own construction, and the three unused routes are named rather than omitted."},
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 26, "end_line": 28, "note": "He identifies the same sentence he wrote about the December disclosure and states that he notices the correct question and then files it."},
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 36, "end_line": 36, "note": "The retained copy is explicitly not foresight, and he has had to explain that absence of thought to people who wanted it to be suspicion."}
    ],
    "finding": "pass",
    "rationale": "The chapter is a self-indictment conducted through a contents list, which is the most characteristic possible form for Julian. Its integrity lies in naming the funder review, the county governance referral, and the regulator channel as available and declined, with the cost of each stated, so his failure is a choice rather than an oversight. The recognition that he is a man who notices the correct question and files it lands harder because the December parallel is specific. `DEC-007` holds: he records what is institutionally enterable while privately knowing what he did not do. The closing paragraph refuses to let the retained copy become heroism, and the file's legibility is presented as the consolation of a man who mistook completeness for action.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-001",
    "scope": "batch",
    "chapter_numbers": [43, 44, 49, 53],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Voice separation under DEC-018 clause 7: the EDITORIAL-CAL-004 reader-instruction formula reserved to Mara has crossed into Julian's narration and accumulated there",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "start_line": 106, "end_line": 106, "note": "Original text: 'was competence, and I want to be exact about it, because it is the part I am least able to defend.'"},
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 16, "end_line": 36, "note": "Original text carried three instances in one chapter: 'I want to be exact about why I thought two pages was sufficient', 'There were other routes and I want them named', and 'I want to be plain that this was not foresight.'"},
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 96, "end_line": 142, "note": "Mara's two retained instances, which EDITORIAL-CAL-004 expressly permits as her log register."}
    ],
    "finding": "revision",
    "rationale": "`EDITORIAL-CAL-004` identified 'I want to be exact' as a shared generation tic and ruled that only Mara's log register may keep it. A direct count across the delivered chapters found five instances in Julian's narration — one in Chapter 44, three in Chapter 49, and one in Chapter 53 — against two in Mara's. In Julian's mouth the construction is worse than redundant: it announces precision instead of performing it, which is the opposite of a register built from qualified clauses that anticipate a future reader and then break into unqualified admission. Three occurrences inside Chapter 49 also flatten a chapter whose whole subject is an over-complete file. This is `EDITORIAL-REVISION-004` resurfacing in the voice it was supposed to have been cleared from.",
    "requested_action": "Remove the construction from Julian's narration in Chapters 44, 49, and 53 and let the surrounding sentences carry the precision themselves. Retain Mara's instances, which her Voice_Brief supports. Do not substitute a new shared preamble.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": {
      "resolved_at": "2026-09-13T20:57:37Z",
      "action_taken": "Four instances were removed from Julian's narration in Chapters 44 and 49 and replaced with his own constructions: a bare declarative admission, a subordinate clause, and an obligation-framed sentence. Chapter 44's shortened beat was rebuilt to 'That is the part of this I am least able to defend, and I have tried', which keeps the chapter inside the clause-10 band at 1,052 Prose_Words; Chapter 49 became 1,083. Both Chapter_Local_Gates and the 43–49 batch rerun clean. The fifth instance, in Chapter 53, belongs to the Chapters 50–55 batch and is carried there under the standing cadence criterion of EDITORIAL-PRIVATE-DEFENSE-050-055-006.",
      "follow_up_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002",
    "scope": "batch",
    "chapter_numbers": [44, 49],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Follow-up: voice separation under DEC-018 clause 7 after removing the reader-instruction formula from Julian's narration",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "start_line": 106, "end_line": 106, "note": "The admission now stands bare, which is the register the Voice_Brief specifies for his unqualified moments."},
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 22, "end_line": 36, "note": "The named alternatives now arrive as an obligation the file owes, and the retained copy is denied as foresight without a preamble."}
    ],
    "finding": "pass",
    "rationale": "Julian's narration no longer borrows Mara's stance. The repaired sentences are shorter and more characteristic, since his precision now shows in the qualifications and the flat admissions rather than in an announcement that precision is coming. Mara retains the construction twice in Chapter 43, which her brief permits, so the formula once again marks one voice instead of two. One instance remains open in Chapter 53 and is explicitly carried to the Chapters 50–55 batch rather than treated as closed here.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-003",
    "scope": "batch",
    "chapter_numbers": [43, 44, 45, 46, 47, 48, 49],
    "batch_id": "BATCH-PRIVATE-DEFENSE-043-049",
    "criterion": "Batch judgment: April and page-nine canon fidelity, POV transition value, Cross Cut clarity, pacing, Hook variety, adversary agency, bodily and institutional cost, originality, and amended DEC-020 anti-formula quality",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "start_line": 122, "end_line": 122, "note": "The counterforce's best argument is put in Mara's hands unanswered."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 22, "end_line": 38, "note": "One printed control converts a receiver network into a transmitter with a policy without reaching backward into December."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 46, "end_line": 46, "note": "The negotiated protection is revealed as a rule for a switch represented as a lock."},
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 24, "end_line": 28, "note": "The consequence lands on the person the document does not have to ask."},
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 62, "end_line": 70, "note": "The refusal is priced in a lost operator and a page with no custodian."}
    ],
    "finding": "pass",
    "rationale": "The batch is the strongest run in the movement because its reversal is structural rather than announced: an offer nobody can dismiss, a clause competently won, one line of specification that makes the clause worthless, and then the accounting. Canon holds throughout — the April arrival and the page-nine line are preserved exactly, and four separate passages refuse to let page nine become evidence about the December rig or about Nia's wanting. Viewpoint alternates without repetition and every handoff transfers a document plus a new position. Pacing is genuinely varied by need rather than by rotation: a 1,692-word negotiation, a 431-word microchapter that is one page turning, and five chapters at ordinary length. Endings differ in kind across a refusal to sign, an unopened binder, a man stopping writing, nodes in manufacture, an unanswerable question, an uncustodied page, and an unexamined habit. The adversary now acts continuously: booking rooms, withholding a specification, declining a hardware interlock on product identity, harvesting an incident under an information-sharing agreement, and asking for ninety-one words outside the institute. Cost is real and specific — a dead man in an appendix, a lost console, a lost operator, a patient with no daughter in the building — and none of it is spectacle. Nothing appears for compliance, and the two structural outliers exist because their scenes require those shapes.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T20:57:37Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-043",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [43], "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 43, covering the April arrival canon, the unanswered adversary argument, and the long-outlier purpose."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-043"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-044",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [44], "documents": ["chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 44, covering the constrainable-clause irony and the resolved voice-separation criterion."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-044", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-045",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [45], "documents": ["chapters/private-defense-part/private-defense-part-045-page-nine.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 45, covering MOT-CHAIN-02, page-nine canon discipline, and microchapter compression."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-045"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-046",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [46], "documents": ["chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 46, covering the capability-versus-use reversal and December apparatus continuity."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-046"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-047",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [47], "documents": ["chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 47, covering the enrollment consequence, DEC-007 refusal, and the de-identification standing problem."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-047"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-048",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [48], "documents": ["chapters/private-defense-part/private-defense-part-048-the-refusal.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 48, covering the priced refusal, adversary agency, and institutional record behavior."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-048"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-049",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [49], "documents": ["chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First editorial approval gate for revised Chapter 49, covering the named unused remedies, the DEC-007 split, and the resolved voice-separation criterion."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-049", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-PRIVATE-DEFENSE-043-049",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [43, 44, 45, 46, 47, 48, 49], "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "chapters/private-defense-part/private-defense-part-045-page-nine.md", "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First Chapters 43–49 drafting-batch editorial gate. All chapter findings pass and the voice-separation revision raised in this pass is resolved with follow-up evidence, except one instance expressly carried to the Chapters 50–55 batch. This gate does not approve the Private_Defense_Part movement."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-043", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-044", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-045", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-046", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-047", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-048", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-049", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-003"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T20:57:37Z"
  }
]
```
## Private Defense Chapters 50–55 editorial gates and standing-criterion closure

The Chapters 50–55 review recorded eight findings at task 13.4 but never produced an editorial `GateResult` of any scope, so the batch has been carrying evaluated findings with no gate to hold them. Two matters were also left open there: the standing cadence criterion in `EDITORIAL-PRIVATE-DEFENSE-050-055-006`, and the handoff obligation in `EDITORIAL-PRIVATE-DEFENSE-050-055-008`, which Chapter 56 has since discharged.

This section closes the standing criterion against current prose and records the missing gates. It also records a manuscript-scale length finding that only became visible once Chapters 1–49 had been measured against the same rule.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001",
    "scope": "batch",
    "chapter_numbers": [50, 51, 52, 53, 54, 55],
    "batch_id": "BATCH-PRIVATE-DEFENSE-050-055",
    "criterion": "Follow-up on the standing cadence and voice-separation criterion left open by EDITORIAL-PRIVATE-DEFENSE-050-055-006",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 22, "end_line": 22, "note": "Original text carried the reserved reader-instruction formula: 'which I had put off, and I want to be exact about why.' It now reads 'I had put that off, and the reason is not creditable.'"},
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 44, "end_line": 47, "note": "The single retained instance is diegetic: he is placing the order of his own entries into an archive, and the custodian's note that follows is the act it announces."},
      {"path": "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "start_line": 60, "end_line": 72, "note": "The batch's strongest ending still lands on the retained-versus-lost accounting and the test strips behind glass rather than on a maxim."}
    ],
    "finding": "pass",
    "rationale": "The cadence risk that `EDITORIAL-PRIVATE-DEFENSE-050-055-006` carried forward has been closed by subtraction rather than by rewriting. The fifth and last instance of the `EDITORIAL-CAL-004` formula in Julian's narration is gone from Chapter 53, which leaves one occurrence in that chapter whose function is an act inside a record rather than a preamble to the reader. Across Chapters 50 through 55 the paragraph endings now rest on objects, entries, and refusals — a softened minute, a conditions folder she wrote herself, an indexed heading that contradicts its own holding, a forty-one-second recording, test strips behind glass — rather than on balanced antitheses. Chapter 53 remains the batch's best chapter and its ending is unimproved by anything in this pass.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:22:10Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001",
    "scope": "manuscript",
    "chapter_numbers": [19, 35, 51, 52, 53, 54, 55, 57, 58, 59, 60, 118, 124],
    "batch_id": null,
    "criterion": "Whether DEC-018 clause 10's 1,050–1,200 normal-class band is operating as a per-chapter rule or as a budget mechanism, and whether the delivered manuscript satisfies the requirement it exists to protect",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "start_line": 17, "end_line": 41, "note": "At 1,487 Prose_Words this is the longest normal chapter in the manuscript, and the length is spent on Nia reading the closed review and setting her own conditions, which is the batch's load-bearing scene."},
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 40, "end_line": 49, "note": "At 799 Prose_Words this is the shortest normal chapter, and the compression is the point: the blocked send and its rejection occupy seventy-six milliseconds and the chapter refuses to pad around them."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "Safiya's account remains 756 Prose_Words, which is the specific complaint EDITORIAL-REVISION-009 made and the one place where the shortfall still coincides with the manuscript's largest emotional obligation."}
    ],
    "finding": "revision",
    "rationale": "A direct measurement of all 64 delivered files was taken rather than inferred. The manuscript holds 73,147 Prose_Words; the normal class contains 55 chapters with a mean of 1,134.4, inside the 1,000 to 1,185 operative window recorded in `ARC-CHANGE-REVISION-001`; and the current class means project to roughly 143,900 Prose_Words across 128 chapters, comfortably inside the approved 130,000 to 150,000 Final_Targets. The budget clause 10 exists to protect is therefore satisfied with margin. But 13 of the 55 normal chapters fall outside clause 10's per-chapter band in both directions: Chapters 19, 35, 51, 52, 53, and 54 above 1,200, and Chapters 55, 57, 58, 59, 60, 118, and 124 below 1,050. That is not a drafting accident. Chapters 1 through 49 were revised into the band, Chapters 50 through 55 were delivered against `DEC-019` clause 11's earlier 900 to 1,400 band and never re-budgeted, and Chapters 56 through 61 were drafted to the length their scenes required under amended `DEC-020`. Two different rules have been operating at once, and the project cannot record clause 10 as satisfied while a quarter of its normal chapters sit outside it.",
    "requested_action": "Author decision required, and it is a governance choice rather than a prose defect. Either confirm that clause 10 is a budget mechanism judged on the class mean, in which case amend its wording so the band reads as guidance and the 13 chapters are compliant as written; or confirm it is a per-chapter rule, in which case a further pass must bring Chapters 51 through 54 down and Chapters 55 and 57 through 60 up, and that pass will change scenes rather than trim words. Do not resolve this by cutting functioning prose to reach an arithmetic target, which is the practice EDITORIAL-PROPULSION-002-FOLLOWUP-001 already rejected. Chapter 118 is the one case that should be revisited on craft grounds regardless of the governance answer, because EDITORIAL-REVISION-009 identified its brevity as a defect in the manuscript's most important account and it is still 756 Prose_Words.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:22:10Z",
    "resolution": {
      "resolved_by": "DEC-021 and EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001",
      "resolved_at": "2026-09-18T22:10:00Z",
      "action_taken": "DEC-021 preserves every objective length and Final_Target constraint while superseding the 1,050-1,200 and 900-1,400 per-chapter quotas, fixed midpoint, fixed mean windows, and waiver mechanism as gate logic. Existing ArcEntry estimates remain planning metadata and are not mass-normalized. Current measurement after the Chapter 118 repair finds 64 delivered files, 73,604 declared Prose_Words, 55 delivered normal chapters averaging 1,142.7, and a current-class projection of approximately 145,400 across the outline's 109 normal, 10 microchapter, and 9 long-outlier entries, inside Final_Targets. No functioning chapter is padded or cut for arithmetic.",
      "follow_up_finding_id": "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001"
    }
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-050",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [50], "documents": ["chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 50, recorded to close the task 13.4 gap; evidence is the existing batch findings plus the closed cadence criterion."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-051",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [51], "documents": ["chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 51, carrying MOT-RECORD-01. The open manuscript length-band finding is recorded against this chapter."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-052",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [52], "documents": ["chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 52, which releases REVEAL-CASUALTY-CONSEQUENCE. The open manuscript length-band finding is recorded against this chapter."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-053",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [53], "documents": ["chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 53 after removing the last reserved reader-instruction instance from Julian's narration. The open manuscript length-band finding is recorded against this chapter."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-004", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-054",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [54], "documents": ["chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 54, the pre-Trust provenance transfer. The open manuscript length-band finding is recorded against this chapter."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-055",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [55], "documents": ["chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Editorial approval gate for revised Chapter 55, the Anchor instrument cost, whose handoff obligation Chapter 56 has discharged. The open manuscript length-band finding is recorded against this chapter."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-BATCH-PRIVATE-DEFENSE-050-055",
    "gate_type": "editorial",
    "scope": {"chapter_numbers": [50, 51, 52, 53, 54, 55], "documents": ["chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "First Chapters 50–55 drafting-batch editorial gate, recorded to close the task 13.4 gap. Every craft finding in the batch now passes, including the previously standing cadence criterion and the discharged Chapter 56 handoff. The result is revision solely because EDITORIAL-LENGTH-BAND-MANUSCRIPT-001 is open and requires an author decision about DEC-018 clause 10; it is not a defect in this batch's prose."},
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-004", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-006", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-008", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-13T21:22:10Z"
  }
]
```
## Follow-up passes on the nine `DEC-018` revision findings

`EDITORIAL-REVISION-001` through `EDITORIAL-REVISION-009` each now carry a resolution object, and each receives a dated follow-up below that re-evaluates the same criterion against current prose. The originals are unedited and remain the honest record of the state they judged.

Eight criteria pass. One does not: `EDITORIAL-REVISION-009` is only partly discharged, because Chapter 118 is still 756 Prose_Words and still `exploratory`, and it was never inside `ARC-CHANGE-REVISION-001`'s Chapters 1–46 authorization. That is recorded as a further `revision` rather than smoothed into a pass.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-REVISION-001-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 33, 34, 35, 37, 39, 42, 43, 45, 46],
    "batch_id": null,
    "criterion": "Follow-up: closed-loop chapter shape, thesis openings, and final lines that restate the ArcEntry Hook",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 12, "end_line": 12, "note": "Opens on a tap running too hot and a hand stopped inside a cup; the cage is drawn mid-chapter and the ending is a half-true facilities request."},
      {"path": "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "start_line": 12, "end_line": 12, "note": "The three-nouns thesis opening is gone; the chapter now opens on a folder left face down for fifty minutes and closes on a transferred obligation."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 12, "end_line": 58, "note": "Opens on a specification not written to be read in order and ends on Julian stopping writing, with the Hook's assurance-worthless claim never stated."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 12, "end_line": 110, "note": "Opens inside the hardware reference and ends on nodes already in manufacture, replacing the former careful-sentence Hook echo."}
    ],
    "finding": "pass",
    "rationale": "All ten cited chapters were checked directly. None opens by stating its conclusion and none closes on a restatement or near-paraphrase of its own Hook; the four final lines quoted in the original finding are no longer present in the prose. The endings now vary in kind and each leaves something owed. One near-restatement survives, in Chapter 41's penultimate paragraph, and it is recorded in EDITORIAL-PRIVATE-DEFENSE-LOCAL-041 rather than ignored: the chapter does not end there, and the sentence performs an institutional act instead of labelling the chapter.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-002-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [1, 34, 35, 37, 42, 46],
    "batch_id": null,
    "criterion": "Follow-up: forward pressure through legitimate dread and reluctant retrospection, without artificial withholding",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-001-noise-floor.md", "start_line": 64, "end_line": 64, "note": "The chapter still ends on an omission whose cost is signalled without concealing any fact Mara holds: the clause is not on the page, and everything after came with it exactly as she left it."},
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 90, "end_line": 113, "note": "Ravi announces a formal request, withholds something he does not trust the notebook to hold, and is gone by the end of the chapter with the log left rolled."},
      {"path": "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "start_line": 92, "end_line": 92, "note": "The chapter closes on 'Ask me again next week', which is an obligation rather than a resolution."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 110, "end_line": 110, "note": "The largest reversal in the movement generates an unmet obligation, since the nodes are in manufacture while the parties agree about permission."}
    ],
    "finding": "pass",
    "rationale": "Chapter 1's register was preserved rather than reconstructed, and it remains the model the finding named: a retrospective narrator marking that a decision cost something without naming the later fact. Each formerly closed chapter now carries a live question past its boundary, and in every case the pressure comes from consequence or dread rather than from concealment. Chapter 35 in particular no longer spends its arrival in a summary sentence; the unrecognized car becomes twelve counted cases and a technician who leaves mid-sentence. Requirements 2.13 and 2.14 remain satisfied, since no narrator withholds a fact they hold.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-003-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [32, 34, 40, 42, 44, 45],
    "batch_id": null,
    "criterion": "Follow-up: dramatic irony in the declared contradiction-cut relationships 32/34, 40/42, and 44/45",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 44, "end_line": 47, "note": "Nia no longer states that she cannot be safe and take the call; she leaves the enclosure and works the call from the corridor floor."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 38, "end_line": 42, "note": "She describes the uncalibrated event and allows the comparison to yield a vocabulary and explicitly not a source, which is DEC-007 compliance rather than the cut's irony."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 38, "end_line": 58, "note": "Mara names the gap between clause and specification while holding both, and the chapter ends by letting the reader watch Julian understand."}
    ],
    "finding": "pass",
    "rationale": "Two of the three pairs are cleanly repaired by subtraction: Chapters 34 and 42 now hold only their own positions, and the incompatibility is assembled by the reader from events. The third pair is judged rather than mechanically cleared. Chapter 45's recognition is retained because Mara physically holds the initialed clause and the specification at the same moment, and a narrator who failed to notice what she was reading would be coy in exactly the way this project bans. The irony of that cut belongs to Julian, and it is preserved intact, because Chapter 44 ends with the binder eighteen inches from his hand and Chapter 45 ends on him stopping writing rather than on any explanation of him.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-004-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 34, 39, 42, 44, 49, 53, 118],
    "batch_id": null,
    "criterion": "Follow-up: POV distinctness and voice separation carried structurally rather than by domain vocabulary",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 50, "end_line": 50, "note": "One enumerated absence, in the chapter whose subject is whether anything arrived."},
      {"path": "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "start_line": 38, "end_line": 38, "note": "The second and last instance in Chapters 30 through 61, again where the absence is the subject."},
      {"path": "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "start_line": 22, "end_line": 36, "note": "Julian's three reader-instruction preambles were replaced with a subordinate clause, an obligation-framed sentence, and a bare denial."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "Safiya's register remains the reference standard: second-person address, a paper map, a kettle with a whistle, one invented private word."}
    ],
    "finding": "pass",
    "rationale": "The named construction was counted rather than estimated. The enumerated absence has fallen from eleven instances across three registers to two, one in Mara's voice and one in Nia's, each where the absence is the chapter's subject and therefore permitted by DEC-018 clause 6. More importantly, the criterion proved live during this pass: a second shared formula, the reserved 'I want to be exact' preamble, had colonized Julian's narration five times against Mara's two, and it was removed from Chapters 44, 49, and 53 so the formula again marks one voice. The three registers are now separated by sentence shape and by what each narrator notices — Mara by mechanism and control, Nia by sequence and evidentiary limit, Julian by qualification breaking into flat admission — rather than by specialist nouns.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-005-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 34, 36, 38, 40, 42, 43],
    "batch_id": null,
    "criterion": "Follow-up: human cost, tenderness, and warmth, and whether any POV lead remains flatter than the supporting cast",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 88, "end_line": 88, "note": "Ruth puts soup in front of Mara and takes the notebook out of her hands to make room for the bowl."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 54, "end_line": 57, "note": "A supervisor sits on the corridor floor, the vending machine has been rigged by vote, and four minutes require no verification."},
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 94, "end_line": 94, "note": "Joss feeds Nia in a van with the heater going and does not ask what she does all day."},
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 84, "end_line": 84, "note": "Ruth's 'I have a bed. That's the difference between us' is humour that is not a professional riposte."}
    ],
    "finding": "pass",
    "rationale": "The ordering the finding objected to has been reversed. Mara and Nia now have private lives on the page: food is offered and accepted repeatedly, two relatives ask nothing about the work, and the jokes are domestic rather than forensic. Crucially neither Ruth nor Joss functions as an exposition audience or a route to absolution — Ruth explicitly never asks, and Joss's one question about the technology is whether it can tell that Nia is tired. Julian receives no new relationship, as the finding required, and clause 9 reaches him inside shared scenes instead, most clearly in his afternoon of enjoying Dalby's company while assembling something neither would defend alone.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-006-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 35, 37, 40, 43, 48],
    "batch_id": null,
    "criterion": "Follow-up: personal, non-abstract cost for the Anchor POV inside Private_Defense",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "start_line": 90, "end_line": 90, "note": "Ravi asks for his name off the page and states he will file a formal request."},
      {"path": "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "start_line": 62, "end_line": 78, "note": "The handwritten transfer reason indicts her accurately, she countersigns rather than argue, and the programme drops to one qualified operator."},
      {"path": "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "start_line": 62, "end_line": 62, "note": "Refusing the money is also refusing the second operator, and she performs that arithmetic aloud in the room."}
    ],
    "finding": "pass",
    "rationale": "The cost is small, specific, and caused by Mara's own recorded act rather than by the Foreign_Signal or by an adversary. It is also genuinely hers to lose: Ravi is the only person who independently reproduced her December timing and told her when her model was contaminated, so losing him halves the verification of everything she takes out of the shielded room. The chapter 40 scene refuses the easy version, since she declines to argue because arguing would not be honest. The cost then compounds correctly in Chapter 48 without colliding with or pre-empting the Chapter 55 instrument loss or the Chapter 112 shutdown, and Ravi's departure is not an injury or a casualty.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-007-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [30, 31, 32, 35, 36, 40],
    "batch_id": null,
    "criterion": "Follow-up: development of the exposed-persons list and the car at the Northline Array gate",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 54, "end_line": 76, "note": "The list is created and immediately contested, and Ravi's objection that on that logic everyone at Northline belongs on it is spoken to Mara's face."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 80, "end_line": 83, "note": "Nia cannot get her name removed, so she attacks how the page will read to a stranger in five years and makes Mara date it and annotate it."},
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 12, "end_line": 18, "note": "The gate visitor book identifies the car as the Consortium advance party, booked by a group entitled to book it on a page where Mara's group does not appear."}
    ],
    "finding": "pass",
    "rationale": "Both threads now carry consequence rather than atmosphere. The list becomes a live moral object handled by four people across five chapters and ends by costing Mara her second operator, which is the strongest possible use of the technician's original objection. The car is answered in the least dramatic and most damning register available: an ordinary ledger entry proving that nobody needed the site lead's permission. Neither development invents a conspiracy, and the technician's later single report is explicitly kept from becoming the first reported pattern of arrivals in strangers, which remains Chapter 62's.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-008-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [36, 41, 118],
    "batch_id": null,
    "criterion": "Follow-up: preparation for the Coda's emotional payload without moving Safiya or pre-empting her reveal",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 26, "end_line": 26, "note": "Lena names the layer as theirs, several hundred words made in a kitchen, unwritten, and held by no calibration."},
      {"path": "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "start_line": 12, "end_line": 36, "note": "The same pair are shown as paid professionals whose shared practice is a working asset, which establishes the class as a real thing with value."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "Safiya's account remains untouched, with heritage_base unspecified, one invented private word, and no foreshadowing anywhere earlier."}
    ],
    "finding": "pass",
    "rationale": "The class of private two-person layer is now established twice before the Coda, in a register that makes its loss legible in advance without spending it: the Ferris layer is intact, unwritten, uncopyable, and explicitly not transferable by calibration. No connection is drawn between Ada or Lena and Safiya, `DEC-003` is unweakened, and `REVEAL-SAFIYA-TUESDAY-LOSS` still releases at Chapter 118 with `POV-SAFIYA` as owner. Safiya was not moved and no chapter was added for her. The pass is limited to the Private_Defense half of the requested action; the Chapters 109 to 114 obligation to make uncounted private civilian loss vivid is a forward planning obligation on undrafted chapters, recorded in the Mindwars and Coda movement sections, and it is not evaluated here because the prose does not exist.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-009-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [4, 24, 31, 34, 118],
    "batch_id": null,
    "criterion": "Follow-up: chapter scale, and whether loaded scenes are now inhabited rather than named",
    "prose_locations": [
      {"path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "start_line": 58, "end_line": 58, "note": "At 1,181 Prose_Words the chapter now stays with the four seconds it once gestured at, and ends on the part of the day nobody kept."},
      {"path": "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "start_line": 36, "end_line": 39, "note": "At 1,148 Prose_Words the first measured silence is inhabited through jaw, hands, and the space behind the eyes rather than resolved into an epigram."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 20, "end_line": 23, "note": "The remembered two-calls death is now given the binder, the closed cover, and the hands on it instead of five words."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 20, "note": "Safiya's account is still 756 Prose_Words and still exploratory, which is the exact condition the original finding objected to."}
    ],
    "finding": "revision",
    "rationale": "Four of the five cited chapters are repaired. Chapters 4, 31, and 34 now sit inside the clause 10 band and spend their length on the moments the finding said were named and left, and Chapter 24 remains a declared microchapter whose compression is its function. The manuscript-level arithmetic is also sound: 73,147 Prose_Words across 64 delivered files, a normal-class mean of 1,134.4, and a projection near 143,900 across 128 chapters, inside the approved 130,000 to 150,000. The finding cannot pass because its sharpest example is untouched. Chapter 118 carries the Coda's whole emotional payload in 756 Prose_Words, fewer than any delivered normal chapter except Chapter 124, and it was never inside `ARC-CHANGE-REVISION-001`'s Chapters 1 to 46 authorization, so no wave has been responsible for it. A second condition also emerged that the original could not have seen: thirteen normal chapters now fall outside the clause 10 band in both directions, because Chapters 50 to 55 were delivered under the earlier `DEC-019` band and Chapters 56 to 61 were drafted to scene need.",
    "requested_action": "Two separable actions. First, authorize a Coda pass for Chapter 118 that inhabits the Tuesday at greater length without adding an arrival, naming a real heritage base, quoting the private layer, or disturbing MOT-KETTLE-01 and the 118–119 reveal window; the chapter's material plainly supports it, since the layer's forty-year construction, the third that is gone, and the interpreting work are each stated once and could each be lived. Second, decide the clause 10 governance question recorded in EDITORIAL-LENGTH-BAND-MANUSCRIPT-001 before any further length pass, so the two rules stop operating at once.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:32:24Z",
    "resolution": {
      "resolved_by": "DEC-021, the Chapter 118 craft expansion, and EDITORIAL-REVISION-009-FOLLOWUP-002",
      "resolved_at": "2026-09-18T22:10:00Z",
      "action_taken": "The governance condition was closed by DEC-021 without padding or cutting any chapter. Chapter 118 was then expanded from 756 to 1,215 observed Prose_Words on craft grounds: the revision inhabits the forty-year domestic construction of the private layer, the Tuesday room and body sequence, the failed retrieval, intact public interpreting work, sole-survivor grief, and Mara's observable restraint. It preserves Safiya's voice, exploratory status, existing reveal and motif, unspecified heritage base, one invented private token, and Chapter 119's lexical work.",
      "follow_up_finding_id": "EDITORIAL-REVISION-009-FOLLOWUP-002"
    }
  }
]
```

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-REVISION-PASS-002",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [1, 4, 24, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 53, 118],
    "documents": ["planning/decisions.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/motif-ledger.md", "planning/editorial-log.md", "planning/gate-results.md"],
    "description": "Rerun of the DEC-018 revision-pass editorial gate against current prose. Eight of the nine findings are resolved with follow-up passes; EDITORIAL-REVISION-009 is partly discharged and remains revision because Chapter 118 is unchanged at 756 Prose_Words and outside the original authorization. GATE-EDITORIAL-REVISION-PASS-001 is retained unedited as the historical record of the state it evaluated."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-REVISION-001-FOLLOWUP-001", "EDITORIAL-REVISION-002-FOLLOWUP-001", "EDITORIAL-REVISION-003-FOLLOWUP-001", "EDITORIAL-REVISION-004-FOLLOWUP-001", "EDITORIAL-REVISION-005-FOLLOWUP-001", "EDITORIAL-REVISION-006-FOLLOWUP-001", "EDITORIAL-REVISION-007-FOLLOWUP-001", "EDITORIAL-REVISION-008-FOLLOWUP-001", "EDITORIAL-REVISION-009-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
  "result": "revision",
  "checker_exit_status": null,
  "timestamp": "2026-09-13T21:32:24Z"
}
```
## Discovery_Part movement gate — prerequisite audit after the `DEC-018` revision

`ARC-CHANGE-REVISION-001` requires the Discovery movement Editorial_Gate to be re-recorded against revised prose before any of Chapters 1 through 29 returns to `approved`. All twenty-nine are currently `revised`, so no record presently overstates their status.

That re-recording cannot honestly be produced yet, and the reason is evidentiary rather than editorial. `GATE-EDITORIAL-DISCOVERY-MOVEMENT-001` and the twenty-nine `EDITORIAL-DISCOVERY-LOCAL-*` findings beneath it all evaluated pre-`DEC-018` text. Every one of those chapters has since been rewritten at its opening and closing and re-budgeted for length, which is precisely the class of change the editorial workflow calls a Substantive Prose Change, so that evidence is stale by the log's own rule. Current evidence exists for only five of the twenty-nine: Chapters 25 and 26 through their horizon-repair findings, and Chapters 1, 4, and 24 through the targeted checks made during the `DEC-018` follow-up pass.

Recording a movement pass on twenty-four chapters nobody has read in their current form would be the exact failure this log is built to prevent. The gate below therefore reports `incomplete` and names the missing work.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
    "documents": ["planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/editorial-log.md", "planning/gate-results.md"],
    "description": "Prerequisite audit for re-recording the Discovery_Part movement Editorial_Gate against revised Chapters 1–29. Current chapter-level craft evidence exists only for Chapters 1, 4, 24, 25, and 26. The twenty-nine task 12.7 chapter findings and GATE-EDITORIAL-DISCOVERY-MOVEMENT-001 evaluated pre-DEC-018 prose and are retained unedited as historical. No movement verdict is asserted and no chapter is returned to approved."
  },
  "prerequisite_state": "incomplete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-DISCOVERY-025-HORIZON-RERUN-001", "EDITORIAL-DISCOVERY-026-HORIZON-RERUN-001", "EDITORIAL-REVISION-001-FOLLOWUP-001", "EDITORIAL-REVISION-002-FOLLOWUP-001", "EDITORIAL-REVISION-009-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
  "result": "incomplete",
  "checker_exit_status": null,
  "timestamp": "2026-09-13T21:42:42Z"
}
```

### What the Discovery movement gate still requires

- A continuous read of the current Chapters 1 through 29 and a fresh chapter finding for each of the twenty-four without one, covering POV clarity, Voice Brief fidelity, continuity, and Hook effectiveness against the revised text.
- Fresh batch-level findings for the five Discovery batches, since the existing batch findings also rest on superseded prose.
- Current movement findings for the twelve criteria carried by `EDITORIAL-DISCOVERY-MOVEMENT-001` through `-012`, in particular the receive-only December continuity, the separation of the later bench path, and the page-nine chronology, all of which the revision pass could in principle have disturbed and none of which has been re-verified end to end.
- Objective chapter and batch reruns for Discovery, which have not been recorded since the revision changed those files; only Chapters 25 and 26 and their two affected batches have current objective results.
- A decision on `EDITORIAL-LENGTH-BAND-MANUSCRIPT-001`, because Chapter 19 sits outside the clause 10 band and any length pass would change these files again.

This is a substantial pass in its own right and it is not a prerequisite of the Private_Defense_Part movement gate at task 13.6, which evaluates Chapters 30 through 61. It is a prerequisite of task 14, which requires both movements approved.
## Task 13.6 — Private_Defense_Part movement Editorial_Gate

Every prerequisite the earlier prerequisite audit found missing has now been supplied. All thirty-two Private Defense chapters carry current chapter findings and current chapter editorial gates; all five batches carry batch findings and batch editorial gates; objective chapter and batch results are current for every file after the repairs made in this pass; and the nine `DEC-018` findings and `EDITORIAL-PROPULSION-005` have been resolved with follow-up evidence. `GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001-INCOMPLETE` is superseded and retained unedited.

The movement gate below is `revision` rather than `pass`. That verdict rests on one open item, and it is a governance decision rather than a defect in the prose: `EDITORIAL-LENGTH-BAND-MANUSCRIPT-001` records that two length rules have been operating at once, leaving Chapters 35 and 51 through 55 outside the `DEC-018` clause 10 band while the manuscript's own budget arithmetic is satisfied. Every craft criterion task 13.6 assigns passes on current evidence.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-PROPULSION-005-FOLLOWUP-001",
    "scope": "movement",
    "chapter_numbers": [33, 35, 36, 38, 39, 40, 43, 46, 47, 48, 55, 61],
    "batch_id": null,
    "criterion": "Follow-up: adversary agency beyond argument, and setting variety without checklist rotation",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "start_line": 12, "end_line": 18, "note": "The Consortium takes a room at the site Mara runs, booked by development, in a ledger anyone could read, on a page where her group does not appear."},
      {"path": "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "start_line": 12, "end_line": 46, "note": "The refusal of a hardware interlock is an act with consequence, made on product identity rather than on impossibility."},
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 24, "end_line": 58, "note": "Nia's incident is harvested into an appendix under an agreement that required nobody to ask her, and the de-identification removes her standing to object."},
      {"path": "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "start_line": 54, "end_line": 57, "note": "A corridor floor, machine coffee, and a rigged vending machine, none of it professional and none of it inserted to satisfy a setting requirement."}
    ],
    "finding": "pass",
    "rationale": "Imogen Dalby no longer only argues. She books a room without permission, plants an enabled-by-default box, withholds a specification while accepting every protection that does not reach it, declines an interlock, and asks for Mara's ninety-one words outside the institute. Beyond her, institutional power acts in its truest form throughout the movement — proceeding without you — through closed enrollment that costs Nia her console, an appendix that needs no consent, an access list reissued on the fourth, and a manufacturing schedule that started before the meeting. No concealed villain, sender connection, unmasking, or adversary POV was created to achieve this. Setting variety arrived as a by-product of the warmth obligation rather than as a location quota: the noninstitutional scenes exist because Mara had nowhere else to go at eleven at night and because Joss's van was already that side of the river.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:42:42Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001",
    "scope": "movement",
    "chapter_numbers": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61],
    "batch_id": null,
    "criterion": "Movement turn, canon fidelity, motif progression, institutional chronology, DEC-007 attribution split, Nia's refusal of both origin accounts, and whether a valid ethical rule remains a physically inadequate answer rather than a villain declaration",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "start_line": 29, "end_line": 33, "note": "The movement's rule is established by refusing the better-measuring sealed enclosure, so the ethic costs performance from the start."},
      {"path": "chapters/private-defense-part/private-defense-part-045-page-nine.md", "start_line": 28, "end_line": 38, "note": "The capability reveal is barred from reaching backward into December and relocated to a present architectural intention."},
      {"path": "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "start_line": 22, "end_line": 44, "note": "Julian records the institutionally enterable heading while entering a custodian's note that no material in the archive supports it, which is the DEC-007 split performed rather than asserted."},
      {"path": "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "start_line": 85, "end_line": 122, "note": "The completed rule meets public consequences it cannot reach, and Mara can no longer ask the array what accompanied them."}
    ],
    "finding": "pass",
    "rationale": "The movement performs its declared turn: a physical boundary is invented, proved, priced, offered for sale, defended in language, defeated by architecture, refused at cost, and finally written as a protocol that is correct and insufficient. Copper spreads and cannot restore public life, which is stated by the arithmetic of who can reach a room rather than by a narrator. Canon holds at every load-bearing point — the December apparatus stays receive-only, the later bench path stays a separate act, page nine stays architectural capability, Trust activity is never backdated, and the casualty consequence releases with Nia owning it. Motifs perform their ledgered functions once each: `MOT-COPPER-01` as relief and measurement, `MOT-CHAIN-02` as the chain turning outward, `MOT-RECORD-01` in Chapter 51, `MOT-COME-02` in Chapter 61, with `MOT-KNOCK-01` preserved for Chapter 73. `DEC-007` is exact throughout: Mara's conviction stays private and unsupported, Julian enters an inference professionally while noting it is one, and Nia refuses both accounts through to Chapter 61 without receiving or granting absolution. Chapters 36 through 42 establish freely chosen benefit and pair-specific calibration through people with stated professional reasons. Chapters 56 through 61 make Fluent_Pairing clear, send-gated, revocable, and failure-aware without exposing background thought, guessing completions, or overclaiming metadata. Technical information arrives through action and consequence rather than exposition set pieces, and the register is the project's own rather than an imitation of either named inspiration.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:42:42Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002",
    "scope": "movement",
    "chapter_numbers": [30, 34, 35, 37, 38, 40, 42, 43, 46, 47, 48, 55, 57, 59, 61],
    "batch_id": null,
    "criterion": "Amended DEC-020 contextual judgment: consequence-bearing propulsion, variety of ending, scene form, length and setting without checklist rotation, earned rather than inserted technique, viewpoint allocation, bodily stakes, and the clause 10 named tics",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "start_line": 94, "end_line": 98, "note": "A dated clock with an irreversible external consequence: Thursday, and a console she can keep only by signing."},
      {"path": "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "start_line": 12, "end_line": 12, "note": "That clock expires off the page and the cost is already in force when the next Nia chapter opens."},
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 40, "end_line": 49, "note": "The shortest chapter in the movement is short because its event lasts seventy-six milliseconds."},
      {"path": "chapters/private-defense-part/private-defense-part-030-something-came-in.md", "start_line": 12, "end_line": 20, "note": "The one arrival that happens to a body in this movement is a certainty at a sink with a tap still running, and it is never confirmed as external."}
    ],
    "finding": "pass",
    "rationale": "Judged contextually across the batch, movement, and manuscript as amended Requirement 15.9 now requires, without applying the withdrawn counts. Propulsion is consequence-bearing rather than deliberative: the movement's clocks are an enrollment deadline that costs a console, a transfer effective at month end that halves verification, an access list reissued on the fourth, and a manufacturing schedule that predates the negotiation. Endings vary across roughly a dozen kinds and no rotation is detectable. Lengths are set by scene: two long outliers for the negotiation and the movement close, one microchapter that is a single page turning, and the rest at ordinary length, including four chapters in the fifties and one at 799 words whose compression is dramatic rather than budgetary. No interrupted cut, short chapter, or noninstitutional excursion appears as a compliance token. Viewpoint allocation produces no document trough: the longest single-viewpoint run is two chapters, and institutional paperwork is always answered within a chapter or two by a body in a corridor, a van, or a car park. The clause 10 named tics were measured rather than estimated and two accumulations were found and repaired in this pass. The movement's real weakness is one the book chooses: outside Chapter 30's sink and the fire in Chapter 38, nobody is in physical danger, and that is correct here because `DEC-020` clause 5 assigns bodily stakes to Chapters 62 through 112 rather than to this movement.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-13T21:42:42Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002",
  "gate_type": "editorial",
  "scope": {
    "chapter_numbers": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61],
    "documents": ["planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/decisions.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/editorial-log.md", "planning/gate-results.md"],
    "description": "Task 13.6 Private_Defense_Part movement Editorial_Gate on current prose. Prerequisites are complete: all 32 chapters and all 5 batches carry current findings and gates, objective results are current after this pass's repairs, and the nine DEC-018 findings plus EDITORIAL-PROPULSION-005 are resolved with follow-up evidence. Every assigned craft criterion passes. The result is revision solely because EDITORIAL-LENGTH-BAND-MANUSCRIPT-001 remains open and requires an author decision on DEC-018 clause 10. Supersedes GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001-INCOMPLETE, retained unedited. No chapter or batch is returned to approved by this record."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001", "EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002", "EDITORIAL-PROPULSION-005-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003", "EDITORIAL-PRIVATE-DEFENSE-BATCH-036-042", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061", "EDITORIAL-REVISION-001-FOLLOWUP-001", "EDITORIAL-REVISION-003-FOLLOWUP-001", "EDITORIAL-REVISION-004-FOLLOWUP-001", "EDITORIAL-REVISION-005-FOLLOWUP-001", "EDITORIAL-REVISION-006-FOLLOWUP-001", "EDITORIAL-REVISION-007-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001"],
  "result": "revision",
  "checker_exit_status": null,
  "timestamp": "2026-09-13T21:42:42Z"
}
```

## `DEC-021` length-governance and Chapter 118 repair follow-up

`DEC-021` resolves the governance conflict without rewriting any historical finding or gate: the former
per-chapter bands and derived means remain useful evidence, but they no longer decide craft. Chapter 118
was then revised for the separate defect the earlier review identified — emotional under-inhabitation —
and not to hit a quota. Its Chapter Header now declares the checker-observed 1,215 Prose_Words and
retains `normal` / `exploratory`.

No adjacent Coda drafting-batch gate is asserted. Delivered Chapter Files do not exist for 117 or 119,
so the current evidence supports a Chapter 118 local reread and objective rerun only. The unchanged
117–119 ArcEntries remain continuity authority for the boundaries of that reread.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001",
    "scope": "manuscript",
    "chapter_numbers": [19, 35, 51, 52, 53, 54, 55, 57, 58, 59, 60, 118, 124],
    "batch_id": null,
    "criterion": "Follow-up: whether DEC-021 resolves the conflicting length rules while preserving a real complete-manuscript budget safeguard and scene-earned variation",
    "prose_locations": [
      {"path": "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "start_line": 17, "end_line": 41, "note": "The longest delivered normal chapter remains a load-bearing continuous scene in which Nia reads the closed review and sets her conditions; DEC-021 does not order a functioning scene cut to satisfy an obsolete band."},
      {"path": "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "start_line": 40, "end_line": 49, "note": "The shortest delivered normal chapter remains compressed around a seventy-six-millisecond blocked send and rejection; DEC-021 does not order padding around a complete brief event."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 20, "end_line": 56, "note": "Chapter 118 is now 1,215 observed Prose_Words because the material needed inhabiting, not because either historical band required a number; its expansion is evaluated separately below."}
    ],
    "finding": "pass",
    "rationale": "The governance conflict is closed at the level where it arose. DEC-021 keeps exactly 128 chapters, 130,000-150,000 final Prose_Words, the 700-1,600 normal range, 2,500 hard maximum, 108-normal floor, 20-outlier cap, and 3,600-word same-POV run limit. It retires only the use of 1,050-1,200, 1,125, 900-1,400, and derived fixed mean windows as craft verdicts or waiver triggers. Current measurement after the Chapter 118 repair finds 64 delivered files and 73,604 declared Prose_Words. The 55 delivered normal chapters average 1,142.7; applying current delivered class means to the outline's 109 normal, 10 microchapter, and 9 long-outlier entries projects approximately 145,400, inside Final_Targets. The old-band departures therefore require neither exceptions nor arithmetic prose changes. The safeguard remains active: future reviews must recompute the projection and repair genuine manuscript-level drift where it occurs.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T22:10:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-REVISION-009-FOLLOWUP-002",
    "scope": "manuscript",
    "chapter_numbers": [4, 24, 31, 34, 118],
    "batch_id": null,
    "criterion": "Second follow-up: chapter scale and whether the final unrepaired load-bearing scene, Chapter 118's Tuesday account, is now inhabited rather than named",
    "prose_locations": [
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 16, "end_line": 23, "note": "The ordinary room tone and forty-year domestic construction of the private layer are now lived through the window, damp cloth, shallow cupboard, washing, and Safiya's post-funeral use rather than summarized as a duration."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 30, "end_line": 47, "note": "The Tuesday change is slowed through counter, sleeve, metal, handle, steam, cup, and repeated hand movement; partial survival remains uneven and explicitly not listable that night, preserving Chapter 119."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 48, "end_line": 56, "note": "Safiya demonstrates intact public interpreting competence in action, names the sole-survivor condition without creating a corpus, and observes Mara's restraint without entering Mara's interior."}
    ],
    "finding": "pass",
    "rationale": "The last unrepaired example in EDITORIAL-REVISION-009 is repaired on literary rather than numeric grounds. Chapter 118 now gives physical duration to the Tuesday and human duration to the forty years that preceded it. Its expansion is causal rather than decorative: domestic memory establishes how the layer accumulated and why no corpus exists; the kettle sequence lets intact ordinary action and failed inward retrieval occupy the same time; the appointment scene proves that the loss is private rather than generalized impairment; and the final observable thumb movement leaves Mara listening rather than taking over the account. Safiya still addresses Mara directly in a register unlike the three institutional narrators. Nothing arrives, Oam remains the only invented quoted token, no real heritage base is inferred, no reconstruction route appears, the Chapter 73 parallel remains unnamed, and Chapter 119 retains the exact lexical shape of the absence. The chapter's 1,215 words are evidence of the room now present, not the reason for the pass.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T22:10:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-AFTERMATH-CODA-118-REPAIR-001",
    "scope": "chapter",
    "chapter_numbers": [118],
    "batch_id": null,
    "criterion": "Current Chapter 118 local review: Safiya voice, emotional inhabitation, canon and epistemic restraint, MOT-KETTLE-01 function, reveal ownership, Chapter 117/119 boundary, and DEC-021 scene-earned length",
    "prose_locations": [
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 12, "end_line": 28, "note": "Safiya begins already seated and addressing Mara, locates her house eleven miles from the array, develops the maternal layer without naming a heritage base, and denies any arrival or third presence."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 30, "end_line": 47, "note": "One continuous kettle event carries the change through ordinary sensation and failed retrieval; the prose quotes no second private word and declines to list the loss."},
      {"path": "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "start_line": 48, "end_line": 59, "note": "Public interpreting remains exact, the absent corpus remains unrecoverable, Mara is visible only through restraint, and Safiya owns both the stop and the request that follows."}
    ],
    "finding": "pass",
    "rationale": "The revised chapter performs its ArcEntry purpose and Hook without replaying the Chapter 117 threshold or spending Chapter 119's lexical account. POV-SAFIYA, TL-CODA-ACCOUNT, MOT-KETTLE-01, and REVEAL-SAFIYA-TUESDAY-LOSS remain exact, and status remains exploratory. The added room, body, work, and grief material is specific to Safiya's life and carries no foreign voice, authorization question, mechanism explanation, real-world language inference, private corpus, archive/model/pairing route, new motif, or Mara interior. The kettle's heating, whistle, pour, and setting down are one continuous Tuesday event. The chapter is fully inhabited at its current length and needs no quota-driven expansion or trimming.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T22:10:00Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-AFTERMATH-CODA-118-REPAIR-001",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [118],
      "documents": ["chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/decisions.md"],
      "description": "Current Chapter 118 local Editorial_Gate after the DEC-021-authorized craft expansion. The chapter passes voice, emotional inhabitation, continuity, reveal ownership, motif function, epistemic restraint, and scene-earned length. It remains exploratory; this local pass does not invent a 117-119 drafting batch or approve the undelivered Coda movement."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-AFTERMATH-CODA-118-REPAIR-001", "EDITORIAL-REVISION-009-FOLLOWUP-002"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-18T22:10:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-REVISION-PASS-003",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [1, 4, 24, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 53, 118],
      "documents": ["planning/decisions.md", "planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/motif-ledger.md", "planning/editorial-log.md", "planning/gate-results.md", "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md"],
      "description": "Second rerun of the DEC-018 revision-pass Editorial_Gate against current prose and DEC-021 governance. All nine original criteria now have current follow-up passes. GATE-EDITORIAL-REVISION-PASS-001 and -002 remain unedited as historical records; this pass does not supply the still-missing current Discovery movement coverage."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-REVISION-001-FOLLOWUP-001", "EDITORIAL-REVISION-002-FOLLOWUP-001", "EDITORIAL-REVISION-003-FOLLOWUP-001", "EDITORIAL-REVISION-004-FOLLOWUP-001", "EDITORIAL-REVISION-005-FOLLOWUP-001", "EDITORIAL-REVISION-006-FOLLOWUP-001", "EDITORIAL-REVISION-007-FOLLOWUP-001", "EDITORIAL-REVISION-008-FOLLOWUP-001", "EDITORIAL-REVISION-009-FOLLOWUP-002", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001", "EDITORIAL-AFTERMATH-CODA-118-REPAIR-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-18T22:10:00Z"
  },
  {
    "gate_result_id": "GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-003",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61],
      "documents": ["planning/arc-outline.md", "planning/arc-changes.md", "planning/canon-bible.md", "planning/decisions.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md", "planning/editorial-log.md", "planning/gate-results.md"],
      "description": "Task 13.6 Private_Defense_Part movement Editorial_Gate rerun after DEC-021. All chapter and batch prerequisites remain current, every assigned craft criterion already passed in GATE-EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002, and its sole governance blocker now has a current follow-up pass. Supersedes -002 without editing it. This gate completes task 13.6 but does not satisfy task 14, because GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE still records 24 missing current Discovery chapter reviews plus batch and objective reruns."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-001", "EDITORIAL-PRIVATE-DEFENSE-MOVEMENT-002", "EDITORIAL-PROPULSION-005-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003", "EDITORIAL-PRIVATE-DEFENSE-BATCH-036-042", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001", "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061", "EDITORIAL-REVISION-001-FOLLOWUP-001", "EDITORIAL-REVISION-003-FOLLOWUP-001", "EDITORIAL-REVISION-004-FOLLOWUP-001", "EDITORIAL-REVISION-005-FOLLOWUP-001", "EDITORIAL-REVISION-006-FOLLOWUP-001", "EDITORIAL-REVISION-007-FOLLOWUP-001", "EDITORIAL-LENGTH-BAND-MANUSCRIPT-001-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": null,
    "timestamp": "2026-09-18T22:10:00Z"
  }
]
```

## Discovery_Part current evidence and movement gate — voice-separation repair pass

`GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE` recorded that current craft evidence existed for only
five of the twenty-nine Discovery chapters. That gap is now closed. All twenty-nine carry a current
chapter finding, all six batches carry a current batch finding, and the movement criteria have been
re-verified against present text rather than against the pre-`DEC-018` prose the historical records
evaluated.

Fifteen chapters returned `revision` and all fifteen are repaired in this pass. Two of those were
substantive rather than cosmetic: Chapters 16 and 27 both performed person-specific work without
acknowledging the restraint memorandum and the open suspension, and both now name the constraint they
proceed against. One was a factual correction, Chapter 13's control-participant count.

**The movement gate is `revision`, and the blocker is a single named criterion.** `DEC-018` clause 7
voice separation does not pass for `POV-MARA` and `POV-NIA`. Four independent close reads and a direct
measurement of both narrators' delivered narration agree that they share one syntactic and epistemic
register. The local repairs in this pass removed the shared epigrams and assigned the retained
constructions to one narrator each; they do not close the clause, which asks for separation carried by
rhythm and paragraph shape. Recording a pass here would be the exact failure this log exists to prevent.

```json record=EditorialFinding schema=1
[
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-001",
    "scope": "chapter",
    "chapter_numbers": [
      1
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "start_line": 60,
        "end_line": 60,
        "note": "The December omission is enacted at the page rather than summarized, and it remains the single canonical instance of the image after the two later callbacks were varied."
      }
    ],
    "finding": "pass",
    "rationale": "Opens with the narrator's head inside a cabinet and a torch in her teeth, which explains her silence before it explains anything else, and the omitted clause carries the movement's first cost without concealing a fact she holds.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-002",
    "scope": "chapter",
    "chapter_numbers": [
      2
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 60,
        "end_line": 60,
        "note": "The closing elegy was replaced by an admission about the account itself, which keeps the bell live and refuses the summary."
      },
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 54,
        "end_line": 54,
        "note": "Care rendered through an unmentioned replaced bulb and a lie about fire risk; no interiority spent."
      }
    ],
    "finding": "revision",
    "rationale": "Nia is unmistakable and the Joss material is the best warmth in the movement, but the chapter closed on a foreclosed elegy that restated its own title and left no question alive.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-003",
    "scope": "chapter",
    "chapter_numbers": [
      3
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 18,
        "end_line": 18,
        "note": "Method turned into self-indictment in one clause."
      }
    ],
    "finding": "pass",
    "rationale": "The control that was built to kill the result kills the wrong thing, and the chapter turns method against its own author. Ravi is a real second mind who refuses to let a number belong to one pair of hands.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-004",
    "scope": "chapter",
    "chapter_numbers": [
      4
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "start_line": 26,
        "end_line": 26,
        "note": "The duplicated fence-story construction shared with chapter 2 was rewritten so the beat is no longer a template."
      }
    ],
    "finding": "pass",
    "rationale": "The four seconds the earlier draft gestured at are now inhabited, and the shift-handover correction is carried by two counts with a time against each rather than by narration.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-005",
    "scope": "chapter",
    "chapter_numbers": [
      5
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 48,
        "end_line": 48,
        "note": "The shared 'pleased' self-indictment marker was removed here so the construction belongs to one chapter rather than three."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 78,
        "end_line": 78,
        "note": "The ending remains an unresolved obligation rather than a summary."
      }
    ],
    "finding": "revision",
    "rationale": "The hinge \u2014 that there was never a message and a person is being overheard \u2014 is the movement's central recognition, but the chapter reached it through a self-approving register that duplicated chapter 3's experiment.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-006",
    "scope": "chapter",
    "chapter_numbers": [
      6
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 80,
        "end_line": 80,
        "note": "The third instance of the shared self-indictment marker was replaced with an act."
      },
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 54,
        "end_line": 54,
        "note": "A reveal forty chapters out, motivated entirely as ordinary caution."
      }
    ],
    "finding": "revision",
    "rationale": "The strongest canon discipline in the movement: the December qualifier is planted through Mara's insistence and misread by Julian in a way he flags without understanding. The 'pleased' marker was the one shared tic.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-007",
    "scope": "chapter",
    "chapter_numbers": [
      7
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 64,
        "end_line": 64,
        "note": "The self-labelling structural line was cut."
      },
      {
        "path": "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "start_line": 52,
        "end_line": 52,
        "note": "One of the two enumerated-absence runs was rewritten into positive statement."
      }
    ],
    "finding": "revision",
    "rationale": "Nia's governing principle \u2014 a windscreen beats a picture of a windscreen \u2014 is fully dramatized, but the chapter carried two enumerated-absence runs and a line that labelled its own structure.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-008",
    "scope": "chapter",
    "chapter_numbers": [
      8
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "start_line": 80,
        "end_line": 80,
        "note": "The protagonist's secrecy is reframed as a description of intention rather than situation."
      }
    ],
    "finding": "pass",
    "rationale": "Ravi's search log turns the chapter against its narrator: her withholding has already produced a paper trail with somebody else's name on it. Real, irreversible, mechanical consequence.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-009",
    "scope": "chapter",
    "chapter_numbers": [
      9
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 46,
        "end_line": 46,
        "note": "The abstract accumulation passage was replaced with the specific acts and their clock time."
      }
    ],
    "finding": "revision",
    "rationale": "The tracked-changes fight over five words is the book's thesis executed as clerical detail, but institutional appetite was asserted in an essayistic passage with no room, person, or object in it.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-010",
    "scope": "chapter",
    "chapter_numbers": [
      10
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "start_line": 78,
        "end_line": 78,
        "note": "The verbatim repeat of the pen image was varied while the December callback was preserved."
      }
    ],
    "finding": "pass",
    "rationale": "Every category offers a box whose accuracy depends on misdescribing the event, the form refuses to save without a sponsor, and the abandonment is logged and used against her later.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-011",
    "scope": "chapter",
    "chapter_numbers": [
      11
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md",
        "start_line": 54,
        "end_line": 54,
        "note": "Epistemology carried by an exchange rather than by exposition."
      }
    ],
    "finding": "pass",
    "rationale": "The blinded read where the fifth failure is the actual discovery converts a negative result into plot, and the aphorism it raises is immediately attacked by another character rather than left standing.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-012",
    "scope": "chapter",
    "chapter_numbers": [
      12
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
        "start_line": 82,
        "end_line": 82,
        "note": "A flat physical ending that refuses to comment on what preceded it."
      }
    ],
    "finding": "pass",
    "rationale": "The strongest chapter in the movement. Its argument that institutional records cannot hold human cost is enacted through a two-hundred-character field rather than stated, and it ends flat on the queue and the next shift.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-013",
    "scope": "chapter",
    "chapter_numbers": [
      13
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "start_line": 98,
        "end_line": 98,
        "note": "The metafictional motif-tagging sentence was removed; the image was already earned a paragraph earlier."
      },
      {
        "path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "start_line": 48,
        "end_line": 48,
        "note": "A factual inconsistency was corrected: four staff asked now reconciles with three participants and three sessions."
      }
    ],
    "finding": "revision",
    "rationale": "The outlier length is fully earned by two complete failure-and-recovery cycles, but the chapter tagged its own motif in the narrator's voice and miscounted the control participants.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-014",
    "scope": "chapter",
    "chapter_numbers": [
      14
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-014-rights-before-names.md",
        "start_line": 18,
        "end_line": 18,
        "note": "The duplicated inventory was reduced to the one argument that is Julian's own increment."
      },
      {
        "path": "chapters/discovery-part/discovery-part-014-rights-before-names.md",
        "start_line": 26,
        "end_line": 26,
        "note": "The six-noun restraint list became plain speech."
      }
    ],
    "finding": "revision",
    "rationale": "The director's call and the printed page with no pressure marks are load-bearing, but the first third narrated a memorandum at the level of its own headings and duplicated chapter 10's forms inventory.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-015",
    "scope": "chapter",
    "chapter_numbers": [
      15
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
        "start_line": 12,
        "end_line": 12,
        "note": "A physical fact of his own was added to the opening."
      },
      {
        "path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
        "start_line": 76,
        "end_line": 76,
        "note": "The unremarked retitling carries the capture without commentary."
      }
    ],
    "finding": "revision",
    "rationale": "The agenda retitling dramatizes institutional capture better than any of the chapter's arguments explain it, but Julian had no body anywhere in the chapter and the only physical detail belonged to opposing counsel.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-016",
    "scope": "chapter",
    "chapter_numbers": [
      16
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-016-come-in.md",
        "start_line": 14,
        "end_line": 14,
        "note": "The memo is now named, and she proceeds on the letter of it, which converts an unexamined act into a deliberate breach."
      },
      {
        "path": "chapters/discovery-part/discovery-part-016-come-in.md",
        "start_line": 56,
        "end_line": 56,
        "note": "The witness withdraws, the door stays open, she proceeds."
      }
    ],
    "finding": "revision",
    "rationale": "The compression is earned and the moral shape is right \u2014 the chapter is over before she can talk herself out of it \u2014 but it built and fired a transmit path without acknowledging the restraint memorandum addressed to her.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-017",
    "scope": "chapter",
    "chapter_numbers": [
      17
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
        "start_line": 40,
        "end_line": 40,
        "note": "An abstract maxim became an act of self-observation in her own register."
      },
      {
        "path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
        "start_line": 118,
        "end_line": 118,
        "note": "The second enumerated-absence run became a physical analogy."
      }
    ],
    "finding": "revision",
    "rationale": "The dispatch sequence and the four touches are the movement's best procedural writing, but roughly a third of the chapter re-litigated the decision in review-board prose and carried a second enumerated-absence run.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-018",
    "scope": "chapter",
    "chapter_numbers": [
      18
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-018-clean-silence.md",
        "start_line": 64,
        "end_line": 64,
        "note": "An objection that would strengthen the thing objected to is refused."
      }
    ],
    "finding": "pass",
    "rationale": "The log-sentence dispute is an ethics fight conducted entirely over sentence placement and resolved by separating his words from her decision, which is the book's thesis about records performed as procedure.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-019",
    "scope": "chapter",
    "chapter_numbers": [
      19
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
        "start_line": 16,
        "end_line": 16,
        "note": "The shared maxim opener was removed so the operational substance carries the beat."
      }
    ],
    "finding": "pass",
    "rationale": "The two-column page keeps possible apart from remembered so a later reader cannot merge them, both comforts are refused on the page, and the Joss scene is the only place in the movement where somebody is looked after.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-020",
    "scope": "chapter",
    "chapter_numbers": [
      20
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
        "start_line": 92,
        "end_line": 92,
        "note": "The chapter's ethical centre, earned rather than asserted."
      },
      {
        "path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
        "start_line": 18,
        "end_line": 18,
        "note": "A seven-item negative inventory was compressed."
      }
    ],
    "finding": "pass",
    "rationale": "Guilt is exposed as a way of converting an unnameable person into a fact about the narrator's own character, and the burial of the bench path from the compliance answer is disclosed to the reader in the same breath.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-021",
    "scope": "chapter",
    "chapter_numbers": [
      21
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-021-reconstruction.md",
        "start_line": 108,
        "end_line": 108,
        "note": "The shared closing formula was replaced with an act that defers the answer physically."
      }
    ],
    "finding": "revision",
    "rationale": "The reconstruction is complete and still does not contain the moment she became sure, which is the point, but the chapter closed on a deliberation formula shared with two other narrators.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-022",
    "scope": "chapter",
    "chapter_numbers": [
      22
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-022-fundable.md",
        "start_line": 64,
        "end_line": 64,
        "note": "The courier returns at the end and her unanswered question becomes the closing beat."
      }
    ],
    "finding": "revision",
    "rationale": "The condition-precedent exchange carries the whole argument about capture in four lines, but the chapter remained document archaeology with its one live human discarded after two clauses.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-023",
    "scope": "chapter",
    "chapter_numbers": [
      23
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "start_line": 46,
        "end_line": 46,
        "note": "A self-correction that indicts the narrator mid-sentence."
      },
      {
        "path": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "start_line": 96,
        "end_line": 96,
        "note": "Power transferred, question live, no maxim."
      }
    ],
    "finding": "pass",
    "rationale": "The identity is verified and released here without stealing chapter 24's refusal, the folders are separated physically as the only honest argument available, and the failed correction shows testimony behaving like testimony.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-024",
    "scope": "chapter",
    "chapter_numbers": [
      24
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-024-not-case-zero.md",
        "start_line": 48,
        "end_line": 48,
        "note": "An abstract construction became plain speech in her own register."
      }
    ],
    "finding": "pass",
    "rationale": "Five hundred and ninety-four words of discipline. Two concrete details carry it: the clock forty seconds fast, and Mara writing the request into the wrong folder while Nia watches and says nothing.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-025",
    "scope": "chapter",
    "chapter_numbers": [
      25
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
        "start_line": 28,
        "end_line": 28,
        "note": "A belief refused entry to the record without being abandoned."
      }
    ],
    "finding": "pass",
    "rationale": "The unsigned sentence is typed, read back with its grammar exposed, and deleted word by word, which is the most exact refusal of a convenient finding anywhere in the movement.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-026",
    "scope": "chapter",
    "chapter_numbers": [
      26
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-026-already-outside.md",
        "start_line": 58,
        "end_line": 58,
        "note": "The containment question is answered by an event that proceeds regardless of the narrator's choice."
      }
    ],
    "finding": "pass",
    "rationale": "Julian remains truthfully ignorant of the identity and the later path, and the receive-only audit works as a knowledge boundary and dramatic irony rather than as a technical recap.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-027",
    "scope": "chapter",
    "chapter_numbers": [
      27
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "start_line": 54,
        "end_line": 54,
        "note": "The authorization gap is now named, and consent is explicitly distinguished from authorization."
      },
      {
        "path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "start_line": 78,
        "end_line": 78,
        "note": "The manuscript's strongest interrupted cut."
      }
    ],
    "finding": "revision",
    "rationale": "Consent is enacted physically before any apparatus is discussed, and the interrupted cut is the strongest in the manuscript, but the chapter ran person-specific acquisition and transmission without addressing the open suspension.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-028",
    "scope": "chapter",
    "chapter_numbers": [
      28
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-028-named-second.md",
        "start_line": 76,
        "end_line": 76,
        "note": "The physicist's phrasing was replaced with the dispatcher's."
      },
      {
        "path": "chapters/discovery-part/discovery-part-028-named-second.md",
        "start_line": 14,
        "end_line": 14,
        "note": "The numbered protocol recital became her own speech."
      }
    ],
    "finding": "revision",
    "rationale": "The one active trial she misses is the one where impatience arrived before the act, which is design and phenomenology confirming each other without commentary, but her diction had migrated into Mara's at the moments that matter.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-029",
    "scope": "chapter",
    "chapter_numbers": [
      29
    ],
    "batch_id": null,
    "criterion": "Current Discovery chapter review against DEC-018 chapter shape, DEC-021 scene-earned length, voice separation, canon fidelity (receive-only December, separated bench path, unresolved causation), and no artificial withholding",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
        "start_line": 64,
        "end_line": 64,
        "note": "The ending now establishes a consequence: the key is useless against the meeting it cannot stop."
      }
    ],
    "finding": "revision",
    "rationale": "The shutdown, the useless lock, and the unnameable eighth attendee are real drama, but the chapter closed on a gesture that recycled chapter 1's terminal formula and established nothing.",
    "requested_action": "Repaired in this pass; see the resolution object and the batch follow-up finding.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": {
      "resolved_by": "Discovery current-evidence repair pass",
      "resolved_at": "2026-09-18T23:40:00Z",
      "action_taken": "The defect named in the rationale was repaired in the chapter's current text; the prose locations above cite the repaired passages. Header word counts were resynchronized and the chapter, batch, and global objective gates were rerun clean.",
      "follow_up_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001"
    }
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-001-005",
    "scope": "batch",
    "chapter_numbers": [
      1,
      2,
      3,
      4,
      5
    ],
    "batch_id": "BATCH-DISCOVERY-001-005",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "start_line": 56,
        "end_line": 58,
        "note": "Joss scene: an unmentioned replaced bulb and a lie about fire risk."
      },
      {
        "path": "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "start_line": 60,
        "end_line": 64,
        "note": "Ruth withholds the good biscuits rather than asking a question about the array."
      }
    ],
    "finding": "pass",
    "rationale": "Four of the five carry a live question past their boundary and none opens by stating its conclusion. The batch's one structural weakness, a closing elegy in chapter 2 and a duplicated experiment in chapter 5, is repaired. Warmth is real and unforced across Joss and Ruth, and neither relative is an exposition audience.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-006-010",
    "scope": "batch",
    "chapter_numbers": [
      6,
      7,
      8,
      9,
      10
    ],
    "batch_id": "BATCH-DISCOVERY-006-010",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 44,
        "end_line": 48,
        "note": "Keep December in the sentence: a reveal forty chapters out, motivated as ordinary caution."
      },
      {
        "path": "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "start_line": 44,
        "end_line": 46,
        "note": "Institutional readiness rendered as three specific acts with a time against them."
      }
    ],
    "finding": "pass",
    "rationale": "Julian's register is the most sharply separated in the manuscript and the December plant in chapter 6 is the batch's best craft. The shared self-indictment marker that had colonized three chapters is now confined to one, and chapter 9's abstract accumulation passage is grounded in clock time.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-011-015",
    "scope": "batch",
    "chapter_numbers": [
      11,
      12,
      13,
      14,
      15
    ],
    "batch_id": "BATCH-DISCOVERY-011-015",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
        "start_line": 56,
        "end_line": 60,
        "note": "The two-hundred-character field enacts the argument the chapter refuses to state."
      },
      {
        "path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "start_line": 26,
        "end_line": 28,
        "note": "Control participants now reconcile: four asked, one refused, three sessions."
      }
    ],
    "finding": "pass",
    "rationale": "Chapter 12 is the strongest chapter in the movement and chapter 11 converts a negative result into plot. The batch's two real defects are repaired: chapter 13's motif-tagging and participant miscount, and chapter 14's duplicated forms inventory and six-noun restraint list.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-016-020",
    "scope": "batch",
    "chapter_numbers": [
      16,
      17,
      18,
      19,
      20
    ],
    "batch_id": "BATCH-DISCOVERY-016-020",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-016-come-in.md",
        "start_line": 13,
        "end_line": 15,
        "note": "The memorandum is named and she proceeds on the letter of it."
      },
      {
        "path": "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
        "start_line": 70,
        "end_line": 74,
        "note": "Guilt exposed as a way of converting an unnameable person into a fact about her own character."
      }
    ],
    "finding": "pass",
    "rationale": "The compressed-clock cluster holds to the second across five chapters and three viewpoints. Chapter 16 now names the restraint memorandum it proceeds against, which converts an unexamined act into a deliberate breach, and chapter 17's second enumerated-absence run is replaced by physical analogy.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-021-025",
    "scope": "batch",
    "chapter_numbers": [
      21,
      22,
      23,
      24,
      25
    ],
    "batch_id": "BATCH-DISCOVERY-021-025",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "start_line": 60,
        "end_line": 64,
        "note": "The failed correction: testimony behaving like testimony."
      },
      {
        "path": "chapters/discovery-part/discovery-part-022-fundable.md",
        "start_line": 50,
        "end_line": 52,
        "note": "The courier's single unanswered question becomes the closing beat."
      }
    ],
    "finding": "pass",
    "rationale": "Chapter 23 releases the identity without stealing chapter 24's refusal, and chapter 25 refuses a convenient finding word by word. The shared deliberation-formula ending is broken in chapter 21, and chapter 22's discarded courier now closes the chapter.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-BATCH-026-029",
    "scope": "batch",
    "chapter_numbers": [
      26,
      27,
      28,
      29
    ],
    "batch_id": "BATCH-DISCOVERY-026-029",
    "criterion": "Current Discovery batch review: chapter shape across the batch, cadence and length variation under DEC-021, warmth and cost, canon fidelity, and whether any technique appears as a compliance token",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "start_line": 56,
        "end_line": 58,
        "note": "Consent and authorization explicitly separated before the session."
      },
      {
        "path": "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
        "start_line": 58,
        "end_line": 60,
        "note": "The key is useless against the meeting it cannot stop."
      }
    ],
    "finding": "pass",
    "rationale": "The movement closes on capability rather than resolution. Chapter 27 now distinguishes consent from authorization rather than letting Nia's consent silently answer the chair's question, and chapter 29 ends on an established consequence instead of a recycled gesture.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001",
    "scope": "movement",
    "chapter_numbers": [
      2,
      5,
      6,
      7,
      9,
      13,
      14,
      15,
      16,
      17,
      21,
      22,
      27,
      28,
      29
    ],
    "batch_id": null,
    "criterion": "Follow-up: whether the fifteen Discovery chapter revisions raised in this pass are discharged in current prose",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-016-come-in.md",
        "start_line": 13,
        "end_line": 15,
        "note": "The restraint memorandum is named; the breach is deliberate and the microchapter remains under 700 Prose_Words."
      },
      {
        "path": "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "start_line": 26,
        "end_line": 28,
        "note": "The participant count reconciles and the metafictional motif-tag is gone."
      },
      {
        "path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "start_line": 56,
        "end_line": 58,
        "note": "Consent no longer stands in for authorization."
      }
    ],
    "finding": "pass",
    "rationale": "All fifteen revisions are repaired in current text. Two were substantive continuity repairs rather than polish: chapters 16 and 27 both ran person-specific work without acknowledging the restraint memorandum and the open suspension, and both now name the constraint they proceed against, which increases the Anchor's culpability rather than excusing it. One was a factual correction: chapter 13's control participants now reconcile with chapter 11. The remainder removed shared formulas \u2014 the self-indictment marker across three chapters, the deliberation-formula ending across three narrators, two enumerated-absence runs, a self-labelling structural line, a metafictional motif-tag, and a recycled terminal gesture. Mechanical verification: cross-chapter six-word phrase repetition fell from seven to four, and the surviving 'I have not been able to' construction now appears only in the Anchor's chapters, which assigns it to one voice. Every chapter, batch, and global objective gate reran clean and no length class changed.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-CANON",
    "scope": "movement",
    "chapter_numbers": [
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
      29
    ],
    "batch_id": null,
    "criterion": "Movement canon re-verification: receive-only December apparatus, separation of the later temporary bench path, page-nine chronology, DEC-007 asymmetry, unresolved causation, and the three never-revealed reveals",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "start_line": 30,
        "end_line": 34,
        "note": "The equipment schedule describes a receiver because the apparatus is one; a diagnostic output is not a transmit stage."
      },
      {
        "path": "chapters/discovery-part/discovery-part-016-come-in.md",
        "start_line": 15,
        "end_line": 17,
        "note": "The December rack is not altered; the outgoing path is built beside it and every added part stays visible."
      },
      {
        "path": "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "start_line": 44,
        "end_line": 48,
        "note": "Identity established; causation explicitly not."
      }
    ],
    "finding": "pass",
    "rationale": "Verified chapter by chapter across all twenty-nine. The December apparatus is receive-only wherever it is described, and the temporary bench path is consistently a separate instrument built beside it rather than a modification of it. The eight-second figure is repeatedly de-naturalized as a receiver-side reconstruction cost under specific settings, never as a transit time or a source-side gap. Page nine is absent from the movement and is named as nonexistent where it could have been anticipated. DEC-007 holds: Mara's conviction stays private and inadmissible, Nia refuses both origin accounts, and no narrator converts belief into proof. The three never-revealed reveals do not appear. No narrator conceals a fact they hold in order to manufacture suspense; where narrators withhold, they withhold from institutions and disclose to the reader in the same breath.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE",
    "scope": "movement",
    "chapter_numbers": [
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
      29
    ],
    "batch_id": null,
    "criterion": "DEC-018 clause 7: whether voice separation is carried structurally by syntax, rhythm, paragraph shape, and attention rather than by domain vocabulary alone",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "start_line": 30,
        "end_line": 32,
        "note": "Anchor register: instrumentation as moral accounting."
      },
      {
        "path": "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
        "start_line": 30,
        "end_line": 32,
        "note": "Dispatcher register: the room heard without a headset, unit numbers coming loose from conditions."
      },
      {
        "path": "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
        "start_line": 26,
        "end_line": 30,
        "note": "Counsel register: defined terms deployed before definitions are agreed."
      }
    ],
    "finding": "revision",
    "rationale": "This is the one criterion the movement does not satisfy, and the local repairs in this pass do not close it. Julian Adebayo is genuinely separated: longer periodic sentences, the highest subordinate-clause density in the manuscript, and judgment carried inside qualification. Safiya Mir is separated by a wide margin in her single delivered chapter. Mara Venn and Nia Calder are not separated at the level the clause requires. Measured across their delivered narration, the two profiles are close to indistinguishable: mean narration sentence length 13.7 against 12.6, share of sentences under eight words 33 per cent against 37, share of single-sentence paragraphs 33 per cent against 30, and appositive 'which' density 2.31 against 2.05 per thousand words. Four independent close reads reached the same conclusion from the prose rather than from the counts, each observing that the two narrators share one epistemic posture \u2014 assert, then limit the assertion \u2014 and that stripping domain nouns makes them interchangeable. This pass removed the specific shared epigrams that were most visible, including the abstract maxims in chapters 17, 19, 24, 34, 42, 52 and 73, and assigned the retained constructions to one narrator each. That was worth doing and it is not sufficient. What remains is a rhythm and paragraph-shape difference that has to be written into Nia's narration across her chapters rather than corrected at individual sentences.",
    "requested_action": "Authorize a dedicated voice pass on Nia Calder's delivered chapters before Mindwars drafting begins, since she holds fourteen of the fifty-one Mindwars chapters and the cost of the pass roughly doubles once those exist. The pass should work at paragraph scale rather than sentence scale: give her shorter paragraph units, sensory and load-bearing detail from the console world, and a habit of reaching conclusions through sequence and consequence rather than through the Anchor's assert-then-limit construction. Do not remove her warm observational 'which' clauses, which are an asset and are not the defect.",
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  },
  {
    "editorial_finding_id": "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-SHAPE",
    "scope": "movement",
    "chapter_numbers": [
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
      29
    ],
    "batch_id": null,
    "criterion": "Movement shape: forward pressure, hook effectiveness without echo, cadence and length variation under DEC-021, personal cost and warmth per lead, and the compressed-clock cluster",
    "prose_locations": [
      {
        "path": "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
        "start_line": 13,
        "end_line": 15,
        "note": "Two calls eleven seconds apart with the first caller's breathing still in her ear."
      },
      {
        "path": "chapters/discovery-part/discovery-part-024-not-case-zero.md",
        "start_line": 13,
        "end_line": 15,
        "note": "A declared microchapter whose compression is its function."
      },
      {
        "path": "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "start_line": 60,
        "end_line": 62,
        "note": "The manuscript's strongest interrupted cut."
      }
    ],
    "finding": "pass",
    "rationale": "No chapter closes on a restatement of its ArcEntry hook; every high-overlap candidate was inspected directly and all were false positives, which confirms the DEC-018 clause 2 repair has held across the movement. Chapters 16 through 20 form a genuine compressed-clock cluster timestamped to the second across three viewpoints, and the outlier budget is spent where it earns: a 679-word microchapter at the irreversible act, answered by a long outlier that runs the consequence as continuous scene. Each lead incurs a personal, non-abstract cost: Mara loses the ability to state her conviction in any record that could reach the person it concerns, Nia loses live routing, and Julian builds the acceleration path himself and is thanked for it. Warmth is present and unforced through Joss and Ruth, neither of whom is an exposition audience or a route to absolution. Length now varies by scene need under DEC-021 rather than by band: the delivered movement runs from 594 to 1,858 Prose_Words. The movement's remaining honest weakness is that a majority of chapters still resolve on something absent rather than something established; that is the book's epistemology and it is defensible here, but it should not be allowed to become the only available ending shape in the movements still to be drafted.",
    "requested_action": null,
    "reviewer": "Author-delegated GPT-5.6 literary review",
    "reviewed_at": "2026-09-18T23:40:00Z",
    "resolution": null
  }
]
```

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-EDITORIAL-DISCOVERY-MOVEMENT-003",
    "gate_type": "editorial",
    "scope": {
      "chapter_numbers": [
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
        29
      ],
      "documents": [
        "planning/arc-outline.md",
        "planning/arc-changes.md",
        "planning/canon-bible.md",
        "planning/decisions.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md",
        "planning/editorial-log.md",
        "planning/gate-results.md"
      ],
      "description": "Discovery_Part movement Editorial_Gate re-recorded against current revised prose, closing the evidence gap that GATE-EDITORIAL-DISCOVERY-MOVEMENT-002-INCOMPLETE scoped. All twenty-nine chapters now carry current chapter findings and all six batches carry current batch findings. Fifteen chapter revisions were raised and repaired in this pass. Canon and movement shape pass. The result is revision because DEC-018 clause 7 voice separation between POV-MARA and POV-NIA does not pass on current evidence and cannot be closed by local sentence repairs. GATE-EDITORIAL-DISCOVERY-MOVEMENT-001 and -002-INCOMPLETE are retained unedited as historical records. No Discovery chapter returns to approved."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [
      "EDITORIAL-DISCOVERY-CURRENT-001",
      "EDITORIAL-DISCOVERY-CURRENT-002",
      "EDITORIAL-DISCOVERY-CURRENT-003",
      "EDITORIAL-DISCOVERY-CURRENT-004",
      "EDITORIAL-DISCOVERY-CURRENT-005",
      "EDITORIAL-DISCOVERY-CURRENT-006",
      "EDITORIAL-DISCOVERY-CURRENT-007",
      "EDITORIAL-DISCOVERY-CURRENT-008",
      "EDITORIAL-DISCOVERY-CURRENT-009",
      "EDITORIAL-DISCOVERY-CURRENT-010",
      "EDITORIAL-DISCOVERY-CURRENT-011",
      "EDITORIAL-DISCOVERY-CURRENT-012",
      "EDITORIAL-DISCOVERY-CURRENT-013",
      "EDITORIAL-DISCOVERY-CURRENT-014",
      "EDITORIAL-DISCOVERY-CURRENT-015",
      "EDITORIAL-DISCOVERY-CURRENT-016",
      "EDITORIAL-DISCOVERY-CURRENT-017",
      "EDITORIAL-DISCOVERY-CURRENT-018",
      "EDITORIAL-DISCOVERY-CURRENT-019",
      "EDITORIAL-DISCOVERY-CURRENT-020",
      "EDITORIAL-DISCOVERY-CURRENT-021",
      "EDITORIAL-DISCOVERY-CURRENT-022",
      "EDITORIAL-DISCOVERY-CURRENT-023",
      "EDITORIAL-DISCOVERY-CURRENT-024",
      "EDITORIAL-DISCOVERY-CURRENT-025",
      "EDITORIAL-DISCOVERY-CURRENT-026",
      "EDITORIAL-DISCOVERY-CURRENT-027",
      "EDITORIAL-DISCOVERY-CURRENT-028",
      "EDITORIAL-DISCOVERY-CURRENT-029",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-001-005",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-006-010",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-011-015",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-016-020",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-021-025",
      "EDITORIAL-DISCOVERY-CURRENT-BATCH-026-029",
      "EDITORIAL-DISCOVERY-CURRENT-REPAIR-FOLLOWUP-001",
      "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-CANON",
      "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE",
      "EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-SHAPE"
    ],
    "result": "revision",
    "checker_exit_status": null,
    "timestamp": "2026-09-18T23:40:00Z"
  }
]
```
