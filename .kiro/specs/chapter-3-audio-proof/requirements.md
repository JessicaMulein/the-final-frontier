# Requirements Document

## Introduction

This document derives the behavioral requirements for a guarded, paid Chapter 3 Tiffany/Nova Sonic 2 proof from the approved design. The workflow uses the existing narration runtime, isolates one separately confirmed paid attempt after nonbillable gates, validates all produced evidence deterministically, preserves prior work, and delivers a clearly named proof WAV with auditable token and cost evidence.

Specification creation is planning only. Specification creation does not authorize AWS identity access, model access, tests, narration, or a paid render.

## Glossary

- **Audio_Proof_Workflow**: The complete Chapter 3 inspection, preflight, paid-attempt, validation, accounting, delivery, and reporting process.
- **Chapter_3_Source**: `The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md`.
- **Restricted_Header**: The exact nine-field YAML-like header accepted by the existing manuscript parser.
- **Prose_Body**: The Chapter_3_Source content after the closing Restricted_Header delimiter.
- **Spoken_Text**: Prose_Body after the existing `markdown_to_spoken` transformation removes supported inline emphasis.
- **Spoken_Token**: A token produced by normalization `frontier-word-sequence-v1`.
- **Source_Inspector**: The read-only component that resolves Chapter_3_Source and derives header, count, hash, and local segmentation evidence.
- **Source_Snapshot**: The approved preflight record of Chapter_3_Source metadata, counts, hashes, and local plan.
- **Runtime_Verifier**: The read-only component that validates the installed configuration, Python runtime, voice, model, region, audio format, and fidelity policy.
- **Existing_Narration_CLI**: `.venv/bin/python -m frontier_audiobook` executed from `/Users/jessica/Documents/frontier-book/.audiobook`.
- **Targeted_Checks**: Nonbillable checks for the paid guard, source transformation, segmentation, reuse, source-drift protection, complete event replay, and atomic paid wrapper.
- **Broader_Suite_Result**: A result from a test scope wider than Targeted_Checks, when such a scope is run independently.
- **Dry_Run**: The Existing_Narration_CLI Chapter 3 narration plan invoked with `--dry-run` and without paid confirmation.
- **Named_AWS_Profile**: The exact profile label `frontier-audiobook`; successful non-model identity resolution is its sole credential acceptance condition.
- **Identity_Evidence**: The persisted Named_AWS_Profile label, identity-resolution boolean, and timestamp only.
- **Official_Rate**: A current Nova Sonic 2.0 on-demand `us-east-1` USD rate per 1,000 tokens from an official AWS pricing source.
- **Four_Modality_Tokens**: Input speech, input text, output speech, and output text token counts.
- **Paid_Confirmation**: A separate explicit authorization obtained immediately before one paid Chapter 3 invocation; this specification is not Paid_Confirmation.
- **Paid_Attempt_Wrapper**: The Python standard-library process wrapper that stages, captures, flushes, and atomically commits the paid console log and native exit evidence.
- **Paid_Attempt**: The single allowed `paid-attempt-001` direct-child invocation of Existing_Narration_CLI.
- **Paid_Attempt_Bundle**: The atomically committed directory containing `render-console.log` and `attempt.json` for Paid_Attempt.
- **Charge_Uncertain**: A state in which a launched Paid_Attempt lacks complete, hash-consistent, committed evidence with an integer native return code.
- **Exact_Fidelity**: Equality of expected and FINAL transcript Spoken_Token sequences, matching replayed LPCM, and zero mid-sentence partial turns.
- **Chapter_3_Build_Root**: `.audiobook/build/narration/chapter-003-tiffany/`.
- **Chapter_3_Manifest**: `Chapter_3_Build_Root/manifest.json`.
- **Active_Segment**: A record in the final Chapter_3_Manifest `segments` collection used in the delivered assembly.
- **Reused_Segment**: An Active_Segment accepted from an intact matching Chapter 3 artifact without a new model call in Paid_Attempt.
- **Event_Journal**: The JSONL Nova output-event file bound by active audio filename stem to one Active_Segment.
- **Postflight_Validator**: The read-only validator for source, attempt, manifest, segment, journal, WAV, usage, cost, and isolation evidence.
- **Chapter_WAV**: `.audiobook/build/narration/chapter-003-tiffany/chapter-003-tiffany.wav`.
- **Proof_Copy**: `voice-samples/chapter-3-tiffany-proof.wav`.
- **Proof_Deliverer**: The collision-safe component that creates or retains a byte-identical Proof_Copy after deterministic validation.
- **Active_Artifact_Totals**: Four_Modality_Tokens aggregated from exactly one validated Event_Journal per Active_Segment, including Reused_Segments.
- **Current_Execution_Totals**: Four_Modality_Tokens aggregated only from segments newly narrated during Paid_Attempt.
- **Cost_Calculator**: The Decimal-based component that applies each Official_Rate to the corresponding token modality.
- **Computed_Pre_Tax_Service_Cost**: A token-derived service cost before taxes, credits, discounts, invoice rounding, or account adjustments.
- **Billing_Confirmation**: A separately obtained Cost Explorer or invoice amount and confirmation date.
- **Proof_Report**: `.audiobook/build/narration/chapter-003-tiffany/chapter-003-tiffany-proof-report.md`.
- **Evidence_Artifact**: A generated file under `Chapter_3_Build_Root/evidence/` or Proof_Report; existing runtime manifest, transcript, Event_Journal, segment-audio, and Chapter_WAV files retain their required runtime schemas and are not Evidence_Artifacts.
- **Listening_Acceptance**: Optional human proof-listening feedback recorded only after deterministic validation.
- **Workflow_Write_Allowlist**: Chapter_3_Build_Root and, after delivery approval, Proof_Copy.
- **Protected_Artifact**: Chapter_3_Source, narration source/configuration/dependencies, relevant tests/tools, Chapter 1 and Chapter 2 audio artifacts, `.kiro/specs/chapter-2-audio-proof/`, and `.kiro/specs/The-Final-Frontier-novel/`.
- **Per_File_Inventory**: Path, existence, byte count, SHA-256, Git status, and attribution recorded for each relevant file.
- **Concurrent_Manuscript_Change**: A changed manuscript path other than Chapter_3_Source that is not attributed to an Audio_Proof_Workflow write.
- **Delivery_Gate**: The all-pass condition for source, paid-attempt, manifest, fidelity, assembly, usage, cost, isolation, and proof-copy prerequisites.
- **Publishing_Workstream**: The separately requested written-edition and audiobook-edition front-matter/title-page work, which is outside Audio_Proof_Workflow.

## Requirements

### Requirement 1: Freeze the exact Chapter 3 source and runtime contract

**User Story:** As the proof operator, I want the actual Chapter 3 source and installed runtime measured before execution, so that the paid operation cannot inherit Chapter 2 counts or stale assumptions.

#### Acceptance Criteria

1. THE Source_Inspector SHALL resolve Chapter_3_Source to exactly one manuscript file.
2. WHEN Source_Inspector parses Restricted_Header, THE Source_Inspector SHALL verify `movement: discovery_part`, `chapter: 3`, `pov_id: POV-MARA`, `timeline_id: TL-DECEMBER-RECEIVE`, `motif_events: []`, the approved hook text, `words: 1192`, `length_class: normal`, and `status: revised`.
3. WHEN Source_Inspector normalizes Prose_Body, THE Source_Inspector SHALL verify a Prose_Body word count of `1192`.
4. WHEN Source_Inspector creates Spoken_Text, THE Source_Inspector SHALL verify `1193` Spoken_Tokens, Prose_Body SHA-256 `a07e7dff0cceea845107eb49958c84092754daa5531ec794ea5325adfe546d45`, and Spoken_Text SHA-256 `a78247a0639799d40d66a16c5d27bc0c67dd64f42d589c7a72e132e39e59cfa7`.
5. WHEN Source_Inspector applies target segment size `5`, THE Source_Inspector SHALL verify `91` ordered segments, `10` narration-only-punctuation segments, and Spoken_Token conservation across the segments.
6. THE Runtime_Verifier SHALL verify Python 3.12 compatibility, voice `tiffany`, model `amazon.nova-2-sonic-v1:0`, region `us-east-1`, normalization `frontier-word-sequence-v1`, target segment size `5`, and 24 kHz 16-bit mono output.
7. IF any source or runtime contract value differs, THEN THE Audio_Proof_Workflow SHALL block Paid_Confirmation.

### Requirement 2: Establish scoped isolation and preserve prior work

**User Story:** As the manuscript owner, I want per-file protection and honest attribution, so that Chapter 3 work preserves prior audio and specs without treating unrelated concurrent manuscript edits as workflow changes.

#### Acceptance Criteria

1. WHEN preflight begins, THE Audio_Proof_Workflow SHALL capture a Per_File_Inventory for every Protected_Artifact.
2. THE Per_File_Inventory SHALL record workspace-relative path, existence, byte count, SHA-256, Git status, and initial attribution for each selected file.
3. THE Audio_Proof_Workflow SHALL define Workflow_Write_Allowlist as Chapter_3_Build_Root plus Proof_Copy after Delivery_Gate approval.
4. WHILE Audio_Proof_Workflow executes, THE Audio_Proof_Workflow SHALL attribute task-created files only to paths in Workflow_Write_Allowlist.
5. WHEN isolation is evaluated, THE Audio_Proof_Workflow SHALL compare Protected_Artifacts by individual path and SHA-256 rather than use a whole-novel aggregate as the sole gate.
6. WHEN a non-Chapter-3 manuscript file changes without workflow-write evidence, THE Audio_Proof_Workflow SHALL record the path as Concurrent_Manuscript_Change separately from workflow-owned changes.
7. WHEN Concurrent_Manuscript_Change exists, THE Delivery_Gate SHALL evaluate Chapter_3_Source and hard Protected_Artifact invariants independently from the whole-novel aggregate.
8. IF a workflow-owned write occurs outside Workflow_Write_Allowlist, THEN THE Audio_Proof_Workflow SHALL block Delivery_Gate.
9. THE Audio_Proof_Workflow SHALL preserve every Chapter 1 and Chapter 2 narration build artifact and proof-audio file at its preflight SHA-256.
10. THE Audio_Proof_Workflow SHALL preserve `.kiro/specs/chapter-2-audio-proof/` and `.kiro/specs/The-Final-Frontier-novel/` at their preflight per-file SHA-256 values.
11. THE Audio_Proof_Workflow SHALL preserve front-matter and title-page files for the written and audiobook editions without modification.
12. THE Proof_Report SHALL identify Publishing_Workstream as separate from Audio_Proof_Workflow.

### Requirement 3: Complete targeted and nonbillable local preflight

**User Story:** As the paying operator, I want focused checks and an exact dry run before AWS access, so that relevant regressions block payment while unrelated suite failures remain visible but separate.

#### Acceptance Criteria

1. WHEN local preflight runs, THE Targeted_Checks SHALL verify the paid guard, source transformation, segmentation conservation, reuse validation, source-drift stops, safe-turn behavior, and complete Event_Journal replay.
2. WHEN Paid_Attempt_Wrapper is prepared, THE Targeted_Checks SHALL verify direct native return-code capture for synthetic exit `0` and a representative synthetic nonzero exit without AWS access.
3. IF a Targeted_Check fails, THEN THE Audio_Proof_Workflow SHALL block Dry_Run and Paid_Confirmation.
4. WHEN Audio_Proof_Workflow invokes Dry_Run, THE Audio_Proof_Workflow SHALL use chapter `3`, voice `tiffany`, target segment size `5`, and `--dry-run` without paid confirmation.
5. WHEN Dry_Run completes, THE Audio_Proof_Workflow SHALL verify chapter `3`, voice `tiffany`, word count `1193`, planned calls `91`, and billable calls `0`.
6. WHEN preflight inventories Chapter_3_Build_Root, THE Audio_Proof_Workflow SHALL classify prior state as absent, reusable, rejected, or Charge_Uncertain.
7. IF prior Chapter 3 state is malformed, conflicting, or Charge_Uncertain, THEN THE Audio_Proof_Workflow SHALL block Paid_Confirmation.
8. WHEN Broader_Suite_Result is available, THE Proof_Report SHALL record Broader_Suite_Result separately from Targeted_Checks.
9. IF a Broader_Suite_Result failure overlaps a Targeted_Check contract, THEN THE Audio_Proof_Workflow SHALL classify the overlapping failure as blocking.
10. IF a Broader_Suite_Result failure does not overlap a Targeted_Check contract, THEN THE Audio_Proof_Workflow SHALL retain the failure as a non-gating diagnostic.

### Requirement 4: Verify the fixed profile and current official rates without a model call

**User Story:** As the paying operator, I want minimal identity verification and current official rates before authorization, so that the correct account boundary and cost basis are known without exposing identity details.

#### Acceptance Criteria

1. WHEN external preflight begins, THE Audio_Proof_Workflow SHALL invoke one non-model identity call with Named_AWS_Profile.
2. WHEN the identity call succeeds, THE Audio_Proof_Workflow SHALL accept successful resolution as the sole credential acceptance condition.
3. WHEN Identity_Evidence is persisted, THE Audio_Proof_Workflow SHALL retain only the profile label, identity-resolution boolean, and UTC timestamp.
4. THE Audio_Proof_Workflow SHALL sanitize Identity_Evidence by excluding account IDs, ARNs, user or role identifiers, access keys, credential values, credential type, credential source, credential age, credential expiration, and every other returned identity field.
5. WHEN external preflight retrieves pricing, THE Audio_Proof_Workflow SHALL resolve one current Official_Rate for each Four_Modality_Tokens category for Nova Sonic 2.0 on-demand inference in `us-east-1`.
6. WHEN Official_Rates are persisted, THE Audio_Proof_Workflow SHALL record official source URL, offer publication date, retrieval date, effective date, model, region, purchase option, currency, unit, and exact decimal rate.
7. THE Audio_Proof_Workflow SHALL record zero Bedrock model calls for external preflight.
8. IF Named_AWS_Profile fails to resolve or any Official_Rate is missing or ambiguous, THEN THE Audio_Proof_Workflow SHALL block Paid_Confirmation.

### Requirement 5: Isolate one separately confirmed paid attempt with definitive process evidence

**User Story:** As the paying operator, I want one explicitly confirmed invocation with atomic native-exit evidence, so that a complete console summary cannot hide an unknown process status or trigger an accidental retry.

#### Acceptance Criteria

1. THE Audio_Proof_Workflow SHALL classify `design.md`, `requirements.md`, `tasks.md`, and `.config.kiro` as planning artifacts that do not provide Paid_Confirmation.
2. WHEN Requirements 1 through 4 pass, THE Audio_Proof_Workflow SHALL request Paid_Confirmation immediately before Paid_Attempt.
3. IF Paid_Confirmation is absent, declined, or not tied to `paid-attempt-001`, THEN THE Audio_Proof_Workflow SHALL stop before a Bedrock model call.
4. WHEN Paid_Confirmation explicitly authorizes `paid-attempt-001`, THE Audio_Proof_Workflow SHALL invoke Existing_Narration_CLI exactly once with Named_AWS_Profile, chapter `3`, voice `tiffany`, target segment size `5`, and `--confirm-paid-render`.
5. WHEN Paid_Attempt begins, THE Existing_Narration_CLI SHALL enforce Exact_Fidelity without `--accept-verbatim-prefix`.
6. WHEN an intact prior segment matches current text and Exact_Fidelity policy, THE Existing_Narration_CLI SHALL classify the segment as Reused_Segment.
7. WHEN an Active_Segment lacks acceptable reusable evidence, THE Existing_Narration_CLI SHALL make at most one new model call for the Active_Segment during Paid_Attempt.
8. WHEN Paid_Attempt_Wrapper starts, THE Paid_Attempt_Wrapper SHALL create a same-filesystem staging directory and spawn Existing_Narration_CLI as a direct child process.
9. WHILE the direct child runs, THE Paid_Attempt_Wrapper SHALL tee combined stdout and stderr to the operator and staged `render-console.log`.
10. WHEN the direct child exits, THE Paid_Attempt_Wrapper SHALL capture the native integer return code directly from the child-process wait operation.
11. WHEN attempt evidence is complete, THE Paid_Attempt_Wrapper SHALL write the exact argv, working directory, profile label, timestamps, native return code, console SHA-256, termination signal, no-retry value, and exact-fidelity value to staged `attempt.json`.
12. WHEN staged attempt evidence is flushed and synchronized, THE Paid_Attempt_Wrapper SHALL atomically rename the staging directory to Paid_Attempt_Bundle.
13. IF a launched Paid_Attempt leaves staging evidence, omits an integer native return code, omits a required file, or produces a hash inconsistency, THEN THE Audio_Proof_Workflow SHALL classify Paid_Attempt as Charge_Uncertain.
14. IF Paid_Attempt returns a nonzero native return code, THEN THE Audio_Proof_Workflow SHALL retain evidence and stop without retry.
15. IF Paid_Attempt fails Exact_Fidelity, crosses a mid-sentence partial turn, is interrupted, or becomes Charge_Uncertain, THEN THE Audio_Proof_Workflow SHALL stop without automatic retry.

### Requirement 6: Validate the final manifest and every active segment

**User Story:** As the proof listener, I want the active set bound to the approved Chapter 3 spoken sequence and recorded output events, so that stale, missing, reordered, or inexact artifacts cannot enter the proof.

#### Acceptance Criteria

1. WHEN Paid_Attempt completes with native return code `0`, THE Postflight_Validator SHALL verify Chapter_3_Manifest chapter, voice, source path, source hash, spoken hash, spoken word count, target segment size, segment count, narration-only-punctuation count, and Chapter_WAV path against Source_Snapshot.
2. THE Postflight_Validator SHALL verify `segment_count` equals `91` and equals the number of Active_Segments.
3. THE Postflight_Validator SHALL verify Active_Segment identifiers are unique and contiguous from `0001` through `0091` in assembly order.
4. THE Postflight_Validator SHALL verify concatenated Active_Segment Spoken_Tokens equal the `1193`-token Spoken_Text sequence.
5. THE Postflight_Validator SHALL verify every Active_Segment has status `narrated`, exact transcript match `true`, coverage ratio `1.0`, and zero mid-sentence partial turns.
6. THE Postflight_Validator SHALL verify every Active_Segment audio SHA-256 against current segment WAV bytes.
7. THE Postflight_Validator SHALL replay every bound Event_Journal and verify reconstructed FINAL transcript and LPCM against the accepted transcript and segment WAV.
8. THE Postflight_Validator SHALL exclude `carried_over_segments` from active fidelity, assembly, segment, and token totals.
9. IF any manifest, Active_Segment, or Event_Journal replay check fails, THEN THE Audio_Proof_Workflow SHALL block Delivery_Gate.

### Requirement 7: Validate assembly and deliver a collision-safe proof copy

**User Story:** As the proof listener, I want one correctly assembled and clearly named Chapter 3 WAV, so that the proof is complete and cannot overwrite a different recording.

#### Acceptance Criteria

1. WHEN every Active_Segment passes Exact_Fidelity, THE Existing_Narration_CLI SHALL assemble Chapter_WAV from the ordered Active_Segments under the recorded stitching profile.
2. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify the recorded chapter SHA-256 against Chapter_WAV bytes.
3. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify 24 kHz sample rate, 16-bit sample size, one channel, and uncompressed PCM encoding.
4. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify manifest duration against frame-derived duration to manifest precision.
5. WHEN Delivery_Gate passes and Proof_Copy is absent, THE Proof_Deliverer SHALL copy Chapter_WAV to Proof_Copy.
6. WHEN Delivery_Gate passes and Proof_Copy is byte-identical to Chapter_WAV, THE Proof_Deliverer SHALL retain Proof_Copy and record `already-identical`.
7. IF Proof_Copy exists with a different SHA-256, THEN THE Proof_Deliverer SHALL leave Proof_Copy unchanged and report a collision failure.
8. WHEN Proof_Copy is created or retained, THE Proof_Deliverer SHALL verify identical byte counts, complete byte sequences, and SHA-256 values for Proof_Copy and Chapter_WAV.

### Requirement 8: Reconcile exact usage and reuse accounting

**User Story:** As the paying operator, I want exact journal-derived usage for the delivered artifacts and current invocation, so that reused work and newly billed work remain distinct.

#### Acceptance Criteria

1. THE Postflight_Validator SHALL resolve exactly one Event_Journal from the active audio stem of every Active_Segment.
2. WHEN Postflight_Validator parses Event_Journal, THE Postflight_Validator SHALL sum only integer modality-specific `usageEvent.details.delta` values.
3. WHEN one Event_Journal aggregation completes, THE Postflight_Validator SHALL verify each modality sum against the terminal modality `details.total` value.
4. WHEN one Event_Journal aggregation completes, THE Postflight_Validator SHALL verify combined modality sums against terminal top-level input, output, and total token values.
5. THE Postflight_Validator SHALL calculate Active_Artifact_Totals from exactly one validated Event_Journal per Active_Segment.
6. THE Postflight_Validator SHALL calculate Current_Execution_Totals from only segments newly narrated during Paid_Attempt.
7. WHEN Reused_Segment is reported, THE Postflight_Validator SHALL assign zero current-execution billable calls to Reused_Segment.
8. WHEN Reused_Segment is reported, THE Postflight_Validator SHALL assign zero Current_Execution_Totals to Reused_Segment.
9. IF Event_Journal is missing, duplicated, malformed, unbound, or internally inconsistent, THEN THE Audio_Proof_Workflow SHALL block Delivery_Gate.

### Requirement 9: Calculate current official service cost and separate billing confirmation

**User Story:** As the paying operator, I want reproducible four-modality cost calculations, so that a service estimate is transparent and never misrepresented as account billing confirmation.

#### Acceptance Criteria

1. WHEN cost calculation begins, THE Cost_Calculator SHALL reverify one current Official_Rate for each Four_Modality_Tokens category.
2. WHEN token totals and Official_Rates are available, THE Cost_Calculator SHALL use Decimal arithmetic to calculate each modality subtotal as `tokens × rate_per_1k ÷ 1000`.
3. THE Cost_Calculator SHALL calculate one Computed_Pre_Tax_Service_Cost from Active_Artifact_Totals.
4. THE Cost_Calculator SHALL calculate one Computed_Pre_Tax_Service_Cost from Current_Execution_Totals.
5. THE Cost_Calculator SHALL include input speech, input text, output speech, and output text tokens, rates, formulas, and subtotals in each Computed_Pre_Tax_Service_Cost.
6. WHEN Computed_Pre_Tax_Service_Cost is reported, THE Cost_Calculator SHALL label Billing_Confirmation as a separate pending, not-performed, or confirmed amount with confirmation date.
7. IF all four Official_Rates cannot be verified from an official AWS source, THEN THE Cost_Calculator SHALL block Computed_Pre_Tax_Service_Cost rather than substitute another rate source.

### Requirement 10: Produce sanitized, deterministic, and supplemental evidence

**User Story:** As the manuscript owner, I want one auditable Chapter 3 report, so that deterministic proof results, costs, concurrent work, and optional listening feedback remain clearly distinguished.

#### Acceptance Criteria

1. WHEN Delivery_Gate passes, THE Audio_Proof_Workflow SHALL create Proof_Report at the specified Chapter_3_Build_Root path.
2. THE Proof_Report SHALL identify Chapter_3_Source path, Restricted_Header contract, source hashes, Prose_Body count, Spoken_Token count, model, region, voice, profile label, target segment size, and timestamps.
3. THE Proof_Report SHALL state exact paid argv, native return code, console SHA-256, invocation count, retry count, and exact-fidelity mode.
4. THE Proof_Report SHALL state active-set, exact-fidelity, partial-turn, replay, assembly, duration, format, newly narrated, Reused_Segment, and proof-copy results.
5. THE Proof_Report SHALL contain Active_Artifact_Totals and Current_Execution_Totals for every Four_Modality_Tokens category.
6. THE Proof_Report SHALL contain current Official_Rates, provenance, modality formulas, modality subtotals, both Computed_Pre_Tax_Service_Cost values, and separate Billing_Confirmation status.
7. THE Proof_Report SHALL contain matching Chapter_WAV and Proof_Copy byte counts and SHA-256 values.
8. THE Proof_Report SHALL record Targeted_Checks and any Broader_Suite_Result in separately labeled sections.
9. WHEN Listening_Acceptance is available, THE Proof_Report SHALL label Listening_Acceptance as supplemental to deterministic validation.
10. THE Audio_Proof_Workflow SHALL sanitize every Evidence_Artifact by excluding transcript bodies, prose bodies, account IDs, ARNs, user or role identifiers, access keys, credential values, and nonpermitted identity details.
11. THE Proof_Report SHALL report Per_File_Inventory differences with workflow-owned, pre-existing, unchanged, and concurrent-or-unattributed classifications.
12. THE Proof_Report SHALL state that Publishing_Workstream remains separate and was not implemented by Audio_Proof_Workflow.
13. THE Audio_Proof_Workflow SHALL preserve narration source files, dependency files, Protected_Artifacts, and existing specification files byte-for-byte except for the new Chapter 3 specification created before execution.
