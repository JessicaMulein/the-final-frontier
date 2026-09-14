# Implementation Plan: Chapter 3 Audio Proof

## Overview

Execute the existing Chapter 3 narration workflow through small, auditable Python/evidence steps. Nonbillable inspection, targeted checks, dry-run planning, fixed-profile identity verification, and current official pricing all precede the only paid leaf. The paid leaf must obtain a fresh, attempt-specific confirmation immediately before launch; opening this plan or starting earlier tasks is not paid authorization.

All implementation and evidence helpers remain under `.audiobook/build/narration/chapter-003-tiffany/`. Do not modify Chapter 3 prose, narration source/dependencies, Chapter 1 or Chapter 2 audio, the Chapter 2 proof spec, the governing novel spec, or publishing front matter/title pages. Stop on any hard-gate failure or charge uncertainty and never retry the paid attempt automatically.

## Tasks

- [ ] 1. Build and complete the nonbillable preflight
  - [ ] 1.1 Implement the Chapter 3 evidence and validation helper
    - Create `.audiobook/build/narration/chapter-003-tiffany/evidence/tools/chapter3_proof.py` with Python-standard-library subcommands for source snapshots, per-file inventories, prior-state classification, dry-run sanitization, paid-attempt wrapping, manifest/replay/WAV/journal/cost validation, collision-safe copying, report generation, and final format checks.
    - Make the paid wrapper spawn a direct child, tee combined stdout/stderr, capture `Popen.wait()` native return code, write log/result in a same-filesystem staging directory, `fsync` files and directory, and atomically rename the complete bundle. Refuse a second attempt ID or any pre-existing staging/ambiguity marker.
    - Keep generated evidence schema-versioned and transcript/prose-free; never persist an environment dump, credentials, or raw identity response. Use only existing dependencies and do not edit `.audiobook/src/` or repository test files.
    - _Requirements: 2.2, 2.3, 2.4, 3.2, 4.3, 4.4, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 10.10_

  - [ ] 1.2 Run targeted nonbillable checks and record broader-suite status separately
    - From `.audiobook/`, run only these existing node IDs: `tests/test_audition.py::test_paid_boundaries_fail_closed`, `tests/test_audition.py::test_event_replay_requires_complete_correlated_output`, `tests/test_narrate.py::test_frontmatter_is_excluded_and_segmentation_preserves_word_order`, `tests/test_narrate.py::test_carried_over_candidate_reclassifies_mismatch_without_render`, `tests/test_narrate.py::test_source_change_stops_before_next_paid_call`, `tests/test_narrate.py::test_source_change_after_last_render_stops_before_stitch`, `tests/test_narrate.py::test_soft_word_target_never_splits_a_sentence_or_paragraph`, and `tests/test_narrate.py::test_safe_turn_preflight_rejects_before_paid_render`.
    - Run the helper's synthetic wrapper checks for native exit `0`, representative nonzero exit, stdout/stderr teeing, interrupted staging, hash inconsistency, and refusal to reuse `paid-attempt-001`; the synthetic commands must not import or invoke AWS.
    - Write node-level and wrapper-check results to `evidence/targeted-checks.json`. Write `evidence/broader-suite-status.json` as `not_run` unless a separately obtained broader result exists; if one exists, record it as non-gating unless a failure maps to a targeted contract.
    - Stop before every later task if a targeted check fails. Do not run the full suite as a hidden delivery gate.
    - _Requirements: 3.1, 3.2, 3.3, 3.8, 3.9, 3.10_

  - [ ] 1.3 Validate Property 1 and capture the local source/isolation baseline
    - Resolve only `The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md`; verify the complete Restricted Header, normalized Prose Body count `1192`, Spoken Token count `1193`, raw-file SHA-256 `ddaff1d45d28b8996845301be56ee91afc22a2f211e0e8bf42bb53384cb74d9f`, Prose Body SHA-256 `a07e7dff0cceea845107eb49958c84092754daa5531ec794ea5325adfe546d45`, Spoken Text SHA-256 `a78247a0639799d40d66a16c5d27bc0c67dd64f42d589c7a72e132e39e59cfa7`, runtime contract, 91 locally planned segments, 10 narration-only-punctuation segments, and exact token conservation.
    - Create `evidence/preflight-local.json` with destination/disk checks, prior Chapter 3 state classification, proof-copy collision state, Git status, write allowlist, and per-file path/size/SHA-256 records. Inventory the full manuscript per file for change attribution, but hard-gate Chapter 3 source separately and never use a whole-novel aggregate as the sole gate.
    - Include per-file baselines for narration code/config/dependencies/relevant tests/tools, `.kiro/specs/chapter-2-audio-proof/`, `.kiro/specs/The-Final-Frontier-novel/`, publishing front-matter/title-page files, every Chapter 1 and Chapter 2 narration build artifact, and every Chapter 1/2 proof-audio file.
    - Write Property 1 evidence to `evidence/property-1-source-plan.json` without source text.
    - **Property 1: Source plan conserves the spoken sequence**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 3.6, 3.7, 6.4**

  - [ ] 1.4 Run and sanitize the exact Chapter 3 dry run
    - From `.audiobook/`, run `.venv/bin/python -m frontier_audiobook audition narrate --chapter 3 --voice tiffany --max-words 5 --dry-run` without `AWS_PROFILE`, `--confirm-paid-render`, or `--accept-verbatim-prefix`.
    - Parse stdout in memory; verify chapter `3`, voice `tiffany`, word count `1193`, planned calls `91`, and billable calls `0` against Property 1 evidence.
    - Write only sanitized fields, segment IDs/counts, and hashes to `evidence/preflight-dry-run.json`; do not persist `first_segments[].text` or raw dry-run output.
    - Stop before external preflight if any assertion fails.
    - _Requirements: 3.3, 3.4, 3.5, 10.10_

  - [ ] 1.5 Verify the named profile and current official four-modality rates
    - With `AWS_PROFILE=frontier-audiobook`, make exactly one non-model identity call. Capture the response in memory, require success as the sole credential condition, discard the raw response, and persist only profile label, `identity_resolved`, and UTC timestamp.
    - Retrieve the current official Amazon Bedrock `us-east-1` offer for Nova Sonic 2.0 on-demand inference. Resolve exactly one USD-per-1K-token rate for input speech, input text, output speech, and output text; record official URL, offer publication/retrieval/effective dates, model, region, purchase option, currency, unit, and exact decimal values.
    - Write the sanitized result to `evidence/preflight-external.json`, explicitly recording zero Bedrock model calls. Treat the Chapter 2 rates as reference values only and stop on any missing or ambiguous current modality.
    - Re-evaluate Requirements 1–4 as the nonbillable gate; do not request paid confirmation in this task.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1_

- [ ] 2. Execute the separately confirmed paid attempt
  - [ ] 2.1 Obtain fresh confirmation, then run `paid-attempt-001` exactly once
    - **Paid hard gate:** immediately before process launch, call `user_input` with reason `general-question` and ask: **Authorize exactly one paid Chapter 3 Tiffany/Nova Sonic 2 invocation (`paid-attempt-001`) now?** Offer `Authorize one paid attempt now` and `Do not authorize`. Specification creation, task selection, and all preflight work are not authorization.
    - If the response is absent, skipped, declined, stale, or does not identify `paid-attempt-001`, stop before launching the child process. On explicit authorization, record only attempt ID, confirmation boolean, exact-command hash, and UTC timestamp in the attempt metadata.
    - Through the tested wrapper, run from `.audiobook/` exactly once with `AWS_PROFILE=frontier-audiobook`: `.venv/bin/python -m frontier_audiobook audition narrate --chapter 3 --voice tiffany --max-words 5 --confirm-paid-render`. Do not add `--accept-verbatim-prefix`.
    - Require the wrapper to commit `evidence/paid-attempt-001/render-console.log` and `attempt.json` atomically with an integer native return code and matching console SHA-256. The CLI may resume only by reusing intact matching Chapter 3 segments within this invocation.
    - If the native return code is nonzero, the wrapper is interrupted, staging remains, evidence is incomplete/inconsistent, fidelity fails, a partial turn occurs, or charge state is uncertain, preserve all evidence and stop. Do not retry, reconcile, reset, copy, or report success under this specification.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 5.15_

- [ ] 3. Validate deterministic postflight properties
  - [ ] 3.1 Validate Property 2: attempt state is definitive or explicitly uncertain
    - Validate prior-state and final-attempt classifications, committed-directory atomicity, exact argv/profile, console hash, integer native return code, termination data, final CLI summary, invocation count `1`, and retry count `0`.
    - Require native return code `0` before continuing; a complete final summary cannot replace this value. Write transcript-free results to `evidence/property-2-attempt-state.json`.
    - **Property 2: Attempt state is definitive or explicitly uncertain**
    - **Validates: Requirements 3.6, 3.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 5.15**

  - [ ] 3.2 Validate Property 3: active manifest set is complete and unambiguous
    - Re-read Chapter 3 through existing manuscript rules and verify manifest chapter, voice, exact source path, source/spoken hashes, word count `1193`, target `5`, segment count `91`, narration-only-punctuation count `10`, Chapter WAV path, and active token conservation.
    - Require unique contiguous IDs `0001`–`0091`, in-root active artifact bindings, and exclusion of every carried-over entry from active counts/totals.
    - Write fixed fields, counts, IDs, hashes, and pass/fail facts—without text—to `evidence/property-3-active-set.json`.
    - **Property 3: Active manifest set is complete and unambiguous**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.8, 6.9**

  - [ ] 3.3 Validate Property 4: active segment fidelity is exact
    - For every Active Segment, require `narrated`, exact match, coverage `1.0`, zero mid-sentence partial turns, matching audio SHA-256, and one transcript/Event Journal binding under the Chapter 3 root.
    - Replay complete correlated events and compare reconstructed FINAL Spoken Tokens and LPCM bytes with accepted artifacts. Keep transcript/prose bodies out of evidence.
    - Write per-segment IDs, hashes, counts, and aggregate pass/fail facts to `evidence/property-4-fidelity.json`.
    - **Property 4: Active segment fidelity is exact**
    - **Validates: Requirements 6.5, 6.6, 6.7, 6.9**

  - [ ] 3.4 Validate Property 5: assembly integrity is preserved
    - Verify the assembled Chapter WAV derives from the exact ordered Active Segment set and recorded stitching profile.
    - Recompute SHA-256 and frame duration; inspect the WAV header for 24,000 Hz, 16-bit, mono, uncompressed PCM; compare duration at manifest precision.
    - Write path, hash, byte count, duration, format, stitching profile, and result to `evidence/property-5-assembly.json`.
    - **Property 5: Assembly integrity is preserved**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

  - [ ] 3.5 Validate Property 6: reuse is excluded from current execution usage
    - Reconcile preflight state, attempt summary, final active IDs, content-addressed hashes, and rendered/reused classifications.
    - Require each reused segment to retain accepted hashes and contribute zero current calls/tokens; require each newly narrated segment to contribute at most one call; require the current journal set to equal exactly newly narrated IDs.
    - Write IDs, counts, hash-preservation facts, and result to `evidence/property-6-reuse.json`.
    - **Property 6: Reuse is excluded from current execution usage**
    - **Validates: Requirements 5.6, 5.7, 8.6, 8.7, 8.8**

  - [ ] 3.6 Validate Property 7: journal aggregation is exact
    - Resolve exactly one `events/<active-audio-stem>.jsonl` per Active Segment and reject missing, duplicate, malformed, unbound, or inconsistent journals.
    - Sum only integer `usageEvent.details.delta` values for input speech, input text, output speech, and output text; reconcile each modality and terminal top-level input/output/total fields.
    - Aggregate each active journal exactly once for Active Artifact Totals and only newly narrated journals for Current Execution Totals. Write per-segment and aggregate integers to `evidence/property-7-usage.json` without event payloads.
    - **Property 7: Journal aggregation is exact**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.9**

  - [ ] 3.7 Validate Property 9: cost is modality-complete and billing-distinct
    - Reverify the four current official rates and provenance recorded in external preflight; block cost if model, region, purchase option, unit, currency, effective data, or any modality is ambiguous.
    - With Python `Decimal`, calculate four exact subtotals and one sum for Active Artifact Totals, then repeat for Current Execution Totals. Never round intermediate values or substitute a third-party rate.
    - Record tokens, rates, provenance, formulas, subtotals, both `computed pre-tax service cost` values, and a separate Cost Explorer/invoice status in `evidence/property-9-cost.json`.
    - **Property 9: Cost is modality-complete and billing-distinct**
    - **Validates: Requirements 4.5, 4.6, 4.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7**

  - [ ] 3.8 Validate Property 10: scoped isolation is per-file and attributable
    - Rebuild the per-file inventory and compare by path/hash with preflight. Require Chapter 3 source, runtime/config/dependencies/tests/tools, Chapter 1/2 audio, protected specs, and publishing files to retain their baselines.
    - Enumerate every workflow-owned write and require allowlist containment. Report changed non-Chapter-3 manuscript paths as pre-existing or concurrent-or-unattributed based on retained evidence; do not call changes unrelated without evidence and do not use aggregate drift alone as the gate.
    - Write exact new/missing/changed/unchanged sets and attribution to `evidence/property-10-isolation.json`.
    - **Property 10: Scoped isolation is per-file and attributable**
    - **Validates: Requirements 2.2, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 10.11, 10.13**

  - [ ] 3.9 Validate Property 11: evidence sanitization follows explicit allowlists
    - Scan every generated Evidence Artifact, including the paid console log, for forbidden identity field names/patterns and source/transcript body leakage; compare persisted identity keys with the exact three-field allowlist.
    - Do not scan required runtime manifest/transcript/Event Journal payloads as if they were sanitized Evidence Artifacts; validate their path confinement and hashes through Properties 3, 4, and 7 instead.
    - Write only categories, paths, counts, and pass/fail facts to `evidence/property-11-sanitization.json`; never echo a detected secret or prohibited body into the result.
    - **Property 11: Evidence sanitization follows explicit allowlists**
    - **Validates: Requirements 4.3, 4.4, 10.10**

- [ ] 4. Pass the delivery gate and publish the proof
  - [ ] 4.1 Evaluate the complete deterministic delivery gate
    - Require passing Tasks 1.1–3.9, a committed Paid Attempt Bundle with native return code `0`, and no waived source, fidelity, replay, journal, rate, cost, isolation, or sanitization field.
    - Record every prerequisite evidence path/hash and exact gate decision in `evidence/delivery-gate.json`. Broader non-overlapping suite failures remain separately reported; Listening Acceptance is not a gate input.
    - Stop before Proof Copy on any failed or missing prerequisite. Do not rerun narration.
    - _Requirements: 1.7, 2.8, 3.3, 3.7, 3.9, 3.10, 4.8, 5.13, 5.14, 5.15, 6.9, 8.9, 9.7, 10.9_

  - [ ] 4.2 Validate Property 8 while creating the collision-safe proof copy
    - If `voice-samples/chapter-3-tiffany-proof.wav` is absent, copy the validated Chapter WAV; if byte-identical, retain it and record `already-identical`; if its hash differs, leave it untouched and stop with collision failure.
    - Verify source/destination byte counts, complete bytes, and SHA-256. Do not modify any Chapter 1 or Chapter 2 proof file.
    - Write paths, prior state, action, sizes, hashes, and result to `evidence/property-8-proof-copy.json`.
    - **Property 8: Proof delivery preserves audio and collision safety**
    - **Validates: Requirements 7.5, 7.6, 7.7, 7.8**

  - [ ] 4.3 Create the sanitized Chapter 3 proof report
    - Generate `.audiobook/build/narration/chapter-003-tiffany/chapter-003-tiffany-proof-report.md` only from validated evidence after Task 4.2 succeeds.
    - Include source/header/count/hash contracts; minimal identity fields; exact paid argv/native return code/log hash; segment/fidelity/replay/assembly/reuse summaries; both four-modality token scopes; current official rate provenance; Decimal formulas/subtotals and both computed pre-tax costs; separate billing confirmation; per-file attribution; targeted and separately labeled broader-suite status; and matching WAV/proof hashes.
    - Record Listening Acceptance as `not performed` unless independently supplied after deterministic checks; if supplied, label it supplemental and never alter the deterministic result.
    - State that Chapter 1/2 audio, Chapter 2 spec, governing novel spec, narration source/dependencies, and publishing files were preserved. State that written/audiobook front matter and title-page implementation is a separate requested Publishing Workstream and was not implemented here.
    - Omit transcript/prose bodies and every forbidden identity detail.
    - _Requirements: 2.12, 3.8, 9.6, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13_

- [ ] 5. Produce the final targeted validation record
  - [ ] 5.1 Recheck final evidence, report structure, and protected hashes without external calls
    - Validate all JSON evidence schemas, required report headings/fields, property-to-requirement references, dependency-complete artifact paths, and matching assembled/proof hashes.
    - Recompute post-report per-file hashes for Chapter 3 source, Chapter 1/2 audio, protected specs, runtime/config/dependencies/tests/tools, and publishing files; require the Property 10 conclusions to remain true after report creation.
    - Re-run Evidence Artifact sanitization against the final report and new delivery files. Record broader suite as `not_run` or its separately supplied diagnostic result; do not run a full suite, AWS call, dry run, model call, narration command, or paid retry in this checkpoint.
    - Write `evidence/final-validation.json` with an all-pass/blocked decision and exact blockers.
    - _Requirements: 2.5, 2.8, 2.9, 2.10, 2.11, 3.8, 3.9, 3.10, 7.8, 10.7, 10.8, 10.10, 10.11, 10.12, 10.13_

- [ ] 6. Final checkpoint - Ensure all targeted checks and deterministic properties pass
  - Ensure the final validation record passes, the proof/report exist only after a successful gate, all 11 correctness properties have evidence, native return code is known and zero, broader-suite status is separate, and no second paid attempt occurred. Ask the user if questions arise; do not run another command that can incur charges.

## Notes

- No task is optional because each check protects a paid or delivery boundary.
- The only paid leaf is Task 2.1. Task 2.1 still requires a fresh interactive Paid Confirmation immediately before launch.
- Tasks 1.1–1.5, 3.1–5.1, and the final checkpoint must not invoke Bedrock Runtime.
- Correctness properties are deterministic checks over local inputs/artifacts; they do not justify repeated external calls or randomized paid tests.
- Full-suite execution is intentionally outside the gate. Any independently available broader failure is reported separately and becomes blocking only when it overlaps a targeted contract.
- A failed, interrupted, nonzero, or Charge Uncertain Paid Attempt has no automatic recovery path in this plan.
- Front matter and title-page implementation for both written and audiobook editions remains a separate already-requested Publishing Workstream; no task here implements it.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["1.5"] },
    { "id": 5, "tasks": ["2.1"] },
    { "id": 6, "tasks": ["3.1", "3.2"] },
    { "id": 7, "tasks": ["3.3", "3.4", "3.5", "3.6"] },
    { "id": 8, "tasks": ["3.7", "3.8"] },
    { "id": 9, "tasks": ["3.9"] },
    { "id": 10, "tasks": ["4.1"] },
    { "id": 11, "tasks": ["4.2"] },
    { "id": 12, "tasks": ["4.3"] },
    { "id": 13, "tasks": ["5.1"] }
  ]
}
```
