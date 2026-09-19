# The Final Frontier audiobook workflows

This directory contains two guarded workflows:

- `frontier-audiobook production ...` is the reusable, transaction-based workflow for normal chapter and approved special-track production. After the separately authorized Chapter 3 pilot is accepted, future normal tracks use this reusable workflow and generated plan/transaction data—not new chapter-specific specs, task plans, or `chapterN_proof.py` helpers.
- `frontier-audiobook audition ...` is the deliberately small blind voice-selection workflow documented later in this file. Its behavior remains available and unchanged.

Neither workflow deploys AWS resources or uploads manuscript text to S3. Only an explicitly authorized paid render boundary can invoke Nova. Generated plans, transactions, runtime artifacts, and delivered audio remain local under the configured build and delivery roots.

Local Mac Chatterbox/Kokoro audition tooling (not Nova production) lives under
[`tools/kokoro-local/`](tools/kokoro-local/README.md), including batch render and STT glitch checks.

## Reusable production operator workflow

### Authority and prerequisites

The tracked authority is the generic Python subsystem under `audiobook-studio/src/frontier_audiobook/` plus the single strict book configuration at `audiobook-studio/config/production.toml`. Routine production generates immutable plans, independent track transactions, validation evidence, WAVs, and reports. It does not generate or edit chapter-specific operational specs.

The historical `.kiro/specs/chapter-2-audio-proof/` and `.kiro/specs/chapter-3-audio-proof/` trees, the governing `.kiro/specs/The-Final-Frontier-novel/` tree, and every existing Chapter 1/2 narration artifact and proof copy are read-only protected inputs. Preflight records per-file existence, byte count, SHA-256, Git status, and attribution; validation compares hard-protected files individually. Unselected manuscript edits are reported separately as concurrent/unattributed work and are never blamed on this workflow merely because a whole-novel aggregate changed.

Install the already pinned environment from the repository root; this workflow adds no dependency:

```bash
cd audiobook-studio
uv sync --extra dev --python 3.12 --no-editable
cd ..
CLI="audiobook-studio/.venv/bin/frontier-audiobook"
```

The direct pins remain `aws-sdk-bedrock-runtime==0.10.0`, `smithy-http[awscrt]==0.4.4`, and development-only `pytest==9.1.1`, as mirrored by `pyproject.toml`, `requirements/`, and `uv.lock`. A future dependency must be proposed separately with a correctness justification and reviewed exact-version pin; do not add it during routine track work.

### Configuration and publishing handoff

`audiobook-studio/config/production.toml` is strict UTF-8 TOML. Unknown keys, duplicate logical entries, unsafe paths, unknown enum values, and invalid bounds fail before a plan is written. Effective values resolve deterministically in this order:

1. global `[defaults]`;
2. the matching track-kind override;
3. the exact track/chapter override.

The tracked defaults are Tiffany, `amazon.nova-2-sonic-v1:0`, `us-east-1`, profile label `frontier-audiobook`, five target words per segment, exact fidelity under `frontier-word-sequence-v1`, and 24 kHz/16-bit/mono PCM. Every resolved value and its provenance is frozen into the plan.

Chapter tracks come from the restricted-header manuscript chapters. Opening credits, dedication, epigraph, other narratable front matter, and closing credits require a publishing handoff before they can be selected:

1. Publishing approves a dedicated spoken-text file or a named section of a source file.
2. The catalog entry records `source_path`, optional `source_section`, sequence, kind, and `render_once = true`. Use `approved_sha256` when publishing supplies an approved digest.
3. Change `approval_status` to `approved` and `enabled` to `true` only after that handoff. Pending entries remain disabled and contain no invented prose.
4. Planning reads the approved source with no-follow path checks and freezes hashes, counts, and segment metadata—not prose.
5. Any source/section/hash change invalidates the old plan. A special track is one independent catalog item and is never repeated per chapter.

Written-edition title, copyright, layout, typography, and pagination remain publishing-owned. Production consumes only explicitly approved narratable text.

### Stable command reference

Run commands from the repository root with `$CLI` as defined above. The JSON output supplies canonical paths and digests; use the exact emitted values rather than guessing or copying values from a historical spec.

| Command | Purpose and boundary |
|---|---|
| `production plan` | Resolve repeatable `--chapter`, inclusive repeatable `--chapter-range START:END`, and repeatable `--track` selectors into one finite immutable plan. `--plan-id` is optional. No AWS, network, identity, pricing, or model call. |
| `production preflight` | `--dry-run` validates and previews without writing. Full preflight requires `--targeted-checks`, `--identity-evidence`, and `--official-rate-document`, then writes local/protected-inventory and bounded estimate evidence. The command consumes those strict local evidence files and makes no live external or model call. `--required-free-bytes` may impose an additional local capacity floor. |
| `production authorize` | Create one expiring, one-shot authorization for the exact plan/preflight, ordered transactions/tracks/commands, per-track and total call ceilings, estimate, and approved maximum. Requires `--expires-at`, `--max-estimated-pre-tax-usd`, exact `--confirm-plan-sha256`, and `--confirm-paid-scope`. It makes no model call and does not itself permit a retry. |
| `production execute` | **The first and only stable production command capable of launching a model call or incurring a service charge.** It accepts exactly one `--authorization`, revalidates every binding, durably consumes authorization before direct-child launch, and executes tracks sequentially. |
| `production validate` | Deterministically validate definitive native-zero attempt evidence, frozen source/config, active manifest, exact transcript/event/LPCM replay, assembly, usage, Decimal cost, isolation, and sanitization for `--plan`. No model call. |
| `production deliver` | Publish validated WAVs for `--plan` collision-safely: absent destinations are atomically copied, identical destinations are retained, and differing destinations are preserved and blocked. No model call. |
| `production report` | Rebuild the sanitized batch report for `--plan` from independent transaction truth. No model call. |
| `production status` | Reconstruct either `--plan PLAN` or `--book` status from independent ledgers; a missing/stale/corrupt derived index is rebuilt. No model call. |
| `production inspect-resume` | Read one `--transaction` and classify local recovery without identity, pricing, child, network, or model calls. |
| `production resolve` | Apply one explicit local disposition to `--transaction`: `accept-complete-local-artifacts`, `quarantine-invalid-artifacts`, or `abandon-uncertain-attempt`. No disposition starts a child or model call. |

`production preflight` never retrieves identity or rates itself. The three-field identity projection and normalized official-rate document must be produced by the separately governed preflight evidence process. Their collection may involve approved non-model external access; a task that forbids AWS/network access must stop at `--dry-run` and must not fabricate either file.

### Normal single-track example

The following creates and previews a Chapter 4 plan without AWS or model access:

```bash
$CLI production plan --chapter 4 --plan-id chapter-004-review
PLAN="/absolute/path/from/the-plan-json-output/plan.json"
$CLI production preflight --plan "$PLAN" --dry-run
$CLI production status --plan "$PLAN"
```

After the targeted gate and separately permitted evidence collection produce strict local files, full non-model preflight is:

```bash
TARGETED="/absolute/path/to/targeted-checks.json"
IDENTITY="/absolute/path/to/identity-evidence.json"
RATES="/absolute/path/to/normalized-official-rates.json"

$CLI production preflight \
  --plan "$PLAN" \
  --targeted-checks "$TARGETED" \
  --identity-evidence "$IDENTITY" \
  --official-rate-document "$RATES" \
  --required-free-bytes 0

PREFLIGHT="${PLAN%/plan.json}/preflight.json"
```

Do not continue merely because preflight passed. Authorization and execution are separate decisions described below.

### Normal bounded-batch example

A chapter range is inclusive and bounded by `max_tracks_per_plan`. Tracks are de-duplicated, catalog ordered, and independently transacted:

```bash
$CLI production plan --chapter-range 4:8 --plan-id chapters-004-through-008
BATCH_PLAN="/absolute/path/from/the-plan-json-output/plan.json"
$CLI production preflight --plan "$BATCH_PLAN" --dry-run
```

Repeat `--chapter` for an explicit set. Repeat `--track` only for configured, enabled, publishing-approved special tracks; for example, after its handoff is approved:

```bash
$CLI production plan \
  --track opening-credits \
  --chapter-range 4:8 \
  --plan-id opening-and-chapters-004-through-008
```

Single and batch plans use the same schema, state machine, authorization boundary, and per-track ledgers. The batch maximum is a safety bound, not a recommendation to authorize the largest possible scope.

### Exact paid authorization boundary

A spec, selected task, plan, dry run, passing test, preflight, old approval, generic “continue,” environment variable, or existing authorization file is **not** paid authorization. Before invoking `production authorize`, a human operator must freshly review and explicitly approve all of the following together:

- exact plan and preflight SHA-256 values;
- exact ordered track and transaction IDs;
- every direct-child command SHA-256;
- maximum new calls per track and total;
- `Cost_Estimate` and its inputs;
- operator-approved maximum estimated pre-tax USD amount, which must be at least the estimate;
- authorization expiration and one-shot/no-retry semantics.

For agent-driven operation, obtain a fresh interactive confirmation naming this exact plan/authorization immediately before `authorize`; obtain confirmation again before `execute` if execution is not immediate. Never infer consent from this README or from task completion.

Only after that confirmation may the operator substitute exact emitted values here:

```bash
PLAN_SHA256="<exact Frozen_Plan SHA-256>"
EXPIRES_AT="<UTC timestamp such as 2027-01-01T00:00:00Z>"
APPROVED_MAX_USD="<decimal amount at least equal to Cost_Estimate>"

$CLI production authorize \
  --plan "$PLAN" \
  --preflight "$PREFLIGHT" \
  --expires-at "$EXPIRES_AT" \
  --max-estimated-pre-tax-usd "$APPROVED_MAX_USD" \
  --confirm-plan-sha256 "$PLAN_SHA256" \
  --confirm-paid-scope

AUTHORIZATION="/absolute/path/from/the-authorization-json-output.json"
```

`authorize` displays the exact bound scope and creates a local authorization but makes zero model calls. The first paid-capable command is:

```bash
AWS_PROFILE=frontier-audiobook \
$CLI production execute --authorization "$AUTHORIZATION"
```

`execute` is intentionally shown for boundary clarity, not as standing permission to run it. Missing, stale, expired, consumed, mismatched, over-bound, or insufficient authorization stops before child launch. The configured `AWS_PROFILE` label must match the frozen effective configuration; credentials are never placed in the plan or command arguments.

### Transaction states and fail-fast behavior

The normal forward state path is:

```text
discovered -> planned -> preflight-passed -> authorization-required
           -> running -> rendered -> validated -> delivered
```

Blocking paths are explicit:

```text
planned -------------------------------> blocked
authorization-required ----------------> blocked
running -- known nonzero/drift/failure -> blocked
running -- incomplete/ambiguous proof -> charge-uncertain
rendered -- postflight failure --------> blocked
validated -- delivery/isolation issue -> blocked
charge-uncertain -- proven local data -> rendered
charge-uncertain -- quarantine/abandon -> blocked
```

A blocked or launched uncertain transaction never returns to `running` under the same authorization. A conceptual `blocked -> planned` recovery means a **new immutable plan and new transaction**, not mutation of history.

Paid batches run one track at a time in frozen catalog order and stop before the next track on the first nonzero child status, `charge-uncertain`, source/protected-runtime drift, authorization mismatch, call-ceiling exhaustion, exact-fidelity failure, or partial-turn failure. A completed prefix remains complete; the failed track retains its evidence; every later track remains unstarted with zero model calls. Continuing any suffix requires current preflight and a fresh authorization—unused scope in the stopped batch is not standing consent.

### Inspection and manual resolution

Inspect before deciding anything about a failed or interrupted attempt:

```bash
TRANSACTION="/absolute/path/to/transactions/<track-id>/<transaction-id>"
$CLI production inspect-resume --transaction "$TRANSACTION"
```

The read-only classification is one of `nothing-to-resume`, `local-validation-available`, `complete-artifacts-recoverable`, `charge-uncertain-review-required`, or `blocked-new-plan-required`.

If and only if the evidence supports the chosen disposition, run one nonbillable resolution:

```bash
$CLI production resolve --transaction "$TRANSACTION" \
  --disposition accept-complete-local-artifacts

$CLI production resolve --transaction "$TRANSACTION" \
  --disposition quarantine-invalid-artifacts

$CLI production resolve --transaction "$TRANSACTION" \
  --disposition abandon-uncertain-attempt
```

Resolution retains evidence and never resets or retries a model call. Any later paid attempt requires a new transaction, plan, preflight, and authorization. If the retained attempt may have charged, the new authorization flow additionally requires explicit duplicate-charge acknowledgement bound to that attempt digest.

### Validation, delivery, status, and reports

After a definitive native-zero execution, run these separately; none can invoke the model:

```bash
$CLI production validate --plan "$PLAN"
$CLI production deliver --plan "$PLAN"
$CLI production report --plan "$PLAN"
$CLI production status --plan "$PLAN"
$CLI production status --book
```

Validation never estimates missing evidence. A missing/duplicate/malformed manifest, transcript, journal, hash, path, attempt result, native status, WAV property, rate, or isolation input blocks delivery. Listening feedback may be added to a report only as supplemental evidence; it cannot replace deterministic gates.

### Pronunciation lexicon (correct spelling, correct pronunciation)

This workflow sends plain text to Amazon Nova 2 Sonic. No SSML, no phoneme markup, and no service-side pronunciation lexicon is used, so the only way to change how a word is spoken is to change the characters the model receives. Respelling a proper noun in the manuscript is not acceptable, so the respelling lives in the transform between *source text* and *spoken text*.

That seam already exists: `markdown_to_spoken` strips emphasis, so spoken text already differs from source text, and every source snapshot records `normalized_body_sha256` and `spoken_sha256` separately. Deterministic fidelity verification compares the returned transcript against the **spoken** text, so a declared respelling validates normally.

Declare entries in `audiobook-studio/config/production.toml`:

```toml
[[pronunciations]]
written = "Hannah"
spoken = "Haanah"
note = "Open first vowel as in Hawaii; audio-only respelling, never printed"
```

The manuscript keeps the correct spelling; the model receives the respelling. Matching is deliberately strict:

- `written` matches whole words only, never inside a longer word (`Savannah` is untouched).
- Matching is case-sensitive, because these are proper nouns.
- Longer `written` forms are tried first, so a short entry cannot shadow a longer one containing it.
- Substitution is a single pass, so replacement text is never rewritten by another entry.

Entries are part of the production config, so `config_sha256` covers them and changing the lexicon changes the spoken text, its `spoken_sha256`, and therefore the frozen plan. A lexicon edit after planning fails closed at render time rather than silently altering delivered audio.

### Source-currency audit (is the delivered audio still correct?)

Deterministic validation proves audio matched its source *at render time*. It cannot know about a manuscript edit made afterwards. Run the audit at any time to compare every recorded render digest against the live manuscript:

```bash
$CLI audit                 # operator summary
$CLI audit --json          # full record
$CLI audit --skip-unbound  # only artifacts carrying their own render evidence
```

The audit is read-only and never contacts AWS or a model. It exits `0` when every audited artifact is current and `1` when any artifact needs attention, so it works as a pre-publish gate.

Reported statuses:

- `current`: recorded source digest matches the live manuscript and the audio bytes match their delivery digest.
- `stale-source-changed`: the chapter text changed after the audio was rendered. The audio must be re-rendered.
- `audio-modified`: audio bytes no longer match the digest recorded at render time.
- `audio-missing` / `source-missing`: a recorded path is absent from the workspace.
- `source-unreadable`: the chapter no longer parses under the restricted-header contract.

Each pipeline is compared under the convention it actually recorded, because comparing under the wrong one invents false staleness:

- `production` records `source_sha256` as the digest of the whole source file.
- `legacy-narration` records `source_sha256` as the digest of the prose body only, deliberately ignoring restricted-header edits.

WAVs without their own render evidence, such as hand-exported copies under `voice-samples/`, are listed separately. When such a copy is byte-identical to a recorded artifact it inherits that artifact's status; otherwise it is reported as having no matching recorded artifact and cannot be certified.

### Cost labels

Keep these values separate in every review and report:

- `Cost_Estimate`: conservative preflight exposure from call/token ceilings and current official rates. It is an authorization input, not an invoice or absolute account spending control.
- `operator-approved maximum estimated pre-tax USD`: the explicit authorization ceiling. It does not rewrite actual cost after a call.
- `Active_Artifact_Totals`: four-modality tokens from every validated active segment, including reused segments.
- `Current_Execution_Totals`: four-modality tokens only from segments newly rendered in the current attempt; reused segments contribute zero.
- `Computed_Pre_Tax_Service_Cost`: exact journal-derived Decimal service cost, reported separately for active artifacts and current execution.
- `Billing_Confirmation`: separate Cost Explorer/invoice evidence labeled `pending`, `not-performed`, or confirmed with amount/date. Credits, tax, discounts, and invoice rounding are not folded into computed service cost.

If exact computed service cost exceeds the approved estimated maximum, report a blocking budget exception for operator review; never hide it by relabeling estimate, exact cost, or billing confirmation.

### Privacy, generated data, and protected paths

Plans and Evidence_Artifacts contain hashes, counts, strict status fields, paths, and bounded metadata—not prose bodies, segment text, transcript bodies, raw event payloads, credentials, account IDs, ARNs, role/user identifiers, or environment dumps. Identity persistence is limited to profile label, resolution boolean, and UTC timestamp. Required raw transcripts and event journals stay under ignored per-transaction `runtime/` roots.

Normal writes are restricted to the selected plan/transaction roots, rebuildable indexes, and approved delivery destinations. Any workflow-owned write outside that allowlist blocks delivery. Existing Chapter 1/2 build roots matching `audiobook-studio/build/narration/chapter-001-*` and `chapter-002-*`, and proof WAVs matching `voice-samples/chapter-1-*` and `chapter-2-*`, are observed by path/size/SHA-256 and never migrated, renamed, overwritten, or normalized. The historical and governing spec trees listed above are likewise byte-protected.

Generated plans, authorizations, attempts, transcripts, event journals, WAVs, status indexes, and reports belong under ignored build/delivery roots as configured. Do not commit private runtime artifacts, credentials, or generated evidence.

### Chapter 3 pilot instructions (separate authorization required)

The acceptance source is exactly `The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md`. These instructions do not authorize or perform the pilot. Do not run them until Tasks 1–8 and the targeted gate pass, the pilot phase is explicitly selected, and the operation’s AWS/network permissions are separately allowed.

1. **Freeze exactly one track, locally.** Recompute source hashes, counts, spoken hash, segments, and call ceiling from current bytes; never copy those values from the historical Chapter 3 spec.

   ```bash
   # DOCUMENTATION ONLY — do not run during implementation task 8.3.
   $CLI production plan --chapter 3 --plan-id chapter-003-pilot
   PILOT_PLAN="/absolute/path/from-the-plan-json-output/plan.json"
   $CLI production preflight --plan "$PILOT_PLAN" --dry-run
   ```

2. **Complete the separately permitted nonbillable gate.** Produce the targeted-check binding with AWS/model access denied. Only when Task 9.1 separately permits it, obtain the minimal three-field identity projection and current normalized official four-modality rate document, then run full preflight. Full preflight must select only `chapter-003`, inventory every protected file, classify reuse/collisions/capacity, and make zero model calls.
3. **Stop and review.** Present the exact plan/preflight digests, one track/transaction, command hash, maximum calls, `Cost_Estimate`, proposed approved maximum, expiration, targeted result, and every blocker. Any failed or missing gate stops here.
4. **Obtain fresh Chapter 3-specific consent.** Immediately before authorization, ask the operator to authorize exactly one paid Chapter 3 pilot transaction under the displayed digests, call ceiling, expiration, and approved maximum. A skipped, stale, generic, or mismatched response is a decline. Only an affirmative exact response permits `production authorize` for this one pilot.
5. **Execute at most once.** After a second immediate scope check, invoke `production execute` with that authorization. On nonzero native status, charge uncertainty, drift, exhausted bound, fidelity failure, or partial turn, retain evidence and stop—no retry, reset, delivery, second authorization, or next track.
6. **Accept only after deterministic success.** Native status `0` is necessary but insufficient. Run `production validate`, `production deliver`, `production report`, and final protected-file comparison. Accept this reusable workflow for future normal tracks only when every Delivery_Gate input passes. Keep exact service cost, billing confirmation, and supplemental listening feedback separately labeled.

No Chapter 3 command, AWS access, narration-service access, production child, model call, paid call, delivery, or pilot execution is part of this documentation task.

## Blind voice audition

The audition workflow chooses the female narrator before chapter-scale production. Its only network/billable operation is the explicitly confirmed `audition render` phase, which intentionally fails closed outside macOS and Linux.

## Candidates and excerpts

The configured Nova 2 Sonic candidates are exactly `tiffany` (US), `amy` (UK), `olivia` (Australia), and `kiara` (Indian English). AWS lists these as its current feminine-sounding English voices in the [Nova 2 Sonic language-support table](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-language-support.html). Configuration loading rejects a missing, extra, or duplicate candidate so every audition remains a complete four-voice comparison.

Each candidate reads the same four short, source-anchored excerpts:

1. Chapter 5 — technical authority and analytical cadence.
2. Chapter 73 — consent, procedural precision, and dialogue.
3. Chapter 118 — intimate grief without theatrical excess.
4. Chapter 124 — quiet refusal and domestic action.

Only the normalized Prose Body after the restricted chapter header can be selected. The plan records SHA-256 hashes for the chapter body, source excerpt, spoken transform, configuration, and system prompt. A changed chapter or configuration invalidates the plan.

Every billing manifest is a strict schema-v2 document at the canonical configured `output_root/<audition-id>/plan.json` path. It must contain the unique, exact 4 excerpts × 4 voices matrix and only derived artifact paths. Copied, relocated, duplicate-key, malformed, stale, or manually expanded plans are rejected before the billable boundary. Aggregate plan status is derived from call state rather than trusted from an edit.

## Safety model

- `plan`, `status`, `package`, `reconcile`, `reveal`, and `render --dry-run` never invoke AWS.
- A real call requires `render --confirm-paid-render` at both the CLI and internal billable boundaries.
- Paid rendering is supported only on macOS and Linux because the crash-safety contract requires POSIX directory durability. Offline planning, inspection, packaging, and imports remain non-billable, but other operating systems fail before SDK entry if paid rendering is requested.
- `temperature` is fixed at `0.0`; audio is 24 kHz, signed 16-bit, mono LPCM wrapped as WAV.
- Audio remains under ignored `audiobook-studio/build/` until Nova's FINAL transcript has the exact expected word sequence under `frontier-word-sequence-v1` normalization.
- A mismatch stops immediately with exit `1`; it is never retried automatically.
- Immediately before SDK entry, the call is durably marked `invoking` with an attempt ID, canonical UUID `prompt_name`, and deterministic `request_binding_sha256`. The binding covers the model, region, voice, excerpt, spoken/system hashes, audio format, and inference settings. Nova output must carry that persisted prompt identity.
- SDK work runs in a spawned child process. The parent enforces the stream deadline plus a bounded cleanup grace, then terminates and, if necessary, kills the worker so cancellation-resistant SDK work cannot hang the CLI indefinitely.
- A timeout or crash becomes charge-uncertain and is never retried automatically.
- Missing, malformed, stale, or unauthorized input exits `2`; success exits `0`.
- Packaging replays AWS's documented [Nova output event sequence](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-output-events.html), validates correlated lifecycle IDs and the persisted `prompt_name`, reconstructs FINAL text and LPCM, and binds them byte-for-byte to the transcript and WAV.
- Reconciliation persists a `reconciliation_in_progress` journal before moving uncertain evidence. An interrupted reconciliation resumes that journal; source hashes must still match before recovery or a deliberate reset.
- Blind-key schema and labels are strict; package creation is serialized and privately hash-binds Voice A–D clips to one winning mapping.
- Voice identities stay in ignored `blind-key.json`; the listener package contains only Voice A–D.
- No AWS credentials, account IDs, audio, transcripts, or generated plans belong in Git.

Nova 2 Sonic is a conversational model, and the AWS SDK for Python used for bidirectional streaming is still a pre-1.0 developer-preview dependency. Treat this workflow as an evaluation gate, not a production narration guarantee.

## 1. Verify credits before rendering

In **AWS Billing and Cost Management → Credits**, check the remaining amount and expiration. AWS documents the Credits page and application behavior in [Applying AWS credits](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/useconsolidatedbilling-credits.html). Open the terms for the specific credit and verify that Amazon Bedrock usage is applicable and not excluded. Eligibility depends on the credit grant; this repository cannot determine it.

Do not proceed merely because a balance exists. If the grant does not cover Bedrock, the account's ordinary payment method will be charged.

## 2. Establish Bedrock access

The audition is pinned to:

```text
Region:   us-east-1
Model ID: amazon.nova-2-sonic-v1:0
API:      InvokeModelWithBidirectionalStream
```

Nova 2 Sonic is currently listed for `us-east-1`, `us-west-2`, `eu-north-1`, and `ap-northeast-1` on its [Bedrock model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-sonic.html). This project uses `us-east-1` consistently.

Bedrock model access is generally enabled by default when the principal has the required permissions; see [Request access to models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access). An account administrator may still need to resolve model-access or organization-policy restrictions in the Bedrock console.

The runtime identity needs only `bedrock:InvokeModel` for the Nova 2 Sonic foundation-model ARN. AWS's [bidirectional API reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithBidirectionalStream.html) identifies `bedrock:InvokeModel` as the required permission. A least-privilege example is provided at:

```text
audiobook-studio/iam/audition-invoke-policy.json
```

Have an AWS administrator attach equivalent permission to the short-lived role/profile used for this audition. Do not create or attach IAM policies from this workflow.

## 3. Configure short-lived credentials

AWS recommends IAM Identity Center/temporary credentials rather than long-lived access keys. The official setup is documented in [Configuring IAM Identity Center authentication with the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html).

Example profile setup:

```bash
aws configure sso --profile frontier-audiobook
aws sso login --profile frontier-audiobook
AWS_PROFILE=frontier-audiobook aws sts get-caller-identity
```

The final command is a non-model identity check; verify that the returned account and role are the intended credit-bearing account. Never paste credentials into TOML, Markdown, shell scripts, or chat.

## 4. Install the pinned local environment

From the repository root:

```bash
cd audiobook-studio
uv sync --extra dev --python 3.12 --no-editable
```

`uv.lock` fixes the complete transitive environment. `.venv/` is local and ignored.

Run the offline safety suite:

```bash
.venv/bin/pytest -q
```

This revision has 16 tests. They scrub AWS credential/profile environment variables, set `FRONTIER_AUDIOBOOK_DISABLE_AWS=1`, exercise the billing gates, strict manifests, event/WAV tamper checks, process deadline, journal recovery, and concurrent blind packaging, then build and smoke-test the installed wheel outside the source tree. They make no AWS request.

## 5. Create a fresh local plan

No AWS call occurs:

```bash
.venv/bin/frontier-audiobook audition plan
```

The command creates a new schema-v2 manifest at `audiobook-studio/build/auditions/<audition-id>/plan.json` and prints its absolute path. Use that exact path; moving or copying the manifest intentionally invalidates it. Set it for the following examples:

```bash
PLAN="/absolute/path/printed/by/the/plan/command.json"
```

Inspect the 16 calls without credentials or network access:

```bash
.venv/bin/frontier-audiobook audition render \
  --plan "$PLAN" \
  --dry-run
```

The output must say `"billable_calls_made": 0` and list four excerpts for each of the four voices.

## 6. Make one paid pilot call

Only continue on macOS or Linux, and only after confirming credits, account identity, and permission. Render exactly one excerpt with one voice:

```bash
AWS_PROFILE=frontier-audiobook \
.venv/bin/frontier-audiobook audition render \
  --plan "$PLAN" \
  --voice tiffany \
  --excerpt technical-authority \
  --confirm-paid-render
```

This is the first command capable of charging the AWS account. Before SDK entry it persists the invocation state and request identity described above. It then writes a quarantined WAV, FINAL transcript, raw event log, and verification result under the plan's ignored build directory. If fidelity fails, stop and inspect rather than retrying.

Check progress at any time without AWS access:

```bash
.venv/bin/frontier-audiobook audition status --plan "$PLAN"
```

If a process ends after invocation begins but before complete artifacts are durably verified, the call remains `invoking` or becomes `charge_uncertain`. Re-running `render` will **not** invoke Bedrock again. First inspect the status and any files under `uncertain-evidence/`. Complete valid artifacts are recovered locally. Only when you deliberately accept the possibility of a duplicate charge may you reset one call:

```bash
.venv/bin/frontier-audiobook audition reconcile \
  --plan "$PLAN" \
  --call-id technical-authority--tiffany \
  --confirm-possible-duplicate-charge
```

`reconcile` itself never calls AWS. It first journals its intended evidence moves in `plan.json`, then recovers a complete valid result or quarantines partial/invalid evidence before returning the call to `pending`. If interrupted, the next reconciliation resumes the same journal. A later render still requires `--confirm-paid-render`.

## 7. Render the remaining audition clips

If the pilot is correct, invoke the remaining pending calls sequentially:

```bash
AWS_PROFILE=frontier-audiobook \
.venv/bin/frontier-audiobook audition render \
  --plan "$PLAN" \
  --confirm-paid-render
```

Already verified calls are revalidated and skipped. A crash after complete artifacts are written is recovered locally instead of billed again. Partial or mismatched artifacts block overwrite.

To limit exposure further, render one voice at a time with `--voice amy`, `--voice olivia`, or `--voice kiara`.

## 8. Build and hear the blind package

After all 16 clips pass:

```bash
.venv/bin/frontier-audiobook audition package --plan "$PLAN"
```

The command prints the listener-folder path under `audiobook-studio/dist/auditions/`. On macOS:

```bash
open "/path/printed/by/package"
```

Do not inspect the matching build directory or `blind-key.json` while scoring. Fill in `scorecard.csv`, using the weights in `LISTENER-GUIDE.txt`. Listen through headphones and ordinary speakers, then repeat the ranking the following day.

After scoring is complete:

```bash
.venv/bin/frontier-audiobook audition reveal \
  --plan "$PLAN" \
  --confirm-scoring-complete
```

The result maps Voice A–D to Tiffany, Amy, Olivia, and Kiara. The top two should then receive a separate 8–12 minute stamina audition before a production voice is locked.

## Generated layout

```text
audiobook-studio/build/auditions/<audition-id>/
├── plan.json               canonical schema-v2 manifest and reconciliation journal
├── inputs/                 exact spoken inputs
├── renders/<voice>/        quarantined WAV files
├── transcripts/<voice>/    Nova FINAL transcripts
├── events/<voice>/         raw output events
├── verification/<voice>/   exact-comparison evidence
├── uncertain-evidence/     retained artifacts from explicit reconciliation
├── package-binding.json    private key-to-clip hash binding
└── blind-key.json          private until scoring is complete

audiobook-studio/dist/auditions/<audition-id>/
├── clips/voice-a...voice-d/
├── scorecard.csv
└── LISTENER-GUIDE.txt
```

Both roots are ignored. No S3 bucket, CloudFormation stack, IAM policy, or other AWS resource is deployed by these commands.

## Attribution

Technical facts above are based on the linked AWS documentation. Content was rephrased for compliance with licensing restrictions.
