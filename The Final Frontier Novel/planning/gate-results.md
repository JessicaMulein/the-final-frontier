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