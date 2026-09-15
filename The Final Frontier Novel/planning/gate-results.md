# Objective Gate Results

Normative schema: [`record-schemas.md`](record-schemas.md), especially `GateResult`
Companion log: [`editorial-log.md`](editorial-log.md), which owns every `editorial` gate

This document is the project log for **objective** `GateResult` records: the
`site-isolation`, `calibration-objective`, `chapter-local`, `batch`,
`baseline-objective`, and `manuscript-global` gate types. Each record states what
an automated run of `.tools/check_novel.py` proved about a requested scope at a
point in time.

It is deliberately separate from `editorial-log.md`. An objective gate carries a
`checker_exit_status` and never a craft judgment; an editorial gate carries human
findings and always a null exit status. Neither substitutes for the other, and no
chapter, batch, or manuscript becomes `approved` or `final` on one alone.

## Reading a record

- `prerequisite_state` is `incomplete` whenever a required input for the
  requested scope was missing, unreadable, malformed, or scope-incomplete. That
  forces `result: "incomplete"` and `checker_exit_status: 2`.
- A complete scope with error diagnostics is `revision` and `1`; a complete scope
  with none is `pass` and `0`.
- `objective_diagnostic_ids` lists the `CheckerDiagnostic` records a run
  produced. A passing run lists none, which is the whole point of the field.
- `scope.chapter_numbers` is empty when a gate proves readiness rather than
  auditing delivered prose.

## Staged authority

A gate result carries exactly the authority its `gate_type` grants:

- `site-isolation` proves the Manuscript_Exclusion_Contract is well-formed and
  that a routine honoring it excludes the manuscript. It does not prove the
  external Site_Build adopted the contract.
- `calibration-objective` unlocks **exploratory** calibration drafting only. It
  makes no claim about global mode, whole-book totals, the complete property
  suite, or the Approved_Baseline.
- `baseline-objective` is the record that global mode and every mandatory test
  are complete. Until it exists and passes, no post-calibration Drafting_Batch
  may begin.
- `manuscript-global` is the only objective gate that may speak about the
  complete Manuscript.

A staged or local result never claims global acceptance, and a rerun receives a
new `gate_result_id` rather than editing an existing record.

## Active records

### `GATE-CALIBRATION-OBJECTIVE-001`

Recorded by task 7.8, the minimal calibration-readiness hard gate. It proves the
minimal checker is ready for exploratory calibration prose; it audits no
Chapter_File, because none exists yet.

Evidence behind this record, all reproducible from the repository:

| Prerequisite | How it was proven |
|---|---|
| Site isolation | `check_novel.py --site-exclusion` exits `0` with `manuscript_entries=0`, and `test_site_exclusion.py` asserts the committed contract names the real manuscript root. |
| Complete provisional planning | All five allowlisted record sources load with zero diagnostics: 128 `ArcEntry`, 44 `TimelineEntry`, 4 `POVProfile`, 4 `VoiceBrief`, 22 `MotifEvent`, 2 `LiteralPhraseConstraint`, and 65 `CrossCut` records, every stable ID resolving uniquely. |
| Headers and filenames | `test_chapter_header_and_length.py` covers the nine required keys, missing and duplicate keys, malformed delimiters, and four-way filename/directory/header/ArcEntry agreement. |
| Counts and Length_Classes | The same module covers empty, Unicode, CRLF, and tab counting and the 0/699/700/1,600/1,601/2,500/2,501 boundaries. |
| Direct reference IDs | `test_direct_references_and_scope.py` covers valid, dangling, duplicate, many-to-one, and disagreeing references, and the closed four-mode `technical_state` table. |
| Mechanism chronology | `test_mechanism_chronology.py` proves the December `RECEIVE` record, the receive-only apparatus with no transmit stage, the eight-second offset carried only on the receiving side, the distinct later bench `INTRUDE`, page nine as capability rather than December evidence, separated Trust composition and deposit, and the `DEC-015` pairing cases. |
| Calibration motif and literal rules | `test_calibration_motif_and_literals.py` covers the `MOT-YES-01`, `MOT-KETTLE-01`, `MOT-COME-04`, and `MOT-KETTLE-02` assignments and the Prose_Body-only `Did I say yes?` scope rule. |
| Changed-reference consistency | `test_scope_modes_and_reporting.py` covers a reached reference, a stale one, an unknown one, an unreadable one, and a duplicate declaration, plus the refusal to accept any of them in chapter scope. |
| Deterministic diagnostics | The same module proves one total order over diagnostics, byte-identical repeated text and JSON reports, and that no diagnostic code names a craft judgment. |
| Exit behavior | The same module proves `0` for a complete zero-violation scope, `1` for objective violations, `2` for missing, malformed, or scope-incomplete input, and that `2` outranks `1`. |
| Chapter and batch smoke test | The complete eight-chapter synthetic Calibration_Batch (1–5, 73, 118, 124) runs through `main()` in both formats and exits `0`; single-chapter scope exits `0`; injected violations exit `1` and `2`. |

`test_calibration_gate.py` re-derives this record's evidence on every run, so the
claim below cannot drift away from the repository it describes.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-CALIBRATION-OBJECTIVE-001",
  "gate_type": "calibration-objective",
  "scope": {
    "chapter_numbers": [],
    "documents": [
      "exclusion-contract.json",
      "planning/arc-outline.md",
      "planning/canon-bible.md",
      "planning/motif-ledger.md",
      "planning/pov-roster.md",
      "planning/voice-briefs.md"
    ],
    "description": "Minimal calibration-readiness gate for task 7.8. Proves site isolation, complete provisional planning, and the chapter and batch modes of the minimal checker are ready for exploratory calibration drafting. Claims no global mode, no whole-book total, no complete property suite, and no Approved_Baseline."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": [],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-12T00:12:20Z"
}
```

#### What this gate does not unlock

- No Chapter_File may become `approved` or `final` on this record. That needs a
  `chapter-local` objective gate and a passing chapter `editorial` gate.
- No Drafting_Batch may begin. Requirement 13.2 makes that conditional on the
  Approved_Baseline, which needs `baseline-objective` first.
- The fifteen principal property tests remain reserved and skipped. They complete
  in parallel with calibration drafting and are required before baseline
  approval, per task 8 and the design's full baseline gate.
- Calibration prose drafted under this gate stays `exploratory` until its
  surrounding movement batches are drafted and it is reconciled into continuity.

### `GATE-BASELINE-OBJECTIVE-001`

Recorded by task 8.27. It proves the objective checker is complete in all three
runnable scopes and that every mandatory test is green. It audits no Chapter_File,
because the manuscript still has none.

Read the scope of this record carefully. It is a statement about the *checker and
its suite*, not about the novel. Global mode is proven against a complete
128-chapter synthetic manuscript; run against this repository, `--scope global`
correctly exits `2`, because 128 ArcEntries are planned and no Chapter_File
exists yet. That is the fail-closed contract working, not a failure of this gate.

Evidence behind this record, all reproducible from the repository:

| Prerequisite | How it was proven |
|---|---|
| Complete global mode | `--scope global` over a synthetic 128-chapter manuscript reports zero diagnostics and exits `0`: outline sequence and movement blocks, the outline-to-file bijection both ways, movement scale, the 80% normal share (128 of 128), Final_Targets against 89,607 counted words, whole-book literal totals, closed motif family totals, Canon_Bible authority, the Canon_Source inventory, Novel_Extensions, Reveals, ArcChanges, status synchronization, gate results, finalization gates, Fluent_Pairing coverage, and Front_Matter. |
| Reachable planning checks | `check_planning_references` is called from `check_global_scope`, so mechanism state, Pair_Calibration uniqueness, the Character_ID/POV_ID pairing, and Cross_Cut reciprocity all run at whole-book scope. `test_integration_scopes_and_process.py` injects a mechanism fault and requires the global run to report it. |
| Deterministic exits | The same workspace yields `0` for a clean Chapter_Local_Gate, `1` for `CHAPTER_MOVEMENT_DISAGREEMENT`, and `2` for a malformed header key, with `2` outranking `1`. Property 13 generates seven corruption kinds and requires `2` for each. |
| Fifteen principal property tests | 136 tests across the fifteen reserved modules, each at 100 generated examples. Every property in the design has exactly one principal module, and no property was split into a new one. |
| Focused unit and edge cases | 139 tests: the `DEC-002` receive-only December and its distinct bench path, `DEC-005` extension records, `DEC-007` with both origin accounts unresolved, `DEC-012` heritage restraint, the `DEC-014` five-source authority matrix, the `DEC-015` four modes with their CancelState, PairState, and PairingEvidence invariants, and exact accepted and rejected cases for `MOT-CHAIN-01..03` and `MOT-COPPER-01..03`. |
| Integration and process smoke | 36 tests: site isolation held separate from the manuscript gate, the eight-chapter calibration batch, chapter-local scope, a changed-reference batch, complete 128-entry global scope, Front_Matter prose rights with all five songs and no *One-Time Pad*, a Canon_Source authority slice, a three-mode pairing flow, and the process from provisional planning through calibration, full-suite evidence, one Baseline_Revision_Pass, approval, revision, and reapproval. |
| Site isolation | `--site-exclusion` exits `0` with `manuscript_entries=0`, `sources=5`, `songs=5`, and prints the standing limit that a local pass does not prove external adoption. |
| Restraint | No diagnostic code names a craft judgment. Name wording and capitalization variants that preserve stable IDs draw nothing, and the suite generates the prose-level claims the design rejects — contradictory geography, an adjudicating inquiry, a hidden release model, provenance as truth, a derived radius for `three counties wide` — and asserts the checker stays silent on every one. |

Two objective checker defects were found by this suite and fixed before the
record was written. `check_motif_family_totals` iterated the closed families that
appeared in the ledger, so a family with *no* events drew no diagnostic and the
global gate passed a manuscript whose kettle motif was never ledgered.
`check_canon_facts` allowed a `ratified-note` fact to declare
`authoritative-proposition`, which let advisory rights or credits metadata reach
the top authority tier by relabelling instead of by ratification. Both now have
focused regression tests.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-BASELINE-OBJECTIVE-001",
  "gate_type": "baseline-objective",
  "scope": {
    "chapter_numbers": [],
    "documents": [
      ".tools/check_novel.py",
      "exclusion-contract.json",
      "planning/arc-changes.md",
      "planning/arc-outline.md",
      "planning/canon-bible.md",
      "planning/editorial-log.md",
      "planning/gate-results.md",
      "planning/motif-ledger.md",
      "planning/pov-roster.md",
      "planning/voice-briefs.md"
    ],
    "description": "Complete objective checker gate for task 8.27. Proves all three runnable scopes, deterministic 0/1/2 exits, and a green mandatory suite of 698 tests: fifteen principal property modules at 100 examples each, the focused unit and edge-case suite, the integration and process-smoke suite, and this record's own re-derivation. Global mode is proven against a complete 128-chapter synthetic manuscript. Claims nothing about any Chapter_File, no calibration Editorial_Review, and no Approved_Baseline."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": [],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-12T04:30:00Z"
}
```

#### What this gate does not unlock

- It does not approve the Baseline. Requirement 12.14 needs the calibration
  Editorial_Review as well, and an `editorial` gate is human-only.
- It does not begin a post-calibration Drafting_Batch. That waits on the
  Approved_Baseline, which waits on the calibration review above.
- It made no claim about the eight exploratory calibration chapters when recorded. Those chapters now exist and are audited separately; this historical baseline-objective record remains evidence about the checker and mandatory suite only.
- It does not speak about the complete Manuscript. Only a `manuscript-global`
  gate may, and that requires 128 delivered Chapter_Files.

### Task 9 current calibration audits

Task 9 reran the checker against the delivered files rather than treating the two readiness gates above as chapter evidence. Every Chapter_Local_Gate and the Calibration_Batch audit completed with zero diagnostics. The batch declaration included every changed direct-reference document: `planning/arc-outline.md`, `planning/canon-bible.md`, `planning/motif-ledger.md`, `planning/pov-roster.md`, and `planning/voice-briefs.md`.

The checkpoint evidence is therefore deliberately split by authority:

- `GATE-EDITORIAL-CALIBRATION-001` is the corrected human editorial `pass`; its original revision findings remain in the audit trail and resolve to current follow-up passes.
- `GATE-BASELINE-OBJECTIVE-001` is the complete-checker and mandatory-suite `pass`, including all fifteen principal property modules, focused tests, integration/process smoke tests, and site isolation.
- `GATE-CHAPTER-LOCAL-CAL-001` through `008` and `GATE-BATCH-CALIBRATION-001` below prove that the current eight exploratory files and their direct planning references are objectively clean.

At the task 9 checkpoint, all eight Chapter Headers and ArcEntries remained `exploratory`, and they still do after baseline approval. At that historical checkpoint the provisional Baseline still had `baseline_revision_pass: null`, `author_approval: null`, and `final_targets: null`; task 9 neither performed task 10.1 nor approved the Baseline. Task 10.1 and the author-approved task 10.2 record their later state in `planning/arc-changes.md` and `planning/arc-outline.md` without changing this historical gate evidence.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [1],
      "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 1."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:41:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [2],
      "documents": ["chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 2."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:42:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-003",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [3],
      "documents": ["chapters/discovery-part/discovery-part-003-the-failed-check.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 3."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:43:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-004",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [4],
      "documents": ["chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 4."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:44:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-005",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [5],
      "documents": ["chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 5."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:45:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-006",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [73],
      "documents": ["chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 73."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:46:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-007",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [118],
      "documents": ["chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 118."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:47:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-CAL-008",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [124],
      "documents": ["chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Chapter_Local_Gate for exploratory calibration chapter 124."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:48:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-CALIBRATION-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
      "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md", "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 9 current-file Calibration_Batch audit with all changed direct-reference documents declared."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-16T20:49:00Z"
  }
]
```

## Task 11 approved-baseline checkpoint

### `GATE-APPROVED-BASELINE-001`

This is the post-approval hard-gate rerun required by task 11. It does not replace
or rewrite `GATE-BASELINE-OBJECTIVE-001`, which remains the objective evidence the
author-approved Baseline cited when approval was recorded. This new record proves
that global-mode planning input now reads that approved state without diagnostics:
Jessica Mulein's approval is present, the exact chapter target is 128, and the
inclusive total Prose_Word range is 130,000–150,000.

The same validation found one current Baseline, one completed
`Baseline_Revision_Pass` preceding approval, exactly one disposition for each of
the 18 calibration findings, and no active `ArcChange`. Chapters 1–5, 73, 118,
and 124 remain the complete Calibration_Batch and remain `exploratory` in both
their ArcEntries and Chapter Headers. No target, canon fact, arc assignment,
chapter prose, or exploratory status changed at this checkpoint.

The complete mandatory suite was rerun after adding this checkpoint evidence and
its committed-state regression coverage. All **702 tests passed**, including the
fifteen principal property modules at 100 examples each, focused unit and edge
cases, integration/process smoke, site isolation, historical gate re-derivation,
and the task-11 approved-baseline checks. The separate site-exclusion command
also passed with zero manuscript entries. A real repository `--scope global` run
continues to fail closed because only eight of 128 planned Chapter Files exist;
that is expected and is not a manuscript-global acceptance claim.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-APPROVED-BASELINE-001",
  "gate_type": "baseline-objective",
  "scope": {
    "chapter_numbers": [],
    "documents": [
      ".tools/check_novel.py",
      ".tools/tests/test_baseline_objective_gate.py",
      "exclusion-contract.json",
      "planning/arc-changes.md",
      "planning/arc-outline.md",
      "planning/canon-bible.md",
      "planning/editorial-log.md",
      "planning/gate-results.md",
      "planning/motif-ledger.md",
      "planning/pov-roster.md",
      "planning/voice-briefs.md"
    ],
    "description": "Task 11 Approved_Baseline hard-gate rerun. Global-mode planning records read one approved Baseline, Jessica Mulein's author approval, exact Final_Targets of 128 chapters and an inclusive 130,000-150,000 Prose_Word range, one complete 18-disposition Baseline_Revision_Pass, and all eight calibration chapters as exploratory. The complete mandatory suite passes 702 tests, and the separate site-exclusion validation reports zero manuscript entries. This readiness gate does not claim a complete Manuscript or manuscript-global acceptance."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": [],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-16T23:00:00Z"
}
```

## Task 12.1 Discovery drafting batch, Chapters 6–10

Task 12.1 created the first post-baseline Drafting_Batch. Chapters 6–10 moved from
`planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry
purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, or
reveal assignment changed, so this is planned drafting rather than an
`ArcChange`. `planning/arc-outline.md` was the only changed cross-document
reference declared to the batch checker; the Canon Bible, Motif Ledger, POV
Roster, and Voice Briefs were read as direct references and required no change.

The five Chapter_Local_Gates and the five-file `drafting` batch audit each
reported `result=pass`, `exit=0`, with zero errors and zero warnings. The batch
nevertheless remains `draft`: Julian's first-appearance Editorial_Gate is owned
by task 12.2 and remains deliberately unexecuted. These objective results do not
approve the chapters or the batch and do not alter `VOICE-JULIAN.first_appearance_review`.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-006",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [6],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 Chapter_Local_Gate for draft Discovery chapter 6."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:01:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-007",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [7],
      "documents": ["chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 Chapter_Local_Gate for draft Discovery chapter 7."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:02:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-008",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [8],
      "documents": ["chapters/discovery-part/discovery-part-008-provisional-identity.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 Chapter_Local_Gate for draft Discovery chapter 8."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:03:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-009",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [9],
      "documents": ["chapters/discovery-part/discovery-part-009-appetite-before-result.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 Chapter_Local_Gate for draft Discovery chapter 9."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:04:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-010",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [10],
      "documents": ["chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 Chapter_Local_Gate for draft Discovery chapter 10."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:05:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-006-010",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [6, 7, 8, 9, 10],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "chapters/discovery-part/discovery-part-008-provisional-identity.md", "chapters/discovery-part/discovery-part-009-appetite-before-result.md", "chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.1 five-file drafting batch audit. The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T00:06:00Z"
  }
]
```

## Task 12.2 approval rerun, Chapters 6–10

After the current editorial findings passed, Chapters 6–10 and their ArcEntries moved from `draft` to `approved`, and `VOICE-JULIAN.first_appearance_review` moved from `null` to its dated Chapter 6 pass reference. No prose changed, no continuity or motif fact changed, and no post-baseline `ArcChange` was required. The Canon Bible, Motif Ledger, and POV Roster remained unchanged. The current five Chapter_Local_Gates and the five-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The batch audit declared the two changed Direct Planning References exactly once: `planning/arc-outline.md` and `planning/voice-briefs.md`.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-006-APPROVAL-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [6],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current Chapter_Local_Gate for approved Discovery chapter 6 after Julian's first-appearance editorial pass."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:13:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-007-APPROVAL-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [7],
      "documents": ["chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current Chapter_Local_Gate for approved Discovery chapter 7."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:14:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-008-APPROVAL-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [8],
      "documents": ["chapters/discovery-part/discovery-part-008-provisional-identity.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current Chapter_Local_Gate for approved Discovery chapter 8."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-009-APPROVAL-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [9],
      "documents": ["chapters/discovery-part/discovery-part-009-appetite-before-result.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current Chapter_Local_Gate for approved Discovery chapter 9."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:16:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-010-APPROVAL-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [10],
      "documents": ["chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current Chapter_Local_Gate for approved Discovery chapter 10."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:17:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-006-010-APPROVAL-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [6, 7, 8, 9, 10],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "chapters/discovery-part/discovery-part-008-provisional-identity.md", "chapters/discovery-part/discovery-part-009-appetite-before-result.md", "chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.2 current five-file drafting-batch audit after editorial approval and status synchronization. Changed references planning/arc-outline.md and planning/voice-briefs.md were each declared once; all unchanged Direct Planning References remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T01:18:00Z"
  }
]
```

## Task 12.3 Discovery drafting batch, Chapters 11–15

Task 12.3 created the second post-baseline Drafting_Batch. Chapters 11–15 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, or reveal assignment changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The five Chapter_Local_Gates and the five-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The batch remains `draft` pending its later human Editorial_Gate. These objective results do not approve any chapter or the batch.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-011",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [11],
      "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 Chapter_Local_Gate for draft Discovery chapter 11."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-012",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [12],
      "documents": ["chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 Chapter_Local_Gate for draft Discovery chapter 12."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-013",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [13],
      "documents": ["chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 Chapter_Local_Gate for draft Discovery chapter 13 and MOT-CHAIN-01."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-014",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [14],
      "documents": ["chapters/discovery-part/discovery-part-014-rights-before-names.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 Chapter_Local_Gate for draft Discovery chapter 14."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-015",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [15],
      "documents": ["chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 Chapter_Local_Gate for draft Discovery chapter 15."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-011-015",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [11, 12, 13, 14, 15],
      "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "chapters/discovery-part/discovery-part-014-rights-before-names.md", "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.3 five-file drafting batch audit. The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:39:21Z"
  }
]
```
## Task 12.4 Discovery drafting batch, Chapters 16–20

Task 12.4 created the third post-baseline Drafting_Batch. Chapters 16–20 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, reveal assignment, Canon Bible fact, Motif Ledger event, POV Profile, or Voice Brief changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The five Chapter_Local_Gates and the five-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 16: 550 (`microchapter`, `draft`), 17: 1,626 (`long-outlier`, `draft`), 18: 729 (`normal`, `draft`), 19: 887 (`normal`, `draft`), and 20: 963 (`normal`, `draft`). The batch remains `draft` pending its human Editorial_Gate. These objective results do not approve any chapter or the batch.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-016",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [16],
      "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 Chapter_Local_Gate for draft Discovery chapter 16 and MOT-COME-01."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-017",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [17],
      "documents": ["chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 Chapter_Local_Gate for draft Discovery chapter 17."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-018",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [18],
      "documents": ["chapters/discovery-part/discovery-part-018-clean-silence.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 Chapter_Local_Gate for draft Discovery chapter 18."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-019",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [19],
      "documents": ["chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 Chapter_Local_Gate for draft Discovery chapter 19."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-020",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [20],
      "documents": ["chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 Chapter_Local_Gate for draft Discovery chapter 20."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-016-020",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [16, 17, 18, 19, 20],
      "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "chapters/discovery-part/discovery-part-018-clean-silence.md", "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.4 five-file drafting batch audit. The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:52:01Z"
  }
]
```

## Task 12.5 Discovery drafting batch, Chapters 21–25

Task 12.5 created the fourth post-baseline Drafting_Batch. Chapters 21–25 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, reveal assignment, Canon Bible fact, Motif Ledger event, POV Profile, or Voice Brief changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The five Chapter_Local_Gates and the five-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 21: 1,008 (`normal`, `draft`), 22: 890 (`normal`, `draft`), 23: 1,023 (`normal`, `draft`), 24: 487 (`microchapter`, `draft`), and 25: 917 (`normal`, `draft`), for 4,325 prose words in the batch. The batch remains `draft` pending its human Editorial_Gate. These objective results do not approve any chapter or the batch.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-021",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [21],
      "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 Chapter_Local_Gate for draft Discovery chapter 21."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-022",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [22],
      "documents": ["chapters/discovery-part/discovery-part-022-fundable.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 Chapter_Local_Gate for draft Discovery chapter 22."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-023",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [23],
      "documents": ["chapters/discovery-part/discovery-part-023-the-match-holds.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 Chapter_Local_Gate for draft Discovery chapter 23."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-024",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [24],
      "documents": ["chapters/discovery-part/discovery-part-024-not-case-zero.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 Chapter_Local_Gate for the planned compression microchapter 24."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-025",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [25],
      "documents": ["chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 Chapter_Local_Gate for draft Discovery chapter 25."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-021-025",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [21, 22, 23, 24, 25],
      "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.5 five-file drafting batch audit. The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T18:58:28Z"
  }
]
```

## Task 12.6 — Chapters 26–29 objective drafting gates

Task 12.6 created the fifth post-baseline Drafting_Batch. Chapters 26–29 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, reveal assignment, Canon Bible fact, Motif Ledger event, POV Profile, or Voice Brief changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The four Chapter_Local_Gates and the four-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 26: 981 (`normal`, `draft`), 27: 1,012 (`normal`, `draft`), 28: 1,123 (`normal`, `draft`), and 29: 1,001 (`normal`, `draft`), for 4,117 prose words in the batch. The batch remains `draft`, and the Discovery_Part movement remains unapproved pending the human Editorial_Gate in task 12.7. These objective results do not approve any chapter, the batch, or the movement.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-026",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [26],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.6 Chapter_Local_Gate for draft Discovery chapter 26."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T19:11:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-027",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [27],
      "documents": ["chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.6 Chapter_Local_Gate for draft Discovery chapter 27."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T19:11:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-028",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [28],
      "documents": ["chapters/discovery-part/discovery-part-028-named-second.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.6 Chapter_Local_Gate for draft Discovery chapter 28."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T19:11:21Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-029",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [29],
      "documents": ["chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.6 Chapter_Local_Gate for draft Discovery chapter 29."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T19:11:21Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-026-029",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [26, 27, 28, 29],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 12.6 four-file drafting-batch audit. The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T19:11:21Z"
  }
]
```
## Task 12.7 Discovery movement approval reruns

After the Discovery movement Editorial_Gate and the planning correction recorded by
`ARC-CHANGE-DISCOVERY-001`, every promoted chapter received a current
Chapter_Local_Gate and every affected batch received a current delivered-batch
audit. Chapters 6–10 retained their existing task 12.2 approval records; a
confirmatory task 12.7 rerun also reported `pass`, `exit=0`, and zero diagnostics
for each chapter and for their batch.

Across the full movement, all 29 current chapter checks and all six current batch
checks reported `result=pass`, `exit=0`, with zero errors and zero warnings. The
batch checks declared `planning/arc-outline.md` once for each promoted scope and
also declared `planning/canon-bible.md` once for Chapters 21–25, the scope that
reaches the corrected Reveal. All unchanged Direct Planning References remained
readable and consistent. The current Discovery movement contains 26,810 prose
words.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-001-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [1], "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 1."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-002-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [2], "documents": ["chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 2."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-003-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [3], "documents": ["chapters/discovery-part/discovery-part-003-the-failed-check.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 3."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-004-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [4], "documents": ["chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 4."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-005-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [5], "documents": ["chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 5."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-011-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [11], "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 11."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-012-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [12], "documents": ["chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 12."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-013-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [13], "documents": ["chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 13."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-014-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [14], "documents": ["chapters/discovery-part/discovery-part-014-rights-before-names.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 14."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-015-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [15], "documents": ["chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 15."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-016-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [16], "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 16."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-017-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [17], "documents": ["chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 17."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-018-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [18], "documents": ["chapters/discovery-part/discovery-part-018-clean-silence.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 18."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-019-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [19], "documents": ["chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 19."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-020-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [20], "documents": ["chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 20."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-021-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [21], "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 21 after movement reconciliation."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-022-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [22], "documents": ["chapters/discovery-part/discovery-part-022-fundable.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 22."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-023-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [23], "documents": ["chapters/discovery-part/discovery-part-023-the-match-holds.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 23 and corrected REVEAL-NIA-SOURCE-CASUALTY reader release."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-024-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [24], "documents": ["chapters/discovery-part/discovery-part-024-not-case-zero.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 24 and Nia's refusal/interpretation ownership."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-025-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [25], "documents": ["chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 25."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-026-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [26], "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 26."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-027-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [27], "documents": ["chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 27."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-028-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [28], "documents": ["chapters/discovery-part/discovery-part-028-named-second.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 28."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-029-MOVEMENT-RERUN",
    "gate_type": "chapter-local",
    "scope": {"chapter_numbers": [29], "documents": ["chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 current Chapter_Local_Gate for approved Discovery chapter 29."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:00:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-001-005-RECONCILIATION",
    "gate_type": "batch",
    "scope": {"chapter_numbers": [1, 2, 3, 4, 5], "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 reconciliation audit for approved Discovery chapters 1-5 (3,857 prose words). Changed reference planning/arc-outline.md was declared once."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:01:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-011-015-APPROVAL-RERUN",
    "gate_type": "batch",
    "scope": {"chapter_numbers": [11, 12, 13, 14, 15], "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "chapters/discovery-part/discovery-part-014-rights-before-names.md", "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 approval rerun for Discovery chapters 11-15 (5,607 prose words). Changed reference planning/arc-outline.md was declared once."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:02:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-016-020-APPROVAL-RERUN",
    "gate_type": "batch",
    "scope": {"chapter_numbers": [16, 17, 18, 19, 20], "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "chapters/discovery-part/discovery-part-018-clean-silence.md", "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 approval rerun for Discovery chapters 16-20 (4,755 prose words). Changed reference planning/arc-outline.md was declared once."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:03:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-021-025-APPROVAL-RERUN",
    "gate_type": "batch",
    "scope": {"chapter_numbers": [21, 22, 23, 24, 25], "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 approval rerun for Discovery chapters 21-25 (4,325 prose words). Changed references planning/arc-outline.md and planning/canon-bible.md were each declared once."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:04:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-026-029-APPROVAL-RERUN",
    "gate_type": "batch",
    "scope": {"chapter_numbers": [26, 27, 28, 29], "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"], "description": "Task 12.7 approval rerun for Discovery chapters 26-29 (4,117 prose words). Changed reference planning/arc-outline.md was declared once."},
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-17T03:05:00Z"
  }
]
```

## Task 13.1 — Chapters 30–35 objective drafting gates

Task 13.1 created the first Private_Defense_Part Drafting_Batch. Chapters 30–35 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, reveal assignment, Canon Bible fact, Motif Ledger event, POV Profile, or Voice Brief changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The six Chapter_Local_Gates and the six-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 30: 991 (`normal`, `draft`), 31: 849 (`normal`, `draft`), 32: 891 (`normal`, `draft`), 33: 905 (`normal`, `draft`), 34: 879 (`normal`, `draft`), and 35: 901 (`normal`, `draft`), for 5,416 prose words in the batch. `MOT-COPPER-01` remains assigned only to Chapter 31; `MOT-CHAIN-02` remains assigned only to Chapter 45 and is outside this batch. The batch remains `draft` and unapproved pending its required human Editorial_Gate. These objective results do not approve any chapter, the batch, or the Private_Defense_Part movement.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-030",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [30],
      "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 30."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-031",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [31],
      "documents": ["chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 31."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-032",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [32],
      "documents": ["chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 32."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-033",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [33],
      "documents": ["chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 33."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-034",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [34],
      "documents": ["chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 34."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-035",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [35],
      "documents": ["chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 Chapter_Local_Gate for draft Private Defense chapter 35."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-030-035",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [30, 31, 32, 33, 34, 35],
      "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.1 six-file drafting-batch audit for Chapters 30–35 (5,416 prose words). The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-17T04:15:00Z"
  }
]
```
## Task 13.2 — Chapters 36–42 objective drafting gates

Task 13.2 created the second Private_Defense_Part Drafting_Batch. Chapters 36–42 moved from `planned` to `draft` in both their Chapter Headers and ArcEntries. No ArcEntry purpose, Hook, POV, Timeline, Cross Cut, motif assignment, record horizon, reveal assignment, Canon Bible fact, Motif Ledger event, POV Profile, or Voice Brief changed, so this is planned drafting rather than an `ArcChange`. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker; the Canon Bible, Motif Ledger, POV Roster, and Voice Briefs were read as direct references and required no change.

The seven Chapter_Local_Gates and the seven-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 36: 899 (`normal`, `draft`), 37: 848 (`normal`, `draft`), 38: 912 (`normal`, `draft`), 39: 887 (`normal`, `draft`), 40: 813 (`normal`, `draft`), 41: 840 (`normal`, `draft`), and 42: 910 (`normal`, `draft`), for 6,109 prose words in the batch. No motif is assigned to Chapters 36–42. The batch remains `draft` and unapproved pending its required human Editorial_Gate. These objective results do not approve any chapter, the batch, or the Private_Defense_Part movement.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-036",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [36],
      "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 36."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-037",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [37],
      "documents": ["chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 37."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-038",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [38],
      "documents": ["chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 38."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-039",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [39],
      "documents": ["chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 39."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-040",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [40],
      "documents": ["chapters/private-defense-part/private-defense-part-040-first-calibration.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 40."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-041",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [41],
      "documents": ["chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 41."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-042",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [42],
      "documents": ["chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 Chapter_Local_Gate for draft Private Defense chapter 42."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-036-042",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [36, 37, 38, 39, 40, 41, 42],
      "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.2 seven-file drafting-batch audit for Chapters 36–42 (6,109 prose words). The only changed cross-document reference was planning/arc-outline.md, declared once; every unchanged direct planning reference remained readable and consistent."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T20:41:52Z"
  }
]
```

## Task 13.4 — Chapters 50–55 objective drafting gates

Task 13.4 created the third Private_Defense_Part Drafting_Batch and the record sequence it delivers. Chapters 50 through 55 moved from `planned` through `draft` to `revised` in both their Chapter Headers and ArcEntries. One ArcEntry value changed in this batch — the Chapter 52 `record_horizon.knowledge_limit` — and that change is carried by [`ARC-CHANGE-REVISION-003`](arc-changes.md) rather than by drafting alone, because it synchronizes a horizon left stale when task 5.6 moved `REVEAL-CASUALTY-CONSEQUENCE` onto its owning POV's chapter. No reveal owner, release chapter, payoff window, Cross Cut, motif assignment, Timeline entry, POV Profile, or Voice Brief changed. `planning/arc-outline.md` was the only changed cross-document reference declared to the batch checker.

The results below were produced after the repair pass recorded in [`editorial-log.md`](editorial-log.md), so they evaluate the current state of the prose and not the superseded first delivery. The six Chapter_Local_Gates and the six-file `drafting` batch audit each reported `result=pass`, `exit=0`, with zero errors and zero warnings. The chapter word counts and statuses are 50: 448 (`microchapter`, `revised`), 51: 1,403 (`normal`, `revised`), 52: 1,487 (`normal`, `revised`), 53: 1,413 (`normal`, `revised`), 54: 1,392 (`normal`, `revised`), and 55: 1,039 (`normal`, `revised`), for 7,182 prose words in the batch. `MOT-RECORD-01` is assigned to Chapter 51 only, and Chapters 50 and 52 through 55 carry `motif_events: []`. Chapters 54 and 55 form a two-chapter `POV-MARA` run totalling 2,431 Prose_Words, inside the 3,600 `DEC-016` run limit. Chapters 52 and 53 exceed the `DEC-019` clause 11 drafting band of 900–1,400 by 87 and 13 words respectively; both remain inside the `normal` class, and the manuscript mean across 58 delivered Chapter_Files is 1,142.8 Prose_Words, inside the held 1,006–1,187 window.

The batch remains `revised` and unapproved pending the Private_Defense_Part movement Editorial_Gate at task 13.6, and `EDITORIAL-PRIVATE-DEFENSE-050-055-008` remains open as an obligation on Chapters 56–61. These objective results do not approve any chapter, the batch, or the movement.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-050",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [50],
      "documents": ["chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 50."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-007"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-051",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [51],
      "documents": ["chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 51, carrying MOT-RECORD-01."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-007"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-052",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [52],
      "documents": ["chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 52, which releases REVEAL-CASUALTY-CONSEQUENCE."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-006"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-053",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [53],
      "documents": ["chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 53, which advances REVEAL-CASUALTY-CONSEQUENCE and carries the DEC-007 attribution split."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-004", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-006"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-054",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [54],
      "documents": ["chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 54, the pre-Trust provenance transfer."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-007"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-055",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [55],
      "documents": ["chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 Chapter_Local_Gate for revised Private Defense chapter 55, the Anchor POV instrument cost."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-008"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-050-055",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [50, 51, 52, 53, 54, 55],
      "documents": ["chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.4 six-file drafting-batch audit for Chapters 50-55 (7,182 prose words) after the repair pass. planning/arc-outline.md was the only changed cross-document reference, declared once; every unchanged direct planning reference remained readable and consistent. An earlier run of this batch covered only Chapters 51-55 and did not match the task's declared 50-55 scope; it is superseded by this result."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-001", "EDITORIAL-PRIVATE-DEFENSE-050-055-002", "EDITORIAL-PRIVATE-DEFENSE-050-055-003", "EDITORIAL-PRIVATE-DEFENSE-050-055-004", "EDITORIAL-PRIVATE-DEFENSE-050-055-005", "EDITORIAL-PRIVATE-DEFENSE-050-055-006", "EDITORIAL-PRIVATE-DEFENSE-050-055-007", "EDITORIAL-PRIVATE-DEFENSE-050-055-008"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-12T00:00:00Z"
  }
]
```
## Chapter 25–26 knowledge-horizon repair objective reruns

The current Chapter 25 and 26 files and both affected Discovery drafting batches were rerun after the narrow prose repair. Each command reported zero errors and zero warnings. No planning reference value changed.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-025-HORIZON-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [25],
      "documents": ["chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate after the Chapter 25 disclosure-route repair; observed 1,153 Prose_Words."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T17:26:29Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-DISCOVERY-026-HORIZON-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [26],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate after the Chapter 26 Hook-echo cleanup; observed 1,196 Prose_Words."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T17:26:29Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-021-025-HORIZON-RERUN-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [21, 22, 23, 24, 25],
      "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current five-file Discovery drafting-batch audit after the Chapter 25 repair; no changed reference declared and zero diagnostics."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T17:26:29Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-026-029-HORIZON-RERUN-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [26, 27, 28, 29],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current four-file Discovery drafting-batch audit after the Chapter 26 cleanup; no changed reference declared and zero diagnostics."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T17:26:29Z"
  }
]
```
## Task 13.5 — Chapters 56–61 objective drafting gates

After the continuous editorial pass, all six Chapter_Local_Gates and the six-file `drafting` batch audit reported `result=pass`, `exit=0`, with zero errors and zero warnings. Current observed counts are 56: 1,683 (`long-outlier`, `revised`), 57: 799 (`normal`, `revised`), 58: 914 (`normal`, `revised`), 59: 907 (`normal`, `revised`), 60: 919 (`normal`, `revised`), and 61: 1,647 (`long-outlier`, `revised`), for 6,869 Prose_Words. Only Chapter 61 carries `MOT-COME-02`; `MOT-KNOCK-01` remains assigned to Chapter 73. The drafting-batch run declared `planning/arc-outline.md` and `planning/canon-bible.md` as its changed cross-document references. These results complete task 13.5 objective evidence but do not approve the Private_Defense_Part movement; the task-13.6 editorial prerequisite record remains `incomplete`.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-056",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [56],
      "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 56; observed 1,683 Prose_Words in the long-outlier class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-056", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-057",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [57],
      "documents": ["chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 57; observed 799 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-057"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-058",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [58],
      "documents": ["chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 58; observed 914 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-058"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-059",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [59],
      "documents": ["chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 59; observed 907 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-059"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-060",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [60],
      "documents": ["chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 60; observed 919 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-060"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-061",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [61],
      "documents": ["chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 current Chapter_Local_Gate for revised Private Defense chapter 61; observed 1,647 Prose_Words in the long-outlier class and MOT-COME-02."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-061"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-056-061",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [56, 57, 58, 59, 60, 61],
      "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Task 13.5 six-file drafting-batch audit for Chapters 56–61 (6,869 Prose_Words) after the final narrow prose pass. planning/arc-outline.md and planning/canon-bible.md were each declared once as changed references; all chapter, direct-reference, status, count, motif, chronology, and run checks completed with zero diagnostics."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-056", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-057", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-058", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-059", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-060", "EDITORIAL-PRIVATE-DEFENSE-LOCAL-061", "EDITORIAL-PRIVATE-DEFENSE-BATCH-056-061", "EDITORIAL-PRIVATE-DEFENSE-050-055-008-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T18:13:54Z"
  }
]
```
## Task 13.3 — Chapters 43–49 objective drafting gates, recorded as current backfill

Task 13.3 delivered Chapters 43 through 49 and was marked complete, but no objective `GateResult` was ever recorded for that range: this log previously jumped from the task 13.2 batch to the task 13.4 batch. The records below close that omission. They are honest current runs rather than reconstructions of a historical state, so they evaluate the present `revised` prose after the `DEC-018` revision reached these files, and their timestamp is the time they were actually produced.

All seven Chapter_Local_Gates and the seven-file `drafting` batch audit reported `result=pass`, `exit=0`, with zero errors and zero warnings. Current observed counts and statuses are 43: 1,692 (`long-outlier`, `revised`), 44: 1,055 (`normal`, `revised`), 45: 431 (`microchapter`, `revised`), 46: 1,054 (`normal`, `revised`), 47: 1,171 (`normal`, `revised`), 48: 1,154 (`normal`, `revised`), and 49: 1,100 (`normal`, `revised`), for 7,657 Prose_Words. The viewpoint sequence is Mara, Julian, Mara, Julian, Nia, Mara, Julian, so no two adjacent chapters share a POV and the `DEC-016` same-POV run limit is not approached. No changed cross-document reference was declared, because this backfill delivers no reference change of its own.

These results carry only objective authority. No editorial finding or gate exists for Chapters 43–49, so nothing here approves a chapter, the batch, or the Private_Defense_Part movement, and the task-13.6 prerequisite record in [`editorial-log.md`](editorial-log.md) remains `incomplete`.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-043-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [43],
      "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 43, recorded to close the missing task 13.3 objective evidence; observed 1,692 Prose_Words in the long-outlier class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-044-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [44],
      "documents": ["chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 44, recorded to close the missing task 13.3 objective evidence; observed 1,055 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-045-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [45],
      "documents": ["chapters/private-defense-part/private-defense-part-045-page-nine.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 45, recorded to close the missing task 13.3 objective evidence; observed 431 Prose_Words, retaining its declared microchapter compression."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-046-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [46],
      "documents": ["chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 46, recorded to close the missing task 13.3 objective evidence; observed 1,054 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-047-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [47],
      "documents": ["chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 47, recorded to close the missing task 13.3 objective evidence; observed 1,171 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-048-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [48],
      "documents": ["chapters/private-defense-part/private-defense-part-048-the-refusal.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 48, recorded to close the missing task 13.3 objective evidence; observed 1,154 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-049-BACKFILL-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [49],
      "documents": ["chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current Chapter_Local_Gate for revised Private Defense chapter 49, recorded to close the missing task 13.3 objective evidence; observed 1,100 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-043-049-BACKFILL-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [43, 44, 45, 46, 47, 48, 49],
      "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "chapters/private-defense-part/private-defense-part-045-page-nine.md", "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current seven-file drafting-batch audit for Chapters 43–49 (7,657 Prose_Words), recorded to close the missing task 13.3 objective evidence. No changed cross-document reference was declared; every direct planning reference remained readable and consistent, and the alternating Mara/Julian/Nia sequence leaves no adjacent same-POV run."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:12:34Z"
  }
]
```
## Chapters 30–35 objective rerun after the voice-separation repair

The Chapter 34 repair recorded by `EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-001` changed prose, so the task 13.1 objective results no longer evaluated current text. The chapter and its batch were rerun. Chapter 34's declared count was corrected from 1,124 to the observed 1,116; no other chapter in the batch changed. Both runs reported zero errors and zero warnings, and no changed cross-document reference was declared.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-034-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [34],
      "documents": ["chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate rerun after deleting the redundant reader-instruction sentence; observed 1,116 Prose_Words in the normal class."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-034", "EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-002"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:42:37Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-030-035-RERUN-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [30, 31, 32, 33, 34, 35],
      "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Six-file drafting-batch rerun for current Chapters 30–35 prose after the Chapter 34 repair. Supersedes GATE-BATCH-PRIVATE-DEFENSE-030-035, which evaluated the pre-DEC-018 text; that record is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-BATCH-030-035-003"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T19:42:37Z"
  }
]
```
## Chapters 43–49 objective rerun after the Julian voice-separation repair

The repair recorded by `EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-001` changed prose in Chapters 44 and 49, so the backfill results recorded earlier in this document no longer evaluate current text for those two files. Declared counts were corrected from 1,055 to 1,052 and from 1,100 to 1,083, and both remain inside the `DEC-018` clause 10 band. The batch total is now 7,637 Prose_Words. Every run reported zero errors and zero warnings, and no changed cross-document reference was declared.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-044-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [44],
      "documents": ["chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate rerun after restoring Julian's own register in the competence admission; observed 1,052 Prose_Words in the normal class. Supersedes GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-044-BACKFILL-001, which is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-044", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-049-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [49],
      "documents": ["chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate rerun after removing three reader-instruction preambles from Julian's narration; observed 1,083 Prose_Words in the normal class. Supersedes GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-049-BACKFILL-001, which is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-LOCAL-049", "EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-002"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T20:57:37Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-043-049-RERUN-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [43, 44, 45, 46, 47, 48, 49],
      "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "chapters/private-defense-part/private-defense-part-045-page-nine.md", "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Seven-file drafting-batch rerun for current Chapters 43–49 prose (7,637 Prose_Words) after the Chapter 44 and 49 repairs. Supersedes GATE-BATCH-PRIVATE-DEFENSE-043-049-BACKFILL-001, which is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-BATCH-043-049-003"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T20:57:37Z"
  }
]
```
## Chapters 50–55 objective rerun after the Chapter 53 voice repair

Chapter 53 lost the last reserved reader-instruction instance from Julian's narration, so the task 13.4 objective results no longer evaluated current text. The declared count moved from 1,413 to the observed 1,411. Both runs reported zero errors and zero warnings, and no changed cross-document reference was declared. The batch now stands at 7,178 Prose_Words.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-053-RERUN-001",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [53],
      "documents": ["chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate rerun after the voice-separation repair; observed 1,411 Prose_Words. Supersedes GATE-CHAPTER-LOCAL-PRIVATE-DEFENSE-053, which is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T21:22:10Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-050-055-RERUN-001",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [50, 51, 52, 53, 54, 55],
      "documents": ["chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md", "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Six-file drafting-batch rerun for current Chapters 50–55 prose (7,178 Prose_Words) after the Chapter 53 repair. Supersedes GATE-BATCH-PRIVATE-DEFENSE-050-055, which is retained unedited."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-050-055-006-FOLLOWUP-001"],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-13T21:22:10Z"
  }
]
```
## Chapters 36–42 objective rerun on current post-revision prose

The task 13.2 results for this batch were produced on 2026-09-12, before the `DEC-018` revision reached these files, and no objective rerun had been recorded since. The batch was rerun on current prose. Counts and statuses are 36: 1,186, 37: 1,159, 38: 1,172, 39: 1,171, 40: 1,187, 41: 1,054, and 42: 1,057, all `normal` and all `revised`, for 7,986 Prose_Words. The run reported zero errors and zero warnings with no changed cross-document reference declared. The viewpoint sequence is Julian, Mara, Nia, Julian, Mara, Julian, Nia, so no two adjacent chapters share a POV.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-036-042-RERUN-001",
  "gate_type": "batch",
  "scope": {
    "chapter_numbers": [36, 37, 38, 39, 40, 41, 42],
    "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
    "description": "Seven-file drafting-batch audit of current Chapters 36–42 prose (7,986 Prose_Words), recorded because the task 13.2 results predate the DEC-018 revision of these files. Supersedes GATE-BATCH-PRIVATE-DEFENSE-036-042, which is retained unedited."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-PRIVATE-DEFENSE-BATCH-036-042"],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-13T21:42:42Z"
}
```

## Chapter 118 objective rerun after the `DEC-021` craft expansion

The expanded Chapter 118 was run in chapter scope after its header count was synchronized. The checker
reported `result=pass`, `exit=0`, zero errors, zero warnings, and no planning diagnostic. It observed
1,215 Prose_Words, matching the declared value; `normal`, `exploratory`, `POV-SAFIYA`,
`TL-CODA-ACCOUNT`, and `MOT-KETTLE-01` all agree with direct planning references.

No objective Coda batch result is invented here. Chapter Files 117 and 119 have not been delivered, so
there is no complete adjacent drafting batch to run; their ArcEntries supplied continuity boundaries to
the human local reread only.

```json record=GateResult schema=1
{
  "gate_result_id": "GATE-CHAPTER-LOCAL-AFTERMATH-CODA-118-DEC-021-RERUN-001",
  "gate_type": "chapter-local",
  "scope": {
    "chapter_numbers": [118],
    "documents": ["chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
    "description": "Chapter_Local_Gate rerun after the DEC-021-authorized Chapter 118 craft expansion; observed and declared 1,215 Prose_Words, normal length class, exploratory status, and all direct references agree. Supersedes the historical task 9 calibration-local result for current-file evidence without editing it."
  },
  "prerequisite_state": "complete",
  "objective_diagnostic_ids": [],
  "editorial_finding_ids": ["EDITORIAL-AFTERMATH-CODA-118-REPAIR-001", "EDITORIAL-REVISION-009-FOLLOWUP-002"],
  "result": "pass",
  "checker_exit_status": 0,
  "timestamp": "2026-09-18T22:10:00Z"
}
```

## Objective reruns after the voice-separation and spelling-normalization pass

Thirty-four Chapter_Files changed prose in this pass and every delivered batch was reaudited, because a
spelling standard was applied across the whole manuscript and craft repairs touched chapters in every
delivered batch. Each chapter and batch command reported `result=pass`, `exit=0`, zero errors and zero
warnings. Header `words` values were resynchronized from observed counts before the runs, and no
declared length class changed: Chapter 13 remains a `long-outlier`, Chapter 16 a `microchapter` at 679
Prose_Words, and Chapter 24 a `microchapter` at 594.

The global run continues to report the same 134 expected completion errors with `chapter=0 batch=0
planning=0`, which is the fail-closed contract behaving correctly against a half-delivered manuscript.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-001-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        1
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1199 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-002-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        2
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1144 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-004-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        4
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1178 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-005-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        5
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1182 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-006-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        6
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1195 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-007-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        7
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1124 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-009-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        9
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1042 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-010-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        10
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1066 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-012-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        12
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1098 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-013-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        13
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1858 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-014-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        14
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-014-rights-before-names.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1167 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-015-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        15
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1218 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-016-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        16
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-016-come-in.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 679 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-017-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        17
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1806 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-019-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        19
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1197 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-020-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        20
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1069 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-021-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        21
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-021-reconstruction.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1150 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-022-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        22
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-022-fundable.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1170 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-023-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        23
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1175 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-024-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        24
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-024-not-case-zero.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 594 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-025-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        25
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1153 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-026-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        26
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-026-already-outside.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1196 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-027-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        27
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1215 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-028-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        28
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-028-named-second.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1216 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-029-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        29
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1203 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-031-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        31
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1144 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-034-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        34
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1129 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-038-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        38
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1242 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-042-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        42
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1061 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-046-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        46
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1060 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-052-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        52
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1485 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-057-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        57
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-057-no-longer-current.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 887 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-073-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        73
      ],
      "documents": [
        "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1157 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-118-VOICE-PASS-RERUN",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [
        118
      ],
      "documents": [
        "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Chapter_Local_Gate rerun after the voice-separation and spelling-normalization pass; observed and declared 1109 Prose_Words with the declared length class unchanged."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-001-005-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        1,
        2,
        3,
        4,
        5
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-001-noise-floor.md",
        "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md",
        "chapters/discovery-part/discovery-part-003-the-failed-check.md",
        "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md",
        "chapters/discovery-part/discovery-part-005-not-a-message.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 5895 Prose_Words across 5 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-006-010-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        6,
        7,
        8,
        9,
        10
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-006-no-transmit-stage.md",
        "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md",
        "chapters/discovery-part/discovery-part-008-provisional-identity.md",
        "chapters/discovery-part/discovery-part-009-appetite-before-result.md",
        "chapters/discovery-part/discovery-part-010-no-form-for-this.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 5627 Prose_Words across 5 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-011-015-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        11,
        12,
        13,
        14,
        15
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md",
        "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md",
        "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md",
        "chapters/discovery-part/discovery-part-014-rights-before-names.md",
        "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 6519 Prose_Words across 5 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-016-020-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        16,
        17,
        18,
        19,
        20
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-016-come-in.md",
        "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md",
        "chapters/discovery-part/discovery-part-018-clean-silence.md",
        "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md",
        "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 5885 Prose_Words across 5 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-021-025-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        21,
        22,
        23,
        24,
        25
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-021-reconstruction.md",
        "chapters/discovery-part/discovery-part-022-fundable.md",
        "chapters/discovery-part/discovery-part-023-the-match-holds.md",
        "chapters/discovery-part/discovery-part-024-not-case-zero.md",
        "chapters/discovery-part/discovery-part-025-nothing-admissible.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 5242 Prose_Words across 5 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-026-029-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        26,
        27,
        28,
        29
      ],
      "documents": [
        "chapters/discovery-part/discovery-part-026-already-outside.md",
        "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md",
        "chapters/discovery-part/discovery-part-028-named-second.md",
        "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 4830 Prose_Words across 4 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-030-035-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        30,
        31,
        32,
        33,
        34,
        35
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-030-something-came-in.md",
        "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md",
        "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md",
        "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md",
        "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md",
        "chapters/private-defense-part/private-defense-part-035-a-private-no.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 6993 Prose_Words across 6 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-036-042-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        36,
        37,
        38,
        39,
        40,
        41,
        42
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md",
        "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md",
        "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md",
        "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md",
        "chapters/private-defense-part/private-defense-part-040-first-calibration.md",
        "chapters/private-defense-part/private-defense-part-041-two-interpreters.md",
        "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 8060 Prose_Words across 7 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-043-049-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        43,
        44,
        45,
        46,
        47,
        48,
        49
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md",
        "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md",
        "chapters/private-defense-part/private-defense-part-045-page-nine.md",
        "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md",
        "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md",
        "chapters/private-defense-part/private-defense-part-048-the-refusal.md",
        "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 7643 Prose_Words across 7 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-050-055-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        50,
        51,
        52,
        53,
        54,
        55
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-050-the-softened-minutes.md",
        "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md",
        "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md",
        "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md",
        "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md",
        "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 7178 Prose_Words across 6 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-056-061-VOICE-PASS-RERUN",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [
        56,
        57,
        58,
        59,
        60,
        61
      ],
      "documents": [
        "chapters/private-defense-part/private-defense-part-056-ask-first.md",
        "chapters/private-defense-part/private-defense-part-057-no-longer-current.md",
        "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md",
        "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md",
        "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md",
        "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md",
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/motif-ledger.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md"
      ],
      "description": "Drafting-batch audit rerun on current prose after the voice-separation and spelling-normalization pass; 6957 Prose_Words across 6 files, zero errors and zero warnings."
    },
    "prerequisite_state": "complete",
    "objective_diagnostic_ids": [],
    "editorial_finding_ids": [],
    "result": "pass",
    "checker_exit_status": 0,
    "timestamp": "2026-09-18T23:40:00Z"
  }
]
```

## `ARC-CHANGE-VOICE-SEPARATION-002` objective reruns

The paragraph-scale Nia repair changed eighteen Nia Chapter Files and one collateral Mara chapter needed to preserve the Chapter 34-to-35 pad handoff. Every changed chapter passed a fresh Chapter_Local_Gate. Every complete delivered drafting batch containing one of those chapters passed a fresh batch audit, including the changed `planning/arc-outline.md` reference for Chapters 21 and 73. The full eight-chapter Calibration_Batch and repository site-isolation contract also pass. These records preserve all chapter statuses as `revised`; objective success does not substitute for editorial approval or promote a chapter.

```json record=GateResult schema=1
[
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-002-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [2],
      "documents": ["chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1095 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-004-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [4],
      "documents": ["chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1023 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-007-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [7],
      "documents": ["chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 804 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-012-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [12],
      "documents": ["chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1019 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-017-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [17],
      "documents": ["chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1438 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-019-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [19],
      "documents": ["chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 812 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-021-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [21],
      "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 610 Prose_Words, microchapter, revised, with a synchronized compression purpose and zero errors or warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-024-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [24],
      "documents": ["chapters/discovery-part/discovery-part-024-not-case-zero.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 475 Prose_Words, microchapter, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-028-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [28],
      "documents": ["chapters/discovery-part/discovery-part-028-named-second.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1157 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-031-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [31],
      "documents": ["chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1001 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-034-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [34],
      "documents": ["chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1166 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-035-VOICE-SEPARATION-002-COLLATERAL",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [35],
      "documents": ["chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the collateral Chapter 34-to-35 pad-handoff repair; observed and declared 1509 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-038-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [38],
      "documents": ["chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1206 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-042-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [42],
      "documents": ["chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 766 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-047-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [47],
      "documents": ["chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1038 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-052-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [52],
      "documents": ["chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1333 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-056-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [56],
      "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1542 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-060-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [60],
      "documents": ["chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1125 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CHAPTER-LOCAL-073-VOICE-SEPARATION-002",
    "gate_type": "chapter-local",
    "scope": {
      "chapter_numbers": [73],
      "documents": ["chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Chapter_Local_Gate after the paragraph-scale Nia repair; observed and declared 1230 Prose_Words, normal, revised, with zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-001-005-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [1, 2, 3, 4, 5],
      "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 5691 Prose_Words across Chapters 1-5, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-006-010-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [6, 7, 8, 9, 10],
      "documents": ["chapters/discovery-part/discovery-part-006-no-transmit-stage.md", "chapters/discovery-part/discovery-part-007-the-detail-she-keeps.md", "chapters/discovery-part/discovery-part-008-provisional-identity.md", "chapters/discovery-part/discovery-part-009-appetite-before-result.md", "chapters/discovery-part/discovery-part-010-no-form-for-this.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 5307 Prose_Words across Chapters 6-10, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-011-015-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [11, 12, 13, 14, 15],
      "documents": ["chapters/discovery-part/discovery-part-011-the-mind-as-a-field.md", "chapters/discovery-part/discovery-part-012-one-call-end-to-end.md", "chapters/discovery-part/discovery-part-013-spectrum-to-bone.md", "chapters/discovery-part/discovery-part-014-rights-before-names.md", "chapters/discovery-part/discovery-part-015-who-will-be-holding-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 6363 Prose_Words across Chapters 11-15, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-016-020-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [16, 17, 18, 19, 20],
      "documents": ["chapters/discovery-part/discovery-part-016-come-in.md", "chapters/discovery-part/discovery-part-017-two-calls-one-unit.md", "chapters/discovery-part/discovery-part-018-clean-silence.md", "chapters/discovery-part/discovery-part-019-no-history-for-a-certainty.md", "chapters/discovery-part/discovery-part-020-a-belief-with-nothing-under-it.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 5132 Prose_Words across Chapters 16-20, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-021-025-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [21, 22, 23, 24, 25],
      "documents": ["chapters/discovery-part/discovery-part-021-reconstruction.md", "chapters/discovery-part/discovery-part-022-fundable.md", "chapters/discovery-part/discovery-part-023-the-match-holds.md", "chapters/discovery-part/discovery-part-024-not-case-zero.md", "chapters/discovery-part/discovery-part-025-nothing-admissible.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 4453 Prose_Words across Chapters 21-25, including the changed arc-outline reference for Chapter 21's microchapter classification, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-DISCOVERY-026-029-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [26, 27, 28, 29],
      "documents": ["chapters/discovery-part/discovery-part-026-already-outside.md", "chapters/discovery-part/discovery-part-027-the-door-runs-inward.md", "chapters/discovery-part/discovery-part-028-named-second.md", "chapters/discovery-part/discovery-part-029-locking-a-door-it-never-used.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 4747 Prose_Words across Chapters 26-29, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-030-035-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [30, 31, 32, 33, 34, 35],
      "documents": ["chapters/private-defense-part/private-defense-part-030-something-came-in.md", "chapters/private-defense-part/private-defense-part-031-copper-and-quiet.md", "chapters/private-defense-part/private-defense-part-032-a-handle-on-the-inside.md", "chapters/private-defense-part/private-defense-part-033-reception-transmission-consent.md", "chapters/private-defense-part/private-defense-part-034-what-a-room-costs.md", "chapters/private-defense-part/private-defense-part-035-a-private-no.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair and collateral Chapter 35 handoff repair; 7590 Prose_Words across Chapters 30-35, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-036-042-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [36, 37, 38, 39, 40, 41, 42],
      "documents": ["chapters/private-defense-part/private-defense-part-036-electronic-speech-pairings.md", "chapters/private-defense-part/private-defense-part-037-the-send-gate-holds.md", "chapters/private-defense-part/private-defense-part-038-two-dispatchers-one-incident.md", "chapters/private-defense-part/private-defense-part-039-a-benefit-becomes-a-platform.md", "chapters/private-defense-part/private-defense-part-040-first-calibration.md", "chapters/private-defense-part/private-defense-part-041-two-interpreters.md", "chapters/private-defense-part/private-defense-part-042-not-a-conversation.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 7836 Prose_Words across Chapters 36-42, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-043-049-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [43, 44, 45, 46, 47, 48, 49],
      "documents": ["chapters/private-defense-part/private-defense-part-043-a-term-sheet-and-a-pen.md", "chapters/private-defense-part/private-defense-part-044-a-clause-he-can-constrain.md", "chapters/private-defense-part/private-defense-part-045-page-nine.md", "chapters/private-defense-part/private-defense-part-046-nothing-to-strike.md", "chapters/private-defense-part/private-defense-part-047-my-case-in-their-appendix.md", "chapters/private-defense-part/private-defense-part-048-the-refusal.md", "chapters/private-defense-part/private-defense-part-049-filed-as-agreed.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 7247 Prose_Words across Chapters 43-49, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-050-055-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [50, 51, 52, 53, 54, 55],
      "documents": ["chapters/private-defense-part/private-defense-part-050-the-roof-is-not-the-building.md", "chapters/private-defense-part/private-defense-part-051-put-that-on-the-record.md", "chapters/private-defense-part/private-defense-part-052-on-my-own-conditions.md", "chapters/private-defense-part/private-defense-part-053-cleared-and-not-relieved.md", "chapters/private-defense-part/private-defense-part-054-older-than-the-archive.md", "chapters/private-defense-part/private-defense-part-055-the-price-of-the-instruments.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 7206 Prose_Words across Chapters 50-55, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-BATCH-PRIVATE-DEFENSE-056-061-VOICE-SEPARATION-002",
    "gate_type": "batch",
    "scope": {
      "chapter_numbers": [56, 57, 58, 59, 60, 61],
      "documents": ["chapters/private-defense-part/private-defense-part-056-ask-first.md", "chapters/private-defense-part/private-defense-part-057-no-longer-current.md", "chapters/private-defense-part/private-defense-part-058-metadata-and-nothing-else.md", "chapters/private-defense-part/private-defense-part-059-say-it-out-loud.md", "chapters/private-defense-part/private-defense-part-060-fluent-is-not-open.md", "chapters/private-defense-part/private-defense-part-061-come-in-but-ask.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Current drafting-batch audit after the Nia paragraph repair; 7233 Prose_Words across Chapters 56-61, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-CALIBRATION-OBJECTIVE-VOICE-SEPARATION-002",
    "gate_type": "calibration-objective",
    "scope": {
      "chapter_numbers": [1, 2, 3, 4, 5, 73, 118, 124],
      "documents": ["chapters/discovery-part/discovery-part-001-noise-floor.md", "chapters/discovery-part/discovery-part-002-an-ordinary-morning.md", "chapters/discovery-part/discovery-part-003-the-failed-check.md", "chapters/discovery-part/discovery-part-004-no-gap-on-her-side.md", "chapters/discovery-part/discovery-part-005-not-a-message.md", "chapters/mindwars-part/mindwars-part-073-did-i-say-yes.md", "chapters/aftermath-coda/aftermath-coda-118-tuesday-kettle-on.md", "chapters/aftermath-coda/aftermath-coda-124-truthful-refusal.md", "planning/arc-outline.md", "planning/canon-bible.md", "planning/motif-ledger.md", "planning/pov-roster.md", "planning/voice-briefs.md"],
      "description": "Full current Calibration_Batch objective rerun after substantive Nia repairs in Chapters 2, 4, and 73 and the changed arc-outline reference; 8817 Prose_Words, zero errors and zero warnings."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:40:00Z"
  },
  {
    "gate_result_id": "GATE-SITE-ISOLATION-VOICE-SEPARATION-002",
    "gate_type": "site-isolation",
    "scope": {
      "chapter_numbers": [],
      "documents": ["exclusion-contract.json"],
      "description": "Repository site-isolation rerun after the voice-separation repair; the configured manuscript root remained excluded and the collector found zero manuscript entries. This local result does not prove external Site_Build adoption."
    },
    "prerequisite_state": "complete", "objective_diagnostic_ids": [], "editorial_finding_ids": [], "result": "pass", "checker_exit_status": 0, "timestamp": "2026-09-19T00:42:00Z"
  }
]
```
