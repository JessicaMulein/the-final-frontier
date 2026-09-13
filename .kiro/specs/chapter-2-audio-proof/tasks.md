# Implementation Plan: Chapter 2 Audio Proof

## Overview

Execute the existing Chapter 2 narration workflow without changing code or prose. Each leaf task produces or verifies an operational artifact under `.audiobook/build/narration/chapter-002-tiffany/`; the single paid task is isolated between preflight and postflight waves. Stop on any failed hard gate—never retry a failed or charge-uncertain model call automatically.

## Tasks

- [ ] 1. Complete nonbillable preflight
  - [ ] 1.1 Inspect and freeze the local execution contract
    - Work from `/Users/jessica/Documents/frontier-book` and create only the ignored Chapter 2 build/evidence directory needed for execution records.
    - Verify the exact Chapter 2 source path and restricted header, normalized Prose Body word count `1137`, model `amazon.nova-2-sonic-v1:0`, region `us-east-1`, Tiffany availability, target segmentation `5`, expected output paths, writable destinations, and sufficient local space.
    - Inventory any existing Chapter 2 artifacts and stop on malformed, conflicting, or charge-uncertain evidence; do not delete, overwrite, reconcile, or render.
    - Record clean pre-execution status/hashes for protected prose/spec/tooling/dependency paths, all `chapter-001-*` build trees, and `voice-samples/chapter-1-*` in `.audiobook/build/narration/chapter-002-tiffany/evidence/preflight-local.json`.
    - _Requirements: 1.1, 1.2, 1.5, 1.7, 7.8, 7.9, 7.10_

  - [ ] 1.2 Run and record the offline Chapter 2 dry-run
    - From `.audiobook/`, run `.venv/bin/python -m frontier_audiobook audition narrate --chapter 2 --voice tiffany --max-words 5 --dry-run` without an AWS profile requirement or paid confirmation.
    - Save the JSON output as `.audiobook/build/narration/chapter-002-tiffany/evidence/preflight-dry-run.json`; verify chapter `2`, voice `tiffany`, zero billable calls, positive planned calls, and the expected source-derived word count.
    - Stop before paid execution if the command or any assertion fails.
    - _Requirements: 1.3, 1.4, 1.7_

  - [ ] 1.3 Verify the external paid boundary and official rates
    - Run a non-model identity call with the exact named profile `AWS_PROFILE=frontier-audiobook` and require successful resolution. The profile is user-approved as a valid static-credential profile and is not SSO; do not inspect or gate on credential type, source, age, expiration, or lifetime because successful resolution is sufficient. Record only `identity_verified: true`, the profile label, and timestamp—never an account ID, ARN, role identifier, access key, credential value, or other returned identity detail.
    - Read the official Amazon Bedrock `us-east-1` offer for model `Nova Sonic 2.0` and record all four on-demand rates, units, source URL, retrieval/effective dates, model, and region in `.audiobook/build/narration/chapter-002-tiffany/evidence/preflight-external.json`.
    - Expect the design snapshot per 1K tokens (`0.003` input speech, `0.00033` input text, `0.012` output speech, `0.00275` output text), but use current official values and stop on a missing/ambiguous modality instead of substituting another source.
    - _Requirements: 1.6, 1.7, 6.1, 6.2, 6.8, 7.7_

- [ ] 2. Execute the explicitly authorized paid render/resume
  - [ ] 2.1 Run the existing Chapter 2 narration command exactly once
    - **Paid hard gate:** starting this task authorizes the command's Bedrock charges after Tasks 1.1–1.3 pass.
    - From `.audiobook/`, run `AWS_PROFILE=frontier-audiobook .venv/bin/python -m frontier_audiobook audition narrate --chapter 2 --voice tiffany --max-words 5 --confirm-paid-render` exactly once and do not add `--accept-verbatim-prefix`.
    - Capture console output under `.audiobook/build/narration/chapter-002-tiffany/evidence/render-console.log` and record final CLI fields plus newly narrated/reused segment IDs in `.audiobook/build/narration/chapter-002-tiffany/evidence/render-result.json` without transcript bodies or identity details.
    - If the command fails, becomes uncertain, reports a partial turn, or reports a fidelity mismatch, preserve evidence and stop. Do not retry, reset, reconcile, copy, or report success.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 3. Validate the completed render and calculate usage
  - [ ] 3.1 Validate Property 1: active manifest set is complete and unambiguous
    - Re-read Chapter_2_Source through existing manuscript rules and validate manifest chapter, voice, exact source path, target size, source/spoken hashes, Chapter_WAV path, active count, unique contiguous IDs, and exclusion of carried-over entries.
    - Write pass/fail facts and hashes, without prose, to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-1-active-set.json`; a failure blocks all later waves.
    - **Property 1: Active manifest set is complete and unambiguous**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.7, 3.8**

  - [ ] 3.2 Validate Property 2: active segment fidelity is exact
    - For every active segment, require `narrated`, exact match, coverage `1.0`, zero mid-sentence partial turns, an in-root audio/transcript/Event_Journal binding, and a matching recorded WAV SHA-256.
    - Use existing replay and transcript-comparison behavior to reconstruct and compare FINAL text and LPCM; do not emit transcript text into evidence.
    - Write aggregate counts and per-segment pass/hash facts to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-2-fidelity.json`.
    - **Property 2: Active segment fidelity is exact**
    - **Validates: Requirements 3.4, 3.5, 3.6, 3.8**

  - [ ] 3.3 Validate Property 3: assembly integrity is preserved
    - Verify Chapter_WAV derives from the ordered active segments and recorded stitching profile using existing narration behavior.
    - Recompute chapter SHA-256 and frame duration; inspect WAV headers for 24 kHz, 16-bit mono; compare all values with manifest precision.
    - Write the path, hash, duration, format, segment count, and pass/fail result to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-3-assembly.json`.
    - **Property 3: Assembly integrity is preserved**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [ ] 3.4 Validate Property 4: reuse is excluded from current execution usage
    - Reconcile `.audiobook/build/narration/chapter-002-tiffany/evidence/render-result.json`, preflight artifact state, active segment hashes, and final CLI counters.
    - Prove every reused segment retained accepted hashes and contributed zero current billable calls/tokens; prove the current-execution set contains exactly newly narrated segments and each new segment caused at most one call.
    - Write rendered/reused IDs and counts, hash-preservation result, and pass/fail status to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-4-reuse.json`.
    - **Property 4: Reuse is excluded from current execution usage**
    - **Validates: Requirements 2.4, 2.5, 2.6, 5.6, 5.7, 5.8**

  - [ ] 3.5 Validate Property 5: journal aggregation is exact
    - Resolve exactly one `events/<active-audio-stem>.jsonl` for every active segment and reject missing, duplicate, malformed, unbound, or inconsistent evidence.
    - Sum only `usageEvent.details.delta` integers for input speech, input text, output speech, and output text; reconcile each journal with terminal modality and top-level totals.
    - Aggregate each active journal once for Active_Artifact_Totals and only newly narrated journals for Current_Execution_Totals; never sum cumulative totals or carried-over records.
    - Write exact per-segment and aggregate integer totals plus reconciliation status to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-5-usage.json`.
    - **Property 5: Journal aggregation is exact**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.9**

  - [ ] 3.6 Validate Property 7 and calculate both pre-tax service costs
    - Re-verify all four current Official_Rates from the official AWS source recorded during preflight and stop if any modality, model, region, unit, or effective rate is ambiguous.
    - With Python `Decimal`, calculate four subtotals and a total for Active_Artifact_Totals, then repeat for Current_Execution_Totals; preserve exact token integers and sufficient decimal precision.
    - Label both values `computed pre-tax service cost`; record Cost Explorer/invoice confirmation separately as `pending`, `not performed`, or a later confirmed amount/date—never infer confirmation from the computation.
    - Write formulas, provenance, rates, tokens, subtotals, totals, and status to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-7-cost.json`.
    - **Property 7: Cost is modality-complete and billing-distinct**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8**

- [ ] 4. Pass the delivery gate and publish the proof copy
  - [ ] 4.1 Evaluate the complete delivery gate and protected-artifact isolation
    - Require passing evidence from Tasks 1.1–3.6 and successful paid CLI completion; do not waive a failed field or estimate missing evidence.
    - Recheck protected tracked paths and preflight hash inventories, including Chapter 1 build/proof artifacts, dependency files, prose, narration source, and the existing novel spec.
    - Write the all-pass gate decision and changed-path list to `.audiobook/build/narration/chapter-002-tiffany/evidence/delivery-gate.json`; any protected change or failed validation stops delivery.
    - _Requirements: 1.7, 3.8, 5.9, 6.8, 7.8, 7.9, 7.10_

  - [ ] 4.2 Validate Property 6 while creating the clearly named proof copy
    - If `voice-samples/chapter-2-tiffany-proof.wav` exists with a different hash, stop without overwrite; if absent, copy the validated Chapter_WAV; if already identical, retain it.
    - Verify Chapter_WAV and Proof_Copy byte counts and SHA-256 hashes are identical, without changing any Chapter 1 proof file.
    - Write source/destination paths, sizes, hashes, action, and pass/fail status to `.audiobook/build/narration/chapter-002-tiffany/evidence/property-6-proof-copy.json`.
    - **Property 6: Proof delivery preserves audio**
    - **Validates: Requirements 4.5, 4.6, 4.7**

  - [ ] 4.3 Create the final proof report from validated evidence
    - Create `.audiobook/build/narration/chapter-002-tiffany/chapter-002-tiffany-proof-report.md` only after Tasks 4.1 and 4.2 pass.
    - Include source/spoken hashes, fixed execution identity, timestamps, manifest/fidelity result, exact/partial-turn counts, duration, segments, billed calls, reuse, both four-modality token scopes, official rates/provenance, formulas/subtotals, both computed pre-tax costs, separate billing-confirmation status, and matching assembled/proof hashes.
    - Omit account IDs, ARNs, role identifiers, access keys, credential values, every other returned identity detail, and transcript bodies. Persist only the fixed profile label, identity-resolution pass/fail value, and timestamp from the non-model identity call. State explicitly that prose, dependencies, narration code, Chapter 1 artifacts, and `.kiro/specs/The-Final-Frontier-novel/` were unchanged.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

- [ ] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Confirm the assembled WAV, clearly named proof copy, manifest validation, exact-fidelity summary, segment/duration/billed/reuse summary, exact journal totals, official-rate cost calculation, and billing-confirmation distinction are present; do not run another render.

## Notes

- No task is optional. Validation is required for delivery.
- This plan executes existing tooling; no task adds a dependency, edits prose, or changes narration code.
- Correctness properties are checked deterministically against one external-service execution. Property-based random testing is intentionally inappropriate here.
- The only billable leaf is Task 2.1. Starting any other task must not invoke Bedrock.
- A failed or uncertain Task 2.1 leaves downstream tasks blocked until the user chooses a separate recovery action.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["2.1"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2", "3.3", "3.4", "3.5"] },
    { "id": 6, "tasks": ["3.6"] },
    { "id": 7, "tasks": ["4.1"] },
    { "id": 8, "tasks": ["4.2"] },
    { "id": 9, "tasks": ["4.3"] }
  ]
}
```
