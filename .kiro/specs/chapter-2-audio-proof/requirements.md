# Requirements Document

## Introduction

This specification defines a guarded, one-chapter operational workflow for producing and delivering a Tiffany proof-listening WAV for manuscript Chapter 2 with the existing Amazon Nova 2 Sonic tooling. The workflow performs nonbillable preflight, explicitly authorized rendering or reuse, deterministic validation, exact token accounting, and transparent cost reporting without changing prose, narration code, dependencies, Chapter 1 artifacts, or the governing novel spec.

## Glossary

- **Audio_Proof_Workflow**: The complete Chapter 2 preflight, paid-render, validation, accounting, and delivery process.
- **Existing_Narration_CLI**: The installed Python entry point `.venv/bin/python -m frontier_audiobook` executed from `audiobook-studio/`.
- **Chapter_2_Source**: `The Final Frontier Novel/chapters/discovery-part/discovery-part-002-an-ordinary-morning.md`.
- **Named_AWS_Profile**: The exact profile label `frontier-audiobook`, user-approved as a valid static-credential profile rather than an SSO profile. The workflow does not inspect or accept/reject the profile based on credential type, source, age, expiration, or lifetime; successful resolution through a non-model identity call is sufficient.
- **Preflight**: Read-only local checks, one non-model identity call using `AWS_PROFILE=frontier-audiobook`, and `narrate --dry-run`; Preflight makes no Bedrock model call.
- **Paid_Render**: An Existing_Narration_CLI Chapter 2 narration invocation carrying `AWS_PROFILE=frontier-audiobook` and `--confirm-paid-render`.
- **Active_Segment**: A segment in the final manifest `segments` collection used to assemble the delivered chapter audio.
- **Reused_Segment**: An Active_Segment accepted from an intact prior Chapter 2 artifact without a new model invocation.
- **Event_Journal**: The JSONL Nova output-event file bound by filename stem to one Active_Segment audio file.
- **Exact_Fidelity**: Equality of expected and FINAL transcript word sequences under the configured normalization, with matching replayed audio and zero mid-sentence partial turns.
- **Postflight_Validator**: The read-only checks over the final manifest, source hashes, segment artifacts, Event_Journals, and Chapter_WAV.
- **Chapter_WAV**: `audiobook-studio/build/narration/chapter-002-tiffany/chapter-002-tiffany.wav`.
- **Proof_Copy**: `voice-samples/chapter-2-tiffany-proof.wav`.
- **Proof_Deliverer**: The delivery step that copies a validated Chapter_WAV to the Proof_Copy path.
- **Active_Artifact_Totals**: Four-modality token totals from exactly one validated Event_Journal per Active_Segment, including Reused_Segments.
- **Current_Execution_Totals**: Four-modality token totals from only the segments newly narrated by the current Paid_Render.
- **Four_Modality_Tokens**: Input speech, input text, output speech, and output text token counts.
- **Official_Rate**: A current Nova Sonic 2.0 on-demand `us-east-1` USD rate from an official AWS pricing source for one Four_Modality_Tokens category.
- **Cost_Calculator**: The decimal calculation that multiplies each Four_Modality_Tokens count by the corresponding Official_Rate per 1,000 tokens and sums the subtotals.
- **Computed_Pre_Tax_Service_Cost**: A token-derived Bedrock service estimate before tax, credits, discounts, rounding on an invoice, or other account adjustments.
- **Billing_Confirmation**: A separately obtained Cost Explorer or invoice amount and confirmation date.
- **Proof_Report**: `audiobook-studio/build/narration/chapter-002-tiffany/chapter-002-tiffany-proof-report.md`.
- **Delivery_Gate**: The condition in which all required source, manifest, fidelity, journal, WAV, accounting, and cost checks have passed.
- **Protected_Artifacts**: Chapter prose, `.kiro/specs/The-Final-Frontier-novel/`, narration source/dependency files, Chapter 1 build outputs, and Chapter 1 proof copies.

## Requirements

### Requirement 1: Perform a nonbillable and deterministic preflight

**User Story:** As the proof operator, I want Chapter 2 and the execution context verified before rendering, so that the paid operation targets the intended source, voice, region, profile, and destination.

#### Acceptance Criteria

1. THE Audio_Proof_Workflow SHALL resolve Chapter_2_Source to exactly one manuscript file.
2. WHEN Preflight reads Chapter_2_Source, THE Audio_Proof_Workflow SHALL verify `chapter: 2`, `pov_id: POV-NIA`, `words: 1137`, and a normalized Prose Body word count of 1137.
3. WHEN Preflight invokes the Existing_Narration_CLI, THE Audio_Proof_Workflow SHALL use chapter `2`, voice `tiffany`, target segment size `5`, and `--dry-run`.
4. WHEN the dry-run completes, THE Audio_Proof_Workflow SHALL verify that the dry-run reports zero billable calls and a positive planned-call count.
5. THE Audio_Proof_Workflow SHALL verify model `amazon.nova-2-sonic-v1:0` and region `us-east-1` before Paid_Render.
6. WHEN Preflight evaluates Named_AWS_Profile, THE Audio_Proof_Workflow SHALL require successful resolution through a non-model identity call as the sole credential acceptance condition.
7. IF any source, configuration, destination, or prior-artifact check is ambiguous or invalid, or Named_AWS_Profile fails to resolve successfully, THEN THE Audio_Proof_Workflow SHALL stop before Paid_Render.

### Requirement 2: Render or reuse Chapter 2 under explicit billing controls

**User Story:** As the paying operator, I want explicit authorization and safe segment reuse, so that Chapter 2 is rendered without accidental or duplicate model calls.

#### Acceptance Criteria

1. WHEN Preflight passes and paid execution is authorized, THE Audio_Proof_Workflow SHALL invoke Paid_Render exactly once using Named_AWS_Profile.
2. WHEN Paid_Render begins, THE Existing_Narration_CLI SHALL use chapter `2`, voice `tiffany`, target segment size `5`, and exact-fidelity mode.
3. IF `--confirm-paid-render` is absent, THEN THE Existing_Narration_CLI SHALL reject Paid_Render before a Bedrock model call.
4. WHEN an intact prior segment matches the current segment text and fidelity policy, THE Existing_Narration_CLI SHALL classify the segment as a Reused_Segment.
5. WHEN a segment is classified as a Reused_Segment, THE Audio_Proof_Workflow SHALL count zero new billable calls for the segment.
6. WHEN a segment lacks an acceptable reusable artifact, THE Existing_Narration_CLI SHALL make at most one new model call for the segment during the invocation.
7. IF a call fails, becomes charge-uncertain, crosses a mid-sentence partial turn, or fails Exact_Fidelity, THEN THE Audio_Proof_Workflow SHALL stop without an automatic retry.

### Requirement 3: Validate the manifest and every active segment

**User Story:** As a proof listener, I want the delivered audio bound to the exact Chapter 2 text and recorded evidence, so that omissions, substitutions, stale artifacts, and partial turns are detected.

#### Acceptance Criteria

1. WHEN Paid_Render completes, THE Postflight_Validator SHALL verify the manifest chapter, voice, source path, target segment size, source hash, spoken hash, and Chapter_WAV path against the design contract.
2. THE Postflight_Validator SHALL verify that manifest `segment_count` equals the number of Active_Segments.
3. THE Postflight_Validator SHALL verify that Active_Segment identifiers are unique and contiguous in assembly order.
4. THE Postflight_Validator SHALL verify every Active_Segment has `status` equal to `narrated`, `exact_transcript_match` equal to `true`, `coverage_ratio` equal to `1.0`, and `mid_sentence_partial_turns` equal to zero.
5. THE Postflight_Validator SHALL verify every Active_Segment recorded audio SHA-256 against the corresponding segment WAV bytes.
6. THE Postflight_Validator SHALL replay every Active_Segment bound Event_Journal and verify the reconstructed FINAL transcript and audio against the accepted transcript and segment WAV.
7. THE Postflight_Validator SHALL exclude `carried_over_segments` from active fidelity, assembly, segment, and token totals.
8. IF any manifest or Active_Segment validation fails, THEN THE Audio_Proof_Workflow SHALL block the Delivery_Gate.

### Requirement 4: Validate and deliver the assembled proof WAV

**User Story:** As a proof listener, I want one correctly assembled and clearly named WAV, so that I can listen to Chapter 2 without confusing the proof with another chapter or render.

#### Acceptance Criteria

1. WHEN every Active_Segment passes Exact_Fidelity, THE Existing_Narration_CLI SHALL assemble Chapter_WAV from the ordered Active_Segments under the recorded stitching profile.
2. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify the recorded chapter SHA-256 against the Chapter_WAV bytes.
3. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify 24 kHz sample rate, 16-bit sample size, and one audio channel.
4. WHEN Chapter_WAV exists, THE Postflight_Validator SHALL verify the manifest duration against the frame-derived duration to the manifest precision.
5. WHEN the Delivery_Gate passes, THE Proof_Deliverer SHALL copy Chapter_WAV to Proof_Copy.
6. WHEN Proof_Copy is created, THE Proof_Deliverer SHALL verify that Proof_Copy and Chapter_WAV have identical byte counts and SHA-256 hashes.
7. IF an existing Proof_Copy has a different SHA-256 hash, THEN THE Proof_Deliverer SHALL stop before overwriting the existing Proof_Copy.

### Requirement 5: Aggregate exact usage and execution accounting

**User Story:** As the paying operator, I want journal-derived modality totals and reuse accounting, so that the delivered proof and the current invocation have auditable usage records.

#### Acceptance Criteria

1. THE Postflight_Validator SHALL resolve exactly one Event_Journal from the active audio stem of every Active_Segment.
2. WHEN the Postflight_Validator parses an Event_Journal, THE Postflight_Validator SHALL sum only modality-specific `usageEvent.details.delta` integer values.
3. WHEN Event_Journal aggregation completes, THE Postflight_Validator SHALL verify each modality sum against the terminal `usageEvent.details.total` value.
4. WHEN Event_Journal aggregation completes, THE Postflight_Validator SHALL verify combined modality sums against the terminal top-level input, output, and total token values.
5. THE Postflight_Validator SHALL calculate Active_Artifact_Totals from exactly one validated Event_Journal per Active_Segment.
6. THE Postflight_Validator SHALL calculate Current_Execution_Totals from only segments newly narrated by the current Paid_Render.
7. WHEN a Reused_Segment is reported, THE Postflight_Validator SHALL assign zero current-execution billable calls to the Reused_Segment.
8. WHEN a Reused_Segment is reported, THE Postflight_Validator SHALL assign zero Current_Execution_Totals to the Reused_Segment.
9. IF an Event_Journal is missing, duplicated, malformed, unbound, or internally inconsistent, THEN THE Audio_Proof_Workflow SHALL block the Delivery_Gate.

### Requirement 6: Calculate and distinguish service cost

**User Story:** As the paying operator, I want modality-specific official pricing applied transparently, so that the proof has a reproducible cost estimate distinct from account billing records.

#### Acceptance Criteria

1. WHEN cost calculation begins, THE Cost_Calculator SHALL retrieve or verify one Official_Rate for each Four_Modality_Tokens category.
2. WHEN Official_Rates are recorded, THE Cost_Calculator SHALL record the official source URL, retrieval date, effective date, region, model, unit, and USD rate.
3. WHEN token totals and Official_Rates are available, THE Cost_Calculator SHALL use decimal arithmetic to calculate each modality subtotal as `tokens × rate_per_1k ÷ 1000`.
4. THE Cost_Calculator SHALL calculate one Computed_Pre_Tax_Service_Cost from Active_Artifact_Totals.
5. THE Cost_Calculator SHALL calculate one Computed_Pre_Tax_Service_Cost from Current_Execution_Totals.
6. THE Cost_Calculator SHALL include input speech, input text, output speech, and output text subtotals in each Computed_Pre_Tax_Service_Cost.
7. WHEN a Computed_Pre_Tax_Service_Cost is reported, THE Cost_Calculator SHALL label Billing_Confirmation as a separate pending, not-performed, or confirmed value with a confirmation date.
8. IF all four Official_Rates cannot be verified from an official AWS source, THEN THE Cost_Calculator SHALL leave Computed_Pre_Tax_Service_Cost blocked rather than substitute third-party rates.

### Requirement 7: Produce auditable evidence without changing protected work

**User Story:** As the manuscript owner, I want a concise execution record and strict isolation, so that proof narration is auditable without altering creative or prior narration work.

#### Acceptance Criteria

1. WHEN the Delivery_Gate passes, THE Audio_Proof_Workflow SHALL create Proof_Report at the specified Chapter 2 build path.
2. THE Proof_Report SHALL identify the source path, source/spoken hashes, model, region, voice, AWS profile label, target segment size, and execution timestamps.
3. THE Proof_Report SHALL state the manifest result, exact-fidelity count, partial-turn count, duration, total segment count, newly billed-call count, and Reused_Segment count.
4. THE Proof_Report SHALL contain Active_Artifact_Totals and Current_Execution_Totals for all Four_Modality_Tokens categories.
5. THE Proof_Report SHALL contain Official_Rates, modality subtotals, both Computed_Pre_Tax_Service_Cost values, and Billing_Confirmation status.
6. THE Proof_Report SHALL record matching Chapter_WAV and Proof_Copy SHA-256 hashes.
7. THE Audio_Proof_Workflow SHALL sanitize every evidence artifact, including Proof_Report, by retaining from the non-model identity call only the Named_AWS_Profile label, identity-resolution pass/fail value, and timestamp and excluding account IDs, ARNs, role identifiers, access keys, credential values, every other returned identity detail, and transcript bodies.
8. THE Audio_Proof_Workflow SHALL preserve every Protected_Artifact without modification.
9. THE Audio_Proof_Workflow SHALL use only dependencies present before Preflight.
10. THE Audio_Proof_Workflow SHALL preserve every narration source file byte-for-byte.
