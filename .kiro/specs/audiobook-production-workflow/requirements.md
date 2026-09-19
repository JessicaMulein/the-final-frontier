# Requirements Document

## Introduction

This document derives requirements from the reusable audiobook production design. The feature replaces routine per-chapter operational specifications with one tracked production subsystem and one tracked book configuration. Future normal chapter and book-track execution will use immutable generated plans, independent per-track transactions, explicit paid authorization, deterministic validation, and reusable command operations.

The historical Chapter 2 and Chapter 3 audio-proof specifications remain unchanged as pilot inputs. The governing novel specification remains unchanged. Creating this specification authorizes no tests, AWS access, narration, delivery, or paid execution.

## Glossary

- **Production_Workflow**: The complete reusable planning, preflight, authorization, execution, validation, delivery, reporting, status, and recovery system for audiobook tracks.
- **Generic_Production_Subsystem**: The single tracked Python implementation added to `frontier_audiobook` for all normal production tracks.
- **Production_CLI**: The stable `frontier-audiobook production ...` command group.
- **Book_Production_Config**: The single tracked strict TOML configuration containing book defaults, override layers, catalog entries, roots, bounds, and naming policy.
- **Config_Parser**: The strict TOML parser for Book_Production_Config.
- **Config_Printer**: The deterministic formatter that emits a parsed Book_Production_Config as valid canonical TOML for review and round-trip testing.
- **Config_Resolver**: The component that resolves global defaults, track-kind overrides, and exact-track overrides.
- **Strict_Record_Codec**: The strict canonical JSON parser and serializer used for plans, preflight, authorization, ledger, attempt, validation, and status records.
- **Track_Catalog**: The unique ordered collection of chapter and special audiobook tracks for the book.
- **Track**: One independently planned, authorized, rendered, validated, delivered, and reported audiobook unit.
- **Chapter_Track**: A Track sourced from exactly one restricted-header manuscript chapter.
- **Special_Track**: A render-once opening-credit, dedication, epigraph, approved narratable front-matter, or closing-credit Track.
- **Publishing_Handoff**: The approved written-workflow source path, section, and optional approved hash consumed by a Special_Track.
- **Effective_Track_Config**: The fully resolved voice, model, region, profile label, segmentation target, fidelity policy, normalization, audio format, and output naming for one Track.
- **Selector**: A single chapter, bounded inclusive chapter range, or configured Track ID supplied to planning.
- **Source_Snapshot**: A prose-free record of source path, source hashes, counts, and ordered segment hashes/counts computed from a Track source.
- **Frozen_Plan**: The immutable canonical plan containing the exact finite ordered Track scope and one Track_Plan per Track.
- **Track_Plan**: The source snapshot, effective configuration, exact command hash, transaction ID, protected-inventory binding, and maximum new calls for one Track.
- **Preflight**: Nonbillable checks over a Frozen_Plan, local artifacts, identity resolution, current official rates, and bounded cost/call estimates.
- **Preflight_Record**: The immutable canonical output of Preflight.
- **Targeted_Checks**: Automated affected tests that gate authorization and make no AWS/model call.
- **Broader_Suite_Result**: A separately reported result from tests outside Targeted_Checks.
- **Protected_Inventory**: Per-file path, kind, existence, byte count, SHA-256, Git status, and attribution evidence for protected inputs and artifacts.
- **Protected_Artifact**: An active source, production runtime/configuration/dependency, prior audio artifact, historical pilot spec, governing novel spec, or selected publishing handoff protected during execution.
- **Workflow_Write_Allowlist**: The generated plan/transaction/index roots and approved delivery destinations that Production_Workflow may write during normal execution.
- **Concurrent_Manuscript_Change**: A changed unselected manuscript path without Production_Workflow ownership evidence.
- **Reuse_Inspector**: The read-only component that validates content-addressed current or legacy artifacts before reuse.
- **Identity_Evidence**: Exactly the fixed profile label, identity-resolution boolean, and UTC timestamp retained from a non-model identity call.
- **Official_Rate**: A current official four-modality Nova on-demand rate with complete provenance for the configured model and region.
- **Cost_Estimate**: The preflight Decimal estimate calculated from bounded call/token envelopes and Official_Rates.
- **Paid_Authorization**: The one-shot, expiring, SHA-256-bound operator authorization for one exact Track or one exact bounded Frozen_Plan.
- **Batch_Coordinator**: The component that executes exact authorized Track_Transactions sequentially by default and stops on the first blocking result.
- **Track_Transaction**: The independent directory and state history for one Track_Plan execution.
- **Transaction_Ledger**: The append-only, canonical, hash-chained event sequence inside one Track_Transaction.
- **Derived_Status_Index**: A rebuildable book/batch status cache derived from independent Transaction_Ledgers.
- **Transaction_State**: One of `discovered`, `planned`, `preflight-passed`, `authorization-required`, `running`, `charge-uncertain`, `rendered`, `validated`, `delivered`, or `blocked`.
- **Paid_Attempt_Wrapper**: The generic parent process that stages, launches, captures, synchronizes, and atomically commits one direct-child paid attempt.
- **Direct_Child_Worker**: The generic child process that invokes existing source, segmentation, Nova, verification, and assembly functions for one Track.
- **Paid_Attempt_Bundle**: The atomically committed attempt directory containing a sanitized console log and result with native child status.
- **Charge_Uncertain**: A launched attempt lacking complete, committed, hash-consistent evidence with an integer native return code.
- **Reused_Segment**: An active segment accepted from validated matching artifacts without a model call in the current attempt.
- **Resume_Inspector**: The read-only nonbillable operation that classifies a Track_Transaction and available local recovery paths.
- **Manual_Resolver**: The nonbillable operation that accepts complete local artifacts, quarantines invalid artifacts, or abandons an uncertain attempt without starting a model call.
- **Runtime_Manifest**: The generated manifest binding a Track source, active segments, runtime artifacts, assembly, and configuration.
- **Active_Segment**: A Runtime_Manifest segment used in the assembled Track WAV.
- **Exact_Fidelity**: Exact normalized expected/FINAL transcript equality, complete event replay to accepted transcript and LPCM, and zero mid-sentence partial turns.
- **Event_Journal**: The Nova output-event JSONL file bound to one Active_Segment.
- **Postflight_Validator**: The deterministic validator for source, attempt, manifest, fidelity, replay, assembly, usage, cost, isolation, and sanitization.
- **Active_Artifact_Totals**: Four-modality tokens from exactly one validated Event_Journal per Active_Segment, including Reused_Segments.
- **Current_Execution_Totals**: Four-modality tokens from only segments newly rendered in the current paid attempt.
- **Cost_Calculator**: The Decimal component that applies Official_Rates to token totals.
- **Computed_Pre_Tax_Service_Cost**: Exact journal-derived service cost before tax, credits, discounts, invoice rounding, or account adjustments.
- **Billing_Confirmation**: A separately obtained Cost Explorer or invoice amount and confirmation date.
- **Delivery_Gate**: The all-pass condition required before collision-safe publication of a Track WAV.
- **Proof_Deliverer**: The collision-safe, idempotent publisher for validated Track WAVs.
- **Track_Report**: The sanitized evidence report for one Track_Transaction.
- **Batch_Report**: The derived aggregate status/report for one Frozen_Plan.
- **Legacy_Adapter**: The read-only recognizer for existing Chapter 1 and Chapter 2 output conventions.
- **Legacy_Artifact**: An existing Chapter 1 or Chapter 2 manifest, segment, transcript, Event_Journal, assembled WAV, proof copy, or related record.
- **Evidence_Artifact**: A generated plan, preflight, authorization, ledger payload, attempt console/result, validation record, index, Track_Report, or Batch_Report; required private runtime transcripts and raw Event_Journals are excluded from this term.
- **Render_Once**: A catalog policy under which a Special_Track is represented once for the book rather than repeated per chapter.
- **Chapter_3_Pilot**: The first single-track acceptance run for `discovery-part-003-the-failed-check.md` after implementation.

## Requirements

### Requirement 1: Establish one reusable production authority

**User Story:** As the audiobook producer, I want one reusable production authority, so that normal chapters do not require new operational specs or helper code.

#### Acceptance Criteria

1. THE Production_Workflow SHALL govern future normal audiobook Track execution after Chapter_3_Pilot acceptance.
2. THE Generic_Production_Subsystem SHALL provide one tracked implementation for Chapter_Tracks and Special_Tracks.
3. THE Book_Production_Config SHALL provide one tracked configuration for book-wide production behavior.
4. THE Production_Workflow SHALL generate per-run plans, transactions, manifests, WAVs, evidence, and reports without routine chapter-specific specifications.
5. THE Generic_Production_Subsystem SHALL operate without routine `chapterN_proof.py` or equivalent chapter-specific helper files.
6. THE Production_Workflow SHALL retain `.kiro/specs/chapter-2-audio-proof/` and `.kiro/specs/chapter-3-audio-proof/` as unchanged historical pilot inputs.
7. THE Production_Workflow SHALL retain `.kiro/specs/The-Final-Frontier-novel/` unchanged.
8. THE Frozen_Plan SHALL contain computed chapter-specific source hashes, counts, segments, and call bounds rather than the master specification containing those values.
9. THE Production_CLI SHALL preserve existing `frontier-audiobook audition ...` behavior.

### Requirement 2: Parse, resolve, and format the book production configuration

**User Story:** As the audiobook producer, I want strict defaults and overrides in one configuration, so that every Track receives an explicit reproducible runtime contract.

#### Acceptance Criteria

1. WHEN Config_Parser receives valid Book_Production_Config TOML, THE Config_Parser SHALL produce a typed configuration object.
2. IF Book_Production_Config contains malformed UTF-8, malformed TOML, duplicate logical entries, unknown keys, unknown enum values, unsafe paths, or invalid numeric bounds, THEN THE Config_Parser SHALL return a descriptive input error.
3. WHEN Config_Printer formats a typed Book_Production_Config, THE Config_Printer SHALL emit valid deterministic TOML containing every supported value.
4. WHEN Config_Parser reparses Config_Printer output, THE Config_Parser SHALL produce a configuration equivalent to the original typed Book_Production_Config.
5. THE Book_Production_Config SHALL default voice to `tiffany`.
6. THE Book_Production_Config SHALL default model to `amazon.nova-2-sonic-v1:0`.
7. THE Book_Production_Config SHALL default region to `us-east-1`.
8. THE Book_Production_Config SHALL default profile label to `frontier-audiobook`.
9. THE Book_Production_Config SHALL default target segment size to `5`.
10. THE Book_Production_Config SHALL default fidelity policy to `exact` with normalization `frontier-word-sequence-v1`.
11. THE Book_Production_Config SHALL default audio output to 24,000 Hz, 16-bit, mono PCM.
12. WHEN Config_Resolver resolves one Track, THE Config_Resolver SHALL apply global defaults, then Track-kind overrides, then exact-Track overrides.
13. WHEN Config_Resolver resolves one Track twice from identical input, THE Config_Resolver SHALL produce identical Effective_Track_Config values and provenance.
14. THE Track_Catalog SHALL assign each Track a unique ID, unique sequence position, source declaration, Track kind, and output path.
15. THE Track_Catalog SHALL represent opening credits, approved narratable dedication/epigraph/front matter, Chapter_Tracks, and closing credits as independent Tracks.
16. WHERE a Special_Track is configured, THE Track_Catalog SHALL set Render_Once for the Special_Track.
17. WHERE Publishing_Handoff includes an approved source hash, THE Config_Resolver SHALL require the current handoff source to match the approved hash.
18. THE Production_Workflow SHALL keep written-edition title, copyright, layout, typography, and pagination outside Book_Production_Config ownership.

### Requirement 3: Create immutable, bounded, prose-free production plans

**User Story:** As the proof operator, I want exact finite plans before external work, so that authorization cannot drift to different chapters, commands, or calls.

#### Acceptance Criteria

1. WHEN Production_CLI receives one chapter Selector, THE Production_CLI SHALL create a Frozen_Plan containing exactly that Chapter_Track.
2. WHEN Production_CLI receives a valid inclusive chapter-range Selector, THE Production_CLI SHALL create a Frozen_Plan containing the unique ordered Chapter_Tracks in that range.
3. WHEN Production_CLI receives configured Track-ID Selectors, THE Production_CLI SHALL create a Frozen_Plan containing the unique ordered selected Tracks.
4. IF Selectors are empty, reversed, duplicated, unresolved, or exceed the configured maximum Tracks per plan, THEN THE Production_CLI SHALL reject planning before a plan write.
5. WHEN planning reads a Track source, THE Production_Workflow SHALL compute a Source_Snapshot containing source paths, hashes, counts, and ordered segment hashes/counts.
6. WHEN planning segments Spoken_Text, THE Production_Workflow SHALL verify that ordered segment tokens reproduce the complete normalized Spoken_Text token sequence.
7. WHEN planning resolves a Track, THE Production_Workflow SHALL record Effective_Track_Config and resolution provenance in Track_Plan.
8. WHEN planning resolves a Track, THE Production_Workflow SHALL record exact Direct_Child_Worker argv hash and maximum new calls in Track_Plan.
9. THE Frozen_Plan SHALL contain no prose body, segment text, transcript body, raw Event_Journal payload, credential, or identity response.
10. WHEN Strict_Record_Codec serializes Frozen_Plan, THE Strict_Record_Codec SHALL produce canonical UTF-8 JSON with sorted keys, compact separators, finite values, and a reproducible SHA-256.
11. WHEN Strict_Record_Codec reparses serialized Frozen_Plan, THE Strict_Record_Codec SHALL produce a value equivalent to the original Frozen_Plan.
12. IF an existing plan ID contains bytes different from the newly computed canonical Frozen_Plan, THEN THE Production_Workflow SHALL reject replacement of the existing plan.
13. THE Production_Workflow SHALL create Frozen_Plan without an AWS, pricing, identity, or model call.

### Requirement 4: Complete bounded nonbillable preflight

**User Story:** As the paying operator, I want a complete bounded preflight for selected Tracks, so that paid scope, reusable work, collisions, rates, and estimated exposure are known before authorization.

#### Acceptance Criteria

1. WHEN Preflight begins, THE Production_Workflow SHALL revalidate Frozen_Plan, Book_Production_Config, every selected source, and every command hash.
2. WHEN Preflight runs, THE Targeted_Checks SHALL execute with AWS/model access disabled.
3. IF a Targeted_Check fails, THEN THE Production_Workflow SHALL block Paid_Authorization.
4. WHEN Preflight inventories files, THE Production_Workflow SHALL create Protected_Inventory for selected sources, runtime/configuration/dependencies, prior audio, historical specs, governing novel spec, and selected Publishing_Handoffs.
5. WHEN Preflight evaluates prior artifacts, THE Reuse_Inspector SHALL classify each candidate as reusable, rejected, absent, or Charge_Uncertain.
6. WHEN Preflight evaluates delivery paths, THE Production_Workflow SHALL classify each destination as absent, already-identical, or conflicting.
7. WHEN Preflight evaluates local capacity, THE Production_Workflow SHALL verify required disk space and same-filesystem atomic-rename support.
8. WHEN Preflight evaluates a unique profile label, THE Production_Workflow SHALL perform one non-model identity-resolution call for the profile label.
9. WHEN identity resolution succeeds, THE Production_Workflow SHALL persist Identity_Evidence only.
10. WHEN Preflight retrieves pricing, THE Production_Workflow SHALL resolve one current Official_Rate for input speech, input text, output speech, and output text for the configured model, region, and purchase option.
11. WHEN Preflight records Official_Rates, THE Production_Workflow SHALL record source URL, offer publication date, retrieval date, effective date, model, region, purchase option, currency, unit, and exact decimal rates.
12. WHEN Preflight evaluates reusable segments, THE Production_Workflow SHALL compute maximum new calls per Track and for the complete Frozen_Plan.
13. WHEN Preflight has finite configured token envelopes and Official_Rates, THE Production_Workflow SHALL calculate Cost_Estimate with Decimal arithmetic and record every estimate input.
14. IF Preflight cannot produce a finite call bound, finite cost estimate, complete Official_Rates, successful identity resolution, or collision-safe scope, THEN THE Production_Workflow SHALL block Paid_Authorization.
15. THE Preflight_Record SHALL bind Frozen_Plan, Targeted_Checks, Identity_Evidence, Official_Rates, reuse decisions, call bounds, Cost_Estimate, destination states, and Protected_Inventory by SHA-256.
16. THE Preflight SHALL make zero Bedrock model calls.

### Requirement 5: Maintain independent concurrency-safe transaction truth

**User Story:** As the audiobook producer, I want progress stored independently per Track, so that concurrency and one corrupt aggregate cannot lose book-wide progress.

#### Acceptance Criteria

1. WHEN a Track_Plan is materialized, THE Production_Workflow SHALL create one independent Track_Transaction directory.
2. WHEN Track_Transaction state changes, THE Transaction_Ledger SHALL append one canonical Ledger event with sequence number, prior event hash, payload hash, prior state, next state, and timestamp.
3. WHEN Strict_Record_Codec serializes or parses a Ledger event, THE Strict_Record_Codec SHALL preserve the complete event value through a serialize-parse round trip.
4. THE Transaction_Ledger SHALL permit only defined transitions among discovered, planned, preflight-passed, authorization-required, running, charge-uncertain, rendered, validated, delivered, and blocked.
5. IF a Transaction_Ledger contains a sequence gap, duplicate sequence, broken hash, unknown field, malformed value, or invalid transition, THEN THE Production_Workflow SHALL block only the affected Track_Transaction.
6. WHEN a mutating Track operation begins, THE Production_Workflow SHALL acquire an exclusive lock scoped to book ID and Track ID before mutation.
7. IF another writer holds the scoped lock, THEN THE Production_Workflow SHALL return without mutating Track_Transaction.
8. WHEN Production_Workflow commits a ledger event or immutable record, THE Production_Workflow SHALL flush files, synchronize directories, and use exclusive creation or same-filesystem atomic replacement.
9. THE Derived_Status_Index SHALL remain a rebuildable cache rather than transaction authority.
10. IF Derived_Status_Index is absent, stale, or corrupt, THEN THE Production_Workflow SHALL rebuild status from valid independent Transaction_Ledgers.
11. IF one Track_Transaction is corrupt, THEN THE Production_Workflow SHALL preserve the reconstructed states of every other valid Track_Transaction.
12. WHEN a completed nonbillable operation is repeated with unchanged inputs, THE Production_Workflow SHALL return the prior equivalent result without creating a paid attempt.

### Requirement 6: Bind paid authorization to exact finite scope

**User Story:** As the paying operator, I want one explicit, expiring authorization for exact Tracks and limits, so that approval cannot expand into retries or different work.

#### Acceptance Criteria

1. WHERE one Track is selected, THE Production_CLI SHALL support Paid_Authorization for exactly one Track_Transaction.
2. WHERE multiple Tracks are selected, THE Production_CLI SHALL support Paid_Authorization for exactly the bounded ordered Track_Transactions in Frozen_Plan.
3. WHEN Paid_Authorization is created, THE Production_Workflow SHALL bind Frozen_Plan SHA-256 and Preflight_Record SHA-256.
4. WHEN Paid_Authorization is created, THE Production_Workflow SHALL bind exact ordered transaction IDs, Track IDs, and Direct_Child_Worker command hashes.
5. WHEN Paid_Authorization is created, THE Production_Workflow SHALL bind maximum new calls per Track and in total.
6. WHEN Paid_Authorization is created, THE Production_Workflow SHALL bind Cost_Estimate, operator-approved maximum estimated pre-tax USD amount, issue time, and expiration time.
7. IF the operator-approved maximum estimated pre-tax amount is lower than Cost_Estimate, THEN THE Production_Workflow SHALL reject Paid_Authorization.
8. WHEN Paid_Authorization is requested, THE Production_CLI SHALL require an explicit confirmation displaying plan digest, exact Track scope, command hashes, call bounds, estimated amount, approved maximum, and expiration.
9. THE Production_Workflow SHALL classify specification creation, task selection, prior confirmations, and generic approvals as insufficient Paid_Authorization.
10. IF Paid_Authorization is missing, expired, stale, consumed, hash-mismatched, command-mismatched, scope-mismatched, or over call bounds, THEN THE Production_Workflow SHALL stop before direct-child launch.
11. WHEN Paid_Authorization is consumed, THE Production_Workflow SHALL durably record one-shot consumption before direct-child launch.
12. THE Paid_Authorization SHALL permit zero automatic retries and zero unlisted Track or call additions.
13. WHEN an authorized batch stops before later Tracks, THE Production_Workflow SHALL require fresh current Preflight and Paid_Authorization before any later Track starts.

### Requirement 7: Capture one atomic direct-child paid attempt

**User Story:** As the paying operator, I want definitive native process evidence for each Track, so that a console summary cannot conceal an unknown exit or duplicate attempt.

#### Acceptance Criteria

1. WHEN Paid_Attempt_Wrapper starts an attempt, THE Paid_Attempt_Wrapper SHALL refuse an existing committed attempt ID, staging attempt, ambiguity marker, or consumed duplicate attempt.
2. WHEN Paid_Attempt_Wrapper prepares an attempt, THE Paid_Attempt_Wrapper SHALL create a same-filesystem staging directory.
3. WHEN Paid_Attempt_Wrapper launches Direct_Child_Worker, THE Paid_Attempt_Wrapper SHALL use the exact bound argv as a direct child without a shell pipeline.
4. WHEN Paid_Attempt_Wrapper selects credentials, THE Paid_Attempt_Wrapper SHALL pass only the configured profile selection to Direct_Child_Worker without persisting the environment.
5. WHILE Direct_Child_Worker runs, THE Paid_Attempt_Wrapper SHALL tee combined stdout and stderr to the operator and a prose-free sanitized console log.
6. WHEN Direct_Child_Worker exits, THE Paid_Attempt_Wrapper SHALL capture the native integer return code directly from `Popen.wait()`.
7. WHEN attempt evidence is complete, THE Paid_Attempt_Wrapper SHALL record exact argv, command hash, working directory, fixed profile label, authorization hash, timestamps, child-launched fact, native return code, termination signal, console hash, no-retry fact, and no-environment fact.
8. WHEN staged attempt evidence is complete, THE Paid_Attempt_Wrapper SHALL flush files, synchronize staging, atomically rename staging to Paid_Attempt_Bundle, and synchronize the parent directory.
9. IF a launched attempt has staging residue, a missing required file, a missing integer native return code, an inconsistent hash, or interrupted wrapper evidence, THEN THE Production_Workflow SHALL classify Track_Transaction as Charge_Uncertain.
10. IF Direct_Child_Worker returns a nonzero native return code, THEN THE Production_Workflow SHALL retain Paid_Attempt_Bundle and transition Track_Transaction to blocked without automatic retry.
11. THE Paid_Attempt_Wrapper SHALL persist no credential value, access key, account ID, ARN, role/user identifier, environment dump, prose body, or transcript body.

### Requirement 8: Execute bounded batches independently and fail fast

**User Story:** As the audiobook producer, I want bounded batches with independent Track outcomes, so that one failure stops exposure without discarding completed work.

#### Acceptance Criteria

1. WHEN Batch_Coordinator receives a valid Paid_Authorization, THE Batch_Coordinator SHALL process Track_Transactions in Frozen_Plan order.
2. THE Batch_Coordinator SHALL process paid Track_Transactions sequentially by default.
3. WHEN one Track_Transaction starts, THE Batch_Coordinator SHALL use a distinct Paid_Attempt_Bundle and Transaction_Ledger for the Track_Transaction.
4. WHEN Direct_Child_Worker prepares a model call, THE Direct_Child_Worker SHALL revalidate source hash, Effective_Track_Config, protected runtime hashes, authorization scope, and remaining call bound.
5. WHEN Direct_Child_Worker completes segment rendering, THE Direct_Child_Worker SHALL revalidate source hash before final assembly.
6. WHEN an Active_Segment lacks an acceptable Reused_Segment, THE Direct_Child_Worker SHALL make at most one new model call for the Active_Segment in the authorized attempt.
7. IF a Track_Transaction produces nonzero status, Charge_Uncertain, source drift, protected-runtime drift, authorization mismatch, call-bound exhaustion, Exact_Fidelity failure, or partial-turn failure, THEN THE Batch_Coordinator SHALL stop before the next Track.
8. WHEN Batch_Coordinator stops on a Track failure, THE Batch_Coordinator SHALL retain completed prior Track states and leave later Tracks unstarted with zero model calls.
9. WHEN Batch_Coordinator reports progress, THE Batch_Report SHALL derive `not-started`, `running`, `partial`, `blocked`, or `complete` from independent Track_Transactions.

### Requirement 9: Validate reuse, inspect resume, and require manual recovery

**User Story:** As the paying operator, I want reuse and recovery to be evidence-based and nonbillable, so that old artifacts do not hide new calls or trigger accidental retries.

#### Acceptance Criteria

1. WHEN Reuse_Inspector evaluates a candidate segment, THE Reuse_Inspector SHALL verify source/segment hash, Effective_Track_Config binding, audio hash, transcript policy, complete Event_Journal replay, LPCM equality, and zero mid-sentence partial turns.
2. WHEN a candidate passes every reuse check, THE Reuse_Inspector SHALL classify the candidate as Reused_Segment.
3. WHEN Reused_Segment is used, THE Production_Workflow SHALL assign zero new model calls to Reused_Segment.
4. WHEN Reused_Segment is used, THE Production_Workflow SHALL assign zero Current_Execution_Totals to Reused_Segment.
5. WHEN Resume_Inspector reads Track_Transaction, THE Resume_Inspector SHALL validate ledger, attempt, authorization-consumption, source/config binding, and runtime artifact evidence without a model call.
6. WHEN Resume_Inspector completes, THE Resume_Inspector SHALL classify recovery as nothing-to-resume, local-validation-available, complete-artifacts-recoverable, charge-uncertain-review-required, or blocked-new-plan-required.
7. WHERE complete local artifacts validate, THE Manual_Resolver SHALL support accepting complete local artifacts and transition Track_Transaction from charge-uncertain to rendered.
8. WHERE local artifacts are invalid or an uncertain attempt is abandoned, THE Manual_Resolver SHALL retain evidence and transition Track_Transaction to blocked.
9. THE Manual_Resolver SHALL make zero identity, pricing, or model calls.
10. IF the operator requests another paid attempt after a launched failure or uncertainty, THEN THE Production_Workflow SHALL require a new Track_Transaction, new Frozen_Plan, new Preflight_Record, and new Paid_Authorization.
11. IF a prior attempt may have charged, THEN THE Production_Workflow SHALL require explicit duplicate-charge acknowledgement bound to the retained attempt digest before authorizing a new attempt.

### Requirement 10: Validate manifests, fidelity, replay, and assembly deterministically

**User Story:** As the proof listener, I want every delivered Track bound to its frozen source and runtime evidence, so that omissions, substitutions, stale artifacts, and partial turns are detected.

#### Acceptance Criteria

1. WHEN Postflight_Validator starts, THE Postflight_Validator SHALL require Paid_Attempt_Bundle with native return code `0` for a paid Track_Transaction.
2. WHEN Postflight_Validator reads Runtime_Manifest, THE Postflight_Validator SHALL verify Track ID, Track kind, source path/hashes, Effective_Track_Config, spoken token count, target segment size, segment count, and Track WAV path against Track_Plan.
3. THE Postflight_Validator SHALL verify Runtime_Manifest active segment count equals the number of Active_Segments.
4. THE Postflight_Validator SHALL verify Active_Segment IDs are unique and contiguous in assembly order.
5. THE Postflight_Validator SHALL verify concatenated Active_Segment normalized tokens equal the frozen Spoken_Text token sequence.
6. THE Postflight_Validator SHALL verify every Active_Segment has exact transcript match, coverage ratio `1.0`, and zero mid-sentence partial turns.
7. THE Postflight_Validator SHALL verify every Active_Segment recorded audio SHA-256 against current segment WAV bytes.
8. THE Postflight_Validator SHALL replay every bound complete Event_Journal and verify reconstructed FINAL transcript and LPCM against accepted transcript and segment WAV.
9. THE Postflight_Validator SHALL exclude historical, rejected, and carried-over artifacts from active fidelity, segment, assembly, and usage totals.
10. WHEN all Active_Segments pass Exact_Fidelity, THE Postflight_Validator SHALL verify Track WAV assembly order and recorded stitching profile.
11. WHEN Track WAV exists, THE Postflight_Validator SHALL verify configured sample rate, sample size, channel count, uncompressed PCM encoding, SHA-256, byte count, and frame-derived duration.
12. IF any attempt, manifest, segment, transcript, replay, partial-turn, hash, path, assembly, format, or duration check fails, THEN THE Production_Workflow SHALL block Delivery_Gate.

### Requirement 11: Reconcile exact usage and separate service cost from billing

**User Story:** As the paying operator, I want exact four-modality usage and cost evidence, so that reuse, current charges, estimates, and invoices remain distinct.

#### Acceptance Criteria

1. THE Postflight_Validator SHALL resolve exactly one Event_Journal from the active audio stem of every Active_Segment.
2. WHEN Postflight_Validator parses Event_Journal, THE Postflight_Validator SHALL sum only integer modality-specific `usageEvent.details.delta` values.
3. WHEN one Event_Journal aggregation completes, THE Postflight_Validator SHALL verify each modality delta sum against the terminal modality total.
4. WHEN one Event_Journal aggregation completes, THE Postflight_Validator SHALL verify combined modality sums against terminal top-level input, output, and total token values.
5. THE Postflight_Validator SHALL calculate Active_Artifact_Totals from each validated active Event_Journal exactly once.
6. THE Postflight_Validator SHALL calculate Current_Execution_Totals from only segments newly rendered in the current Paid_Attempt_Bundle.
7. WHEN Cost_Calculator receives token totals and Official_Rates, THE Cost_Calculator SHALL calculate each modality subtotal as `Decimal(tokens) × Decimal(rate_per_1k) ÷ Decimal(1000)`.
8. THE Cost_Calculator SHALL calculate one Computed_Pre_Tax_Service_Cost from Active_Artifact_Totals and one from Current_Execution_Totals.
9. THE Cost_Calculator SHALL retain every modality token count, exact rate, formula, unrounded subtotal, sum, and Official_Rate provenance.
10. THE Track_Report SHALL label Cost_Estimate separately from Computed_Pre_Tax_Service_Cost.
11. THE Track_Report SHALL label Billing_Confirmation separately as pending, not-performed, or confirmed with amount and date.
12. IF an Event_Journal is missing, duplicated, malformed, unbound, or internally inconsistent, THEN THE Production_Workflow SHALL block Delivery_Gate rather than estimate exact usage.
13. IF all four current Official_Rates lack complete official provenance, THEN THE Cost_Calculator SHALL block Computed_Pre_Tax_Service_Cost.
14. IF Computed_Pre_Tax_Service_Cost exceeds the operator-approved maximum estimated amount, THEN THE Track_Report SHALL record a blocking budget exception for operator review.

### Requirement 12: Deliver collision-safely and report reconstructable status

**User Story:** As the audiobook producer, I want idempotent delivery and clear track/batch status, so that files are never silently overwritten and partial progress remains understandable.

#### Acceptance Criteria

1. WHEN Delivery_Gate passes and the configured destination is absent, THE Proof_Deliverer SHALL atomically publish a byte-identical copy of the validated Track WAV.
2. WHEN Delivery_Gate passes and the configured destination is byte-identical, THE Proof_Deliverer SHALL retain the destination unchanged and record `already-identical`.
3. IF the configured destination exists with a different SHA-256, THEN THE Proof_Deliverer SHALL retain the destination unchanged and block delivery.
4. WHEN Proof_Deliverer creates or retains a destination, THE Proof_Deliverer SHALL verify matching byte counts, complete byte sequences, and SHA-256 values.
5. WHEN delivery succeeds, THE Production_Workflow SHALL create Track_Report from validated evidence.
6. THE Track_Report SHALL include source/config/plan/preflight/authorization/attempt digests, native status, fidelity, replay, assembly, reuse, usage, estimate, exact cost, billing, delivery, isolation, and test results.
7. WHEN multiple Tracks belong to Frozen_Plan, THE Production_Workflow SHALL create Batch_Report listing every selected Track_Transaction and derived state.
8. WHEN Production_CLI reports book status, THE Production_CLI SHALL derive status from independent valid Transaction_Ledgers.
9. IF a Derived_Status_Index is corrupt, THEN THE Production_CLI SHALL report the corrupt cache and rebuild status without changing transaction truth.
10. WHEN a successful deliver, report, or status operation is repeated with unchanged inputs, THE Production_Workflow SHALL produce an equivalent result without starting a model call.
11. WHERE listening feedback is supplied, THE Track_Report SHALL label listening feedback as supplemental to deterministic Delivery_Gate results.

### Requirement 13: Enforce scoped per-file isolation

**User Story:** As the manuscript owner, I want per-file protection and honest attribution, so that active production inputs and prior audio are preserved without blaming unrelated concurrent edits.

#### Acceptance Criteria

1. WHEN Production_Workflow creates Protected_Inventory, THE Production_Workflow SHALL record workspace-relative path, kind, existence, byte count, SHA-256, Git status, and attribution per selected file.
2. THE Production_Workflow SHALL define Workflow_Write_Allowlist from selected plan/transaction roots, derived index paths, and approved delivery destinations.
3. WHILE normal production executes, THE Production_Workflow SHALL attribute workflow-owned writes only to Workflow_Write_Allowlist.
4. WHEN isolation is evaluated, THE Production_Workflow SHALL hard-gate selected sources, production runtime/configuration/dependencies, and prior audio used for reuse by individual path and SHA-256.
5. THE Production_Workflow SHALL preserve every existing Chapter 1 and Chapter 2 narration artifact and proof copy at preflight bytes.
6. THE Production_Workflow SHALL preserve `.kiro/specs/chapter-2-audio-proof/`, `.kiro/specs/chapter-3-audio-proof/`, and `.kiro/specs/The-Final-Frontier-novel/` at preflight bytes.
7. WHEN an unselected manuscript file changes without workflow-write evidence, THE Production_Workflow SHALL classify the path as Concurrent_Manuscript_Change separately from workflow-owned changes.
8. WHEN Concurrent_Manuscript_Change exists, THE Delivery_Gate SHALL evaluate selected source and hard Protected_Artifact invariants independently from any whole-novel aggregate.
9. IF a workflow-owned write occurs outside Workflow_Write_Allowlist, THEN THE Production_Workflow SHALL block Delivery_Gate.
10. THE Production_Workflow SHALL use no whole-novel aggregate as the sole isolation gate.

### Requirement 14: Preserve and recognize legacy outputs without rewriting them

**User Story:** As the audiobook producer, I want Chapter 1 and Chapter 2 recognized read-only, so that prior paid work can be validated or reused without migration risk.

#### Acceptance Criteria

1. WHEN Legacy_Adapter scans existing output conventions, THE Legacy_Adapter SHALL discover Chapter 1 and Chapter 2 manifests, segment WAVs, transcripts, Event_Journals, assembled WAVs, and proof paths without mutation.
2. WHEN Legacy_Adapter records an observation, THE Legacy_Adapter SHALL bind each discovered Legacy_Artifact by path, byte count, and SHA-256.
3. WHEN Legacy_Adapter evaluates Legacy_Artifact for reuse, THE Legacy_Adapter SHALL apply current source, Effective_Track_Config, Exact_Fidelity, audio-hash, event-replay, usage, and partial-turn checks.
4. WHEN Legacy_Artifact passes every reuse check, THE Legacy_Adapter SHALL expose Legacy_Artifact as a read-only reuse candidate.
5. IF Legacy_Artifact is incomplete, ambiguous, mismatched, or lacks required evidence, THEN THE Legacy_Adapter SHALL classify Legacy_Artifact as a rejected read-only observation.
6. THE Legacy_Adapter SHALL preserve every Legacy_Artifact byte regardless of reuse classification.
7. THE Production_Workflow SHALL write new production outputs using the new transaction schema rather than rewriting legacy layout.

### Requirement 15: Sanitize evidence and constrain trust boundaries

**User Story:** As the manuscript owner, I want minimal private data in production evidence, so that auditability does not expose manuscript or account details.

#### Acceptance Criteria

1. THE Production_Workflow SHALL persist from each identity response only fixed profile label, identity-resolution boolean, and UTC timestamp.
2. THE Production_Workflow SHALL exclude account ID, ARN, role/user identifier, access key, credential value, credential type, credential source, credential age, credential expiration, and every other returned identity field from Evidence_Artifacts.
3. THE Production_Workflow SHALL exclude prose bodies, segment text, transcript bodies, and raw Event_Journal payloads from Evidence_Artifacts.
4. THE Production_Workflow SHALL confine required private runtime transcripts and raw Event_Journals to ignored Track_Transaction runtime roots.
5. THE Paid_Attempt_Wrapper SHALL exclude environment dumps and credential values from console and result evidence.
6. WHEN Production_Workflow reads configuration, JSON, source, legacy, pricing, manifest, journal, or path input, THE Production_Workflow SHALL treat the input as untrusted and validate schema, encoding, containment, and allowed values.
7. THE Production_Workflow SHALL resolve source, runtime, evidence, and delivery paths inside approved roots without following unsafe links.
8. WHEN evidence sanitization detects a forbidden category, THE Production_Workflow SHALL record category, path, and count without reproducing the prohibited value.
9. THE Production_Workflow SHALL retain original failed and Charge_Uncertain evidence rather than rewrite evidence as success.

### Requirement 16: Gate reusable implementation quality without unnecessary dependencies

**User Story:** As the maintainer, I want focused automated coverage and one documented workflow, so that the implementation is safe once and routine chapter work remains command-driven.

#### Acceptance Criteria

1. THE Targeted_Checks SHALL cover configuration parsing/printing, override resolution, planning, transaction state, locking, authorization, atomic attempts, batch stops, reuse/resume, deterministic validation, accounting, delivery, isolation, sanitization, legacy compatibility, and Special_Tracks.
2. THE Targeted_Checks SHALL make zero AWS identity, pricing, or model calls.
3. WHEN a correctness property benefits from broad input variation, THE Targeted_Checks SHALL execute at least 100 deterministic generated cases and report the seed.
4. IF a Targeted_Check fails, THEN THE Production_Workflow SHALL block Paid_Authorization and Chapter_3_Pilot paid execution.
5. WHEN Broader_Suite_Result exists, THE Production_Workflow SHALL report Broader_Suite_Result separately from Targeted_Checks.
6. IF a Broader_Suite_Result failure overlaps a Targeted_Check contract, THEN THE Production_Workflow SHALL classify the overlapping failure as blocking.
7. IF a Broader_Suite_Result failure does not overlap a Targeted_Check contract, THEN THE Production_Workflow SHALL retain the failure as a non-gating diagnostic.
8. THE Generic_Production_Subsystem SHALL use existing pinned dependencies and Python standard library without a new dependency.
9. IF a new dependency becomes demonstrably necessary, THEN THE Generic_Production_Subsystem SHALL require a separate reviewed exact-version pin and justification before use.
10. THE Production_Workflow SHALL document stable CLI operations, safety boundaries, state/recovery semantics, configuration, and normal single/batch examples in `audiobook-studio/README.md`.

### Requirement 17: Accept the reusable workflow through a separately authorized Chapter 3 pilot

**User Story:** As the audiobook producer, I want one guarded Chapter 3 acceptance run, so that reusable production behavior is proven before normal book-wide use.

#### Acceptance Criteria

1. THE Chapter_3_Pilot SHALL select `The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md` as one Chapter_Track.
2. WHEN Chapter_3_Pilot planning runs, THE Production_Workflow SHALL recompute source counts, source hashes, Spoken_Text hashes, segments, and call bounds into Frozen_Plan rather than copy historical Chapter 3 values.
3. WHEN Chapter_3_Pilot Preflight runs, THE Production_Workflow SHALL complete Targeted_Checks, Source_Snapshot, Protected_Inventory, reuse classification, collision checks, Identity_Evidence, Official_Rates, maximum calls, and Cost_Estimate without a model call.
4. WHEN Chapter_3_Pilot Preflight passes, THE Production_Workflow SHALL present exact plan/preflight digests, one Track scope, command hash, maximum calls, estimate, approved maximum, and expiration for review.
5. THE Production_Workflow SHALL classify this specification and all nonbillable Chapter_3_Pilot work as insufficient paid authorization.
6. WHEN the operator gives a fresh confirmation naming Chapter_3_Pilot authorization, THE Production_Workflow SHALL create Paid_Authorization for exactly one Chapter_3_Pilot attempt.
7. IF fresh Chapter_3_Pilot Paid_Authorization is absent, declined, stale, or mismatched, THEN THE Production_Workflow SHALL stop before a model call.
8. WHEN Chapter_3_Pilot paid execution starts, THE Production_Workflow SHALL execute exactly one Track_Transaction through Paid_Attempt_Wrapper.
9. IF Chapter_3_Pilot produces nonzero status, Charge_Uncertain, source drift, protected-runtime drift, Exact_Fidelity failure, or partial-turn failure, THEN THE Production_Workflow SHALL retain evidence and stop without retry or delivery.
10. WHEN Chapter_3_Pilot returns native status `0`, THE Production_Workflow SHALL complete deterministic validation, exact usage/cost accounting, collision-safe delivery, and sanitized reporting.
11. WHEN Chapter_3_Pilot Delivery_Gate passes, THE Production_Workflow SHALL mark the reusable workflow accepted for future normal Track execution.
12. THE Production_Workflow SHALL perform no Chapter_3_Pilot command, test, AWS call, narration, or paid work during specification creation.
