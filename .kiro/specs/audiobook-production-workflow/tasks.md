# Implementation Plan: Reusable Audiobook Production Workflow

## Overview

Implement and validate one generic Python production subsystem around the existing `frontier_audiobook` runtime. The plan builds strict configuration, immutable plans, independent transaction ledgers, bounded paid authorization, an atomic direct-child wrapper, reusable track execution, deterministic validation/accounting, collision-safe delivery, status/reporting, and read-only legacy recognition once. Normal chapters then use stable commands and generated data rather than new specs or chapter helper code.

All implementation and automated tests are nonbillable and must run with AWS/model access denied. The only paid leaf is Task 9.3, after Task 9.2 obtains a fresh Chapter 3-specific confirmation. Starting this plan, completing implementation, or finishing Chapter 3 preflight does not authorize paid work.

## Tasks

- [x] 1. Build strict production models, configuration, catalog, and planning
  - [x] 1.1 Implement typed record models and strict codecs
    - Create cohesive generic models for Track kinds, effective configuration, source/segment snapshots, frozen plans, preflight, authorization, ledger events, attempt results, validation evidence, and reports under `audiobook-studio/src/frontier_audiobook/`.
    - Implement strict canonical JSON parsing/serialization with duplicate-key, unknown-field, nonfinite-number, enum, and schema-version rejection; implement deterministic production-TOML parsing/printing and parser-printer round trips.
    - Reuse current no-follow/path/hash/atomic utilities and keep records prose-free where required.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.10, 3.11, 5.3, 15.6_

  - [x] 1.2 Implement `production.toml`, override resolution, and the ordered Track catalog
    - Add one tracked `audiobook-studio/config/production.toml` with current defaults: Tiffany, `amazon.nova-2-sonic-v1:0`, `us-east-1`, `frontier-audiobook`, target `5`, exact fidelity, `frontier-word-sequence-v1`, and 24 kHz/16-bit/mono PCM.
    - Implement deterministic precedence `global defaults < Track-kind override < exact-Track override`, provenance, confined naming templates, unique IDs/sequences, bounded plan size, and exact-fidelity enum validation.
    - Add generic catalog support for opening credits, dedication, epigraph, approved narratable front matter, chapters, and closing credits. Implement the approved-source path/section/hash handoff and `Render_Once` semantics without taking ownership of written-edition layout.
    - Do not insert unapproved special-track prose; use explicit disabled/pending catalog entries until publishing supplies approved text.
    - _Requirements: 1.3, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18_

  - [x] 1.3 Implement generic selectors, source adapters, snapshots, and immutable plan creation
    - Add generic chapter and approved-special-track source adapters that call existing manuscript/spoken/segmentation functions and persist only paths, hashes, counts, segment metadata, configuration provenance, transaction IDs, exact worker argv hashes, and call ceilings.
    - Support repeatable `--chapter`, inclusive bounded `--chapter-range START:END`, and repeatable `--track`; reject empty, reversed, duplicate, unresolved, or oversized scopes.
    - Create plans exclusively and canonically, validate identical explicit plan IDs idempotently, reject collisions, and make zero identity/pricing/model calls.
    - Do not create routine chapter specs or chapter-specific helper modules.
    - _Requirements: 1.2, 1.4, 1.5, 1.8, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.12, 3.13_

  - [x] 1.4 Write the required property test for deterministic configuration and source planning
    - Add deterministic generated tests, at least 100 cases where input variation is useful, for config parse-print-parse, default/override provenance, catalog uniqueness, handoff hash binding, source snapshot derivation, and spoken-token conservation.
    - Tag the test `Feature: audiobook-production-workflow, Property 1: Effective configuration and source planning are deterministic`.
    - **Property 1: Effective configuration and source planning are deterministic**
    - **Validates: Requirements 2.1, 2.3, 2.4, 2.12, 2.13, 2.14, 2.16, 2.17, 3.5, 3.6, 3.7, 17.2**

  - [x] 1.5 Write the required property test for render-once book tracks
    - Generate ordered catalogs with varied chapter/special-track combinations and verify unique IDs/sequences, handoff binding, and one occurrence per render-once opening/front-matter/closing Track.
    - Tag the test `Feature: audiobook-production-workflow, Property 16: Render-once book tracks are catalog-unique`.
    - **Property 16: Render-once book tracks are catalog-unique**
    - **Validates: Requirements 2.14, 2.15, 2.16, 2.17**

- [x] 2. Implement reusable preflight, isolation, rates, estimates, and legacy observation
  - [x] 2.1 Implement local preflight, per-file isolation, reuse/collision classification, and the read-only legacy adapter
    - Build per-file inventories for selected sources, runtime/config/dependencies, prior audio, historical specs, governing novel spec, and selected publishing handoffs; derive the write allowlist and classify unselected manuscript changes separately.
    - Implement local disk/same-filesystem checks, target-check result binding, destination absent/identical/conflicting classification, prior state classification, and maximum-new-call calculation.
    - Add a read-only Chapter 1/2 adapter that observes existing manifests/audio/transcripts/journals/proof paths by path/size/hash, applies current reuse checks, and never moves or rewrites legacy bytes.
    - Preserve `.kiro/specs/chapter-2-audio-proof/`, `.kiro/specs/chapter-3-audio-proof/`, `.kiro/specs/The-Final-Frontier-novel/`, Chapter 1/2 audio, and unselected manuscript work.
    - _Requirements: 1.6, 1.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.12, 4.14, 4.15, 4.16, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 2.2 Implement minimal identity, current official rates, and bounded Decimal estimates
    - Resolve each unique configured profile with one non-model identity call, discard the raw response in memory, and retain exactly profile label, boolean, and timestamp.
    - Parse current official four-modality rates for the configured model/region/purchase option with complete provenance; reject missing, duplicate, ambiguous, stale, wrong-unit, or wrong-currency matches.
    - Calculate per-Track and total maximum calls plus a conservative Decimal estimate from configured finite token envelopes; record every assumption and make zero Bedrock model calls.
    - _Requirements: 4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 4.14, 4.15, 4.16, 15.1, 15.2_

  - [x] 2.3 Write the required property test for immutable bounded plans and preflight
    - Generate valid and tampered plans/preflight records; test selector bounds, canonical round trips, source/config/command mutation, call/estimate bindings, and authorization invalidation with at least 100 deterministic cases.
    - Tag the test `Feature: audiobook-production-workflow, Property 2: Frozen plans and preflight scopes are immutable and bounded`.
    - **Property 2: Frozen plans and preflight scopes are immutable and bounded**
    - **Validates: Requirements 1.8, 3.1, 3.2, 3.3, 3.4, 3.8, 3.9, 3.10, 3.11, 3.12, 4.1, 4.12, 4.13, 4.15, 6.3, 6.4, 6.5, 6.6**

  - [x] 2.4 Write the required property test for scoped per-file isolation
    - Generate protected/unselected trees and instrument writes; verify per-file hard gates, allowlist containment, concurrent-or-unattributed classification, protected spec/audio preservation, and aggregate-drift independence.
    - Tag the test `Feature: audiobook-production-workflow, Property 13: Protected isolation is per-file and attributable`.
    - **Property 13: Protected isolation is per-file and attributable**
    - **Validates: Requirements 1.6, 1.7, 4.4, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10**

  - [x] 2.5 Write the required property test for observational legacy import
    - Generate complete, incomplete, ambiguous, and tampered Chapter 1/2 convention fixtures; verify current reuse acceptance/rejection and full before/after byte identity.
    - Tag the test `Feature: audiobook-production-workflow, Property 15: Legacy import is observational and byte-preserving`.
    - **Property 15: Legacy import is observational and byte-preserving**
    - **Validates: Requirements 13.5, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7**

- [x] 3. Implement independent ledger truth, locks, idempotency, and status reconstruction
  - [x] 3.1 Implement the transaction state reducer, hash-chained event store, locks, and rebuildable status index
    - Add one independent transaction root/event chain per Track, strict allowed transitions, exclusive book/Track locking, monotonic sequence/hash binding, durable writes, and fault isolation.
    - Implement idempotent nonbillable operations and derived plan/batch/book status rebuilding that never treats the global index as authority.
    - Expose internal APIs for state inspection without reading audio bytes unless validation requests hashes.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 12.7, 12.8, 12.9_

  - [x] 3.2 Write the required property test for independently reconstructable transaction truth
    - Use model-based state sequences, concurrent writers, interruption points, corrupt events, corrupt/missing indexes, and repeated operations; execute at least 100 deterministic sequences and report the seed.
    - Tag the test `Feature: audiobook-production-workflow, Property 3: Transaction truth is independently reconstructable`.
    - **Property 3: Transaction truth is independently reconstructable**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12**

- [x] 4. Implement exact authorization and atomic paid-attempt capture
  - [x] 4.1 Implement one-shot single/batch authorization creation and validation
    - Bind exact plan/preflight digests, ordered transaction/Track/command hashes, call ceilings, estimate inputs, operator-approved maximum estimated pre-tax amount, issue/expiry times, and one-shot status in canonical authorization artifacts.
    - Require explicit displayed confirmation; reject insufficient maximum, stale/mismatched/consumed scope, unlisted calls, retries, and old authorization after a batch stop.
    - Ensure no spec, task state, or generic approval can satisfy the authorization API.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13_

  - [x] 4.2 Implement the generic atomic direct-child attempt wrapper
    - Create same-filesystem staging, durably consume authorization, launch exact argv directly with `Popen`, stream sanitized combined output, capture `Popen.wait()` integer status, and write the complete required result.
    - Flush/fsync log/result/staging, atomically rename, fsync the parent, refuse duplicate/staging/ambiguous attempts, classify incomplete launched evidence as Charge_Uncertain, and block known nonzero status without retry.
    - Pass the configured profile selection to the child while excluding environment/credentials, identity details, and prose/transcript bodies from evidence.
    - Add a hidden generic worker entry point rather than shell pipelines or chapter-specific wrappers.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11_

  - [x] 4.3 Write the required property test for exact finite one-shot authorization
    - Generate scope permutations, additions/removals, command mutations, call-bound changes, Decimal boundaries, expiration boundaries, and repeated consumption; assert zero launches for every invalid case.
    - Tag the test `Feature: audiobook-production-workflow, Property 4: Authorization is exact, finite, current, and one-shot`.
    - **Property 4: Authorization is exact, finite, current, and one-shot**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.10, 6.11, 6.12, 6.13**

  - [x] 4.4 Write the required property test for definitive-or-uncertain paid attempts
    - Use synthetic direct children for exit `0`, varied nonzero statuses, signals, stdout/stderr, interruption before/after launch, missing files, inconsistent hashes, stale staging, and duplicate IDs; never import or call AWS.
    - Tag the test `Feature: audiobook-production-workflow, Property 5: Paid attempt state is definitive or explicitly uncertain`.
    - **Property 5: Paid attempt state is definitive or explicitly uncertain**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10**

- [x] 5. Implement generic Track execution, bounded batches, reuse, and manual recovery
  - [x] 5.1 Refactor existing chapter narration behind a generic Track worker
    - Introduce a Track-source interface used by chapters and approved Special_Tracks while reusing existing safe segmentation, `render_text`, transcript verification, event replay, source-drift checks, content-addressed paths, and assembly.
    - Revalidate source/config/runtime/authorization/call bounds before each model call and source before assembly; allow at most one call per nonreusable segment; persist runtime progress atomically.
    - Preserve existing `audition narrate` behavior and do not duplicate model/verification algorithms.
    - _Requirements: 1.2, 1.9, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4_

  - [x] 5.2 Implement the sequential fail-fast batch coordinator
    - Start transactions in frozen catalog order, one paid Track at a time by default; retain completed-prefix states and leave the unstarted suffix at zero calls after the first blocking result.
    - Derive aggregate status from transaction truth and require fresh preflight/authorization before any post-stop continuation.
    - _Requirements: 6.13, 8.1, 8.2, 8.3, 8.7, 8.8, 8.9_

  - [x] 5.3 Implement nonbillable resume inspection and manual resolution
    - Validate ledger/attempt/authorization/source/config/runtime evidence and return only enumerated resume classifications.
    - Support accept-complete-local-artifacts, quarantine-invalid-artifacts, and abandon-uncertain-attempt without identity, pricing, child, or model calls.
    - Require a new transaction/plan/preflight/authorization and exact duplicate-charge acknowledgement for any possible later paid attempt.
    - _Requirements: 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11_

  - [x] 5.4 Write the required property test for fail-fast independent batches
    - Generate batches and inject each failure type at every position; verify sequential plan order, unique evidence, completed prefix, failed Track evidence, unstarted suffix, zero later calls, and aggregate state.
    - Tag the test `Feature: audiobook-production-workflow, Property 6: Batch execution is fail-fast with independent transactions`.
    - **Property 6: Batch execution is fail-fast with independent transactions**
    - **Validates: Requirements 6.13, 8.1, 8.2, 8.3, 8.7, 8.8, 8.9**

  - [x] 5.5 Write the required property test for reuse and resume call safety
    - Generate reusable/nonreusable partitions plus artifact/config/event mutations; verify zero calls/tokens for reuse, one-call maximum for nonreuse, revalidation points, offline recovery, and new-transaction requirements.
    - Tag the test `Feature: audiobook-production-workflow, Property 7: Reuse and resume never create unapproved calls`.
    - **Property 7: Reuse and resume never create unapproved calls**
    - **Validates: Requirements 4.5, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11**

- [x] 6. Implement deterministic postflight validation and exact accounting
  - [x] 6.1 Implement frozen-plan and active-manifest validation
    - Require a committed native-zero attempt, validate every manifest field against Track_Plan, enforce active count/unique contiguous IDs/token conservation/path confinement, and exclude historical/rejected/carried records.
    - Produce sanitized validation evidence and block Delivery_Gate on every missing, malformed, ambiguous, or mismatched input.
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.9, 10.12_

  - [x] 6.2 Implement exact transcript, event, LPCM, hash, and partial-turn validation
    - Reuse current normalized comparison and complete correlated replay; require exact transcript equality, coverage `1.0`, zero mid-sentence partial turns, matching segment hashes, and reconstructed LPCM equality.
    - Keep transcript/event bodies in private runtime roots and emit only hashes/counts/results.
    - _Requirements: 10.6, 10.7, 10.8, 10.12_

  - [x] 6.3 Implement assembly and WAV integrity validation
    - Verify exact active order and stitching profile, current source hash before assembly, configured uncompressed PCM fields, byte count, SHA-256, and frame-derived duration.
    - _Requirements: 10.10, 10.11, 10.12_

  - [x] 6.4 Implement journal aggregation and two-scope Decimal cost calculation
    - Resolve exactly one journal per active audio stem, sum integer modality deltas only, reconcile terminal modality/combined totals, and calculate Active_Artifact_Totals plus Current_Execution_Totals without double counting.
    - Apply current official four-modality rates with exact Decimal formulas; preserve all provenance; separate estimate, exact service cost, billing confirmation, and budget-exception status.
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12, 11.13, 11.14_

  - [x] 6.5 Write the required property test for complete active manifests
    - Generate valid and malformed active sets with field mutation, gaps, duplicates, reorderings, token loss/addition, and historical records.
    - Tag the test `Feature: audiobook-production-workflow, Property 8: Active manifests are complete and unambiguous`.
    - **Property 8: Active manifests are complete and unambiguous**
    - **Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.9**

  - [x] 6.6 Write the required property test for exact transcript and LPCM replay
    - Generate/tamper transcript tokens, correlated event sequences, audio blocks, hashes, coverage, and partial-turn counts; require every predicate and Delivery_Gate blocking.
    - Tag the test `Feature: audiobook-production-workflow, Property 9: Exact transcript and LPCM replay are preserved`.
    - **Property 9: Exact transcript and LPCM replay are preserved**
    - **Validates: Requirements 10.6, 10.7, 10.8, 10.12**

  - [x] 6.7 Write the required property test for assembly integrity
    - Generate segment PCM/order/stitch-profile and WAV metadata variations; verify exact bytes, format, hash, and frame duration.
    - Tag the test `Feature: audiobook-production-workflow, Property 10: Assembly integrity is preserved`.
    - **Property 10: Assembly integrity is preserved**
    - **Validates: Requirements 10.10, 10.11, 10.12**

  - [x] 6.8 Write the required property test for modality-complete journals and cost
    - Generate four-modality deltas/totals, reused/new partitions, Decimal rates, missing/duplicate/tampered journals, incomplete provenance, and budget boundaries with at least 100 deterministic cases.
    - Tag the test `Feature: audiobook-production-workflow, Property 11: Journal aggregation and exact cost are modality-complete`.
    - **Property 11: Journal aggregation and exact cost are modality-complete**
    - **Validates: Requirements 4.10, 4.11, 4.13, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12, 11.13, 11.14**

- [x] 7. Implement delivery, reports, and evidence privacy
  - [x] 7.1 Implement collision-safe delivery and track/batch reports
    - Publish absent destinations via verified temporary copy and atomic rename, retain identical destinations, and preserve/block different destinations.
    - Generate sanitized Track_Report and Batch_Report with complete digest, state, validation, usage, estimate/exact cost, billing, isolation, test, collision, and optional supplemental-listening sections.
    - Make deliver/report operations idempotent and nonbillable.
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.10, 12.11_

  - [x] 7.2 Implement explicit evidence allowlists, sanitization scans, and path trust boundaries
    - Enforce the three-field identity projection, body/event/environment/credential exclusions, private runtime confinement, strict input schemas, no-follow path containment, and value-safe finding reports.
    - Preserve failed/uncertain evidence immutably and scan plans, preflight, authorization, ledgers, attempt logs/results, validation, indexes, and reports before successful gates.
    - _Requirements: 3.9, 4.9, 7.11, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9_

  - [x] 7.3 Write the required property test for collision-safe idempotent delivery
    - Generate arbitrary source/destination bytes for absent, identical, and conflicting states; verify full byte/hash identity, conflict preservation, atomicity, repeated-result equality, and zero model calls.
    - Tag the test `Feature: audiobook-production-workflow, Property 12: Delivery is collision-safe and idempotent`.
    - **Property 12: Delivery is collision-safe and idempotent**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.10**

  - [x] 7.4 Write the required property test for evidence and identity allowlists
    - Generate arbitrary identity/environment/source/transcript/event/credential values, unsafe paths, and prior failed evidence; verify exact allowed fields, confinement, non-echoing findings, and immutable history.
    - Tag the test `Feature: audiobook-production-workflow, Property 14: Evidence and identity persistence obey explicit allowlists`.
    - **Property 14: Evidence and identity persistence obey explicit allowlists**
    - **Validates: Requirements 3.9, 4.9, 7.4, 7.5, 7.11, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9**

- [x] 8. Wire the stable CLI, complete affected quality gates, and document routine operation
  - [x] 8.1 Wire all stable `production` commands and nonbillable integration flows
    - Add `plan`, `preflight`, `authorize`, `execute`, `validate`, `deliver`, `report`, `status`, `inspect-resume`, and `resolve` handlers to `cli.py`, retaining existing `audition` behavior and exit-code conventions.
    - Add installed-wheel CLI tests for single chapter, range, special tracks, dry/nonbillable flows, status reconstruction, invalid authorization, and synthetic direct-child execution; no AWS/model calls.
    - Verify routine outputs use generic roots/schema and no chapter-specific spec/helper generation occurs.
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.9, 3.1, 3.2, 3.3, 3.13, 12.8, 12.9, 12.10_

  - [x] 8.2 Assemble and run the targeted affected test gate with broader-suite classification
    - Tag and collect all affected config/plan/ledger/auth/attempt/batch/reuse/validation/cost/delivery/isolation/sanitization/legacy/special-track tests; deny Python network and AWS adapters.
    - Ensure applicable property tests run at least 100 deterministic cases with seed reporting.
    - Implement separate broader-suite result reporting and overlap classification. Run only the targeted gate for implementation acceptance unless the broader suite is separately requested.
    - _Requirements: 4.2, 4.3, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [x] 8.3 Document the reusable operator workflow and enforce dependency/protected-path constraints
    - Update `audiobook-studio/README.md` with config/track handoff, all stable commands, single/batch examples, authorization boundaries, state machine, failure/manual-resolution semantics, cost labels, privacy, and Chapter 3 pilot instructions.
    - Confirm `pyproject.toml`, lockfile, and requirements add no dependency. If a future dependency is proposed, require a separate exact-version review rather than adding it in this task.
    - Add structural checks that historical Chapter 2/3 specs, the governing novel spec, and Chapter 1/2 artifacts remain unchanged; state that future normal tracks use this reusable workflow.
    - _Requirements: 1.1, 1.6, 1.7, 16.8, 16.9, 16.10_

- [ ] 9. Run the final separately authorized Chapter 3 acceptance phase
  - [x] 9.1 Complete the Chapter 3 pilot plan and nonbillable preflight
    - After Tasks 1–8 pass, create one new production plan selecting only `The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md` and recompute all source/hash/count/segment/call facts from current bytes.
    - Run the targeted gate, protected inventory, reuse/collision/capacity checks, one minimal identity resolution, current official four-modality rates, and bounded estimate. Make zero model calls and do not copy values from the historical Chapter 3 spec.
    - Present plan/preflight digests, exact Track/command, call ceiling, estimate, proposed approved maximum, expiration, and blockers. Stop if any gate fails.
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.12_

  - [x] 9.2 Obtain a fresh Chapter 3-specific paid confirmation and create one authorization
    - Immediately before authorization, use `user_input` with reason `general-question` and ask: **Authorize exactly one paid Chapter 3 production pilot transaction under the displayed plan/preflight digests, call ceiling, expiration, and approved maximum estimated pre-tax amount now?**
    - Offer `Authorize this one Chapter 3 pilot attempt` and `Do not authorize`. A skipped, declined, stale, generic, or mismatched response stops before authorization/execute.
    - Create one one-shot Paid_Authorization only after exact confirmation; this task itself makes no model call.
    - _Requirements: 6.8, 6.9, 17.4, 17.5, 17.6, 17.7_

  - [x] 9.3 Execute exactly one paid Chapter 3 pilot transaction
    - Through `production execute`, run only the authorized Chapter 3 Track_Transaction and atomic wrapper with the exact configured profile/voice/model/region/segment target/fidelity policy.
    - If status is nonzero, evidence is uncertain, source/runtime drifts, a call bound is reached, or fidelity/partial-turn checks fail, retain evidence and stop without retry, delivery, reset, or a second authorization.
    - _Requirements: 17.8, 17.9_

  - [~] 9.4 Validate, deliver, report, and accept the reusable workflow after a successful pilot
    - Only after native status `0`, run deterministic manifest/fidelity/replay/assembly/usage/cost/isolation/sanitization validation, collision-safe delivery, Track_Report, Batch_Report, and final protected-file comparison.
    - Mark the reusable workflow accepted for future normal Tracks only if every Delivery_Gate input passes. Keep exact service cost separate from billing confirmation and listening feedback supplemental.
    - _Requirements: 17.10, 17.11_

- [~] 10. Final checkpoint - Ensure reusable implementation and pilot evidence are complete
  - Ensure all targeted tests and 16 property tests pass, broader-suite status is separate, all stable CLI operations are documented, dependency/protected-path checks pass, and Chapter 3 has either no paid attempt or exactly one definitively evidenced attempt. Ask the user if questions arise; do not start another paid call.

## Notes

- No task is optional because the tests and validators protect authorization, paid execution, or delivery boundaries.
- Tasks 1–8 implement and test the reusable system once. They must make no AWS identity, pricing, or model calls; tests use local fixtures/mocks with network denied.
- Task 9.1 may perform only future non-model identity/rate preflight after implementation. It is not executed during spec creation.
- Task 9.2 is the distinct interactive paid gate. Task 9.3 is the only paid leaf and permits exactly one Chapter 3 attempt.
- A failed, nonzero, interrupted, or Charge_Uncertain attempt has no automatic recovery or retry path.
- Normal post-pilot chapters use commands and generated plan/transaction data. They do not create new specs, task plans, or chapter helper code.
- Chapter 2/3 specs and the governing novel spec remain historical/protected. Existing Chapter 1/2 artifacts are read-only.
- Property tests are local executable specifications. They never repeat paid or external-service operations.
- The implementation uses Python 3.12, current pinned dependencies, pytest, and standard-library generators; no new dependency is planned.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4", "1.5"] },
    { "id": 4, "tasks": ["2.1", "3.1"] },
    { "id": 5, "tasks": ["2.2"] },
    { "id": 6, "tasks": ["2.3", "2.4", "2.5", "3.2"] },
    { "id": 7, "tasks": ["4.1"] },
    { "id": 8, "tasks": ["4.2"] },
    { "id": 9, "tasks": ["4.3", "4.4"] },
    { "id": 10, "tasks": ["5.1"] },
    { "id": 11, "tasks": ["5.2", "5.3"] },
    { "id": 12, "tasks": ["5.4", "5.5"] },
    { "id": 13, "tasks": ["6.1", "6.4"] },
    { "id": 14, "tasks": ["6.2"] },
    { "id": 15, "tasks": ["6.3"] },
    { "id": 16, "tasks": ["6.5", "6.6", "6.7", "6.8"] },
    { "id": 17, "tasks": ["7.1", "7.2"] },
    { "id": 18, "tasks": ["7.3", "7.4"] },
    { "id": 19, "tasks": ["8.1"] },
    { "id": 20, "tasks": ["8.2", "8.3"] },
    { "id": 21, "tasks": ["9.1"] },
    { "id": 22, "tasks": ["9.2"] },
    { "id": 23, "tasks": ["9.3"] },
    { "id": 24, "tasks": ["9.4"] }
  ]
}
```
