# The Final Frontier — blind Nova 2 Sonic voice audition

This directory contains a deliberately small audition workflow for choosing the female narrator before any chapter-scale audiobook generation. It does **not** deploy AWS resources, upload manuscript text to S3, or render full chapters. The only network/billable operation is the explicitly confirmed `audition render` phase, which intentionally fails closed outside macOS and Linux.

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
- Audio remains under ignored `.audiobook/build/` until Nova's FINAL transcript has the exact expected word sequence under `frontier-word-sequence-v1` normalization.
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
.audiobook/iam/audition-invoke-policy.json
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
cd .audiobook
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

The command creates a new schema-v2 manifest at `.audiobook/build/auditions/<audition-id>/plan.json` and prints its absolute path. Use that exact path; moving or copying the manifest intentionally invalidates it. Set it for the following examples:

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

The command prints the listener-folder path under `.audiobook/dist/auditions/`. On macOS:

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
.audiobook/build/auditions/<audition-id>/
├── plan.json               canonical schema-v2 manifest and reconciliation journal
├── inputs/                 exact spoken inputs
├── renders/<voice>/        quarantined WAV files
├── transcripts/<voice>/    Nova FINAL transcripts
├── events/<voice>/         raw output events
├── verification/<voice>/   exact-comparison evidence
├── uncertain-evidence/     retained artifacts from explicit reconciliation
├── package-binding.json    private key-to-clip hash binding
└── blind-key.json          private until scoring is complete

.audiobook/dist/auditions/<audition-id>/
├── clips/voice-a...voice-d/
├── scorecard.csv
└── LISTENER-GUIDE.txt
```

Both roots are ignored. No S3 bucket, CloudFormation stack, IAM policy, or other AWS resource is deployed by these commands.

## Attribution

Technical facts above are based on the linked AWS documentation. Content was rephrased for compliance with licensing restrictions.
