"""Command-line entry point for audition and reusable audiobook production."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from . import EXIT_FIDELITY_MISMATCH, EXIT_INCOMPLETE, EXIT_PASS
from .audition import (
    create_plan,
    dry_run_render,
    load_plan,
    package_blind_audition,
    plan_status,
    reconcile_uncertain_call,
    render_plan,
    revalidate_plan,
    reveal_blind_key,
)
from .config import load_audition_config
from .currency import audit_currency, format_currency_table
from .errors import AudiobookError, InputError
from .narrate import MAX_SEGMENT_WORDS, narrate_chapter, plan_narration
from .production_worker import run_production_worker
from .util import (
    find_workspace_root,
    json_loads_strict,
    read_bytes_nofollow,
    resolve_inside,
    sha256_bytes,
    workspace_relative,
)


def _add_production_parser(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    production = commands.add_parser(
        "production",
        help="Run the reusable, transaction-based audiobook production workflow",
    )
    phases = production.add_subparsers(dest="phase", required=True)

    plan = phases.add_parser("plan", help="Freeze a finite production scope; never calls AWS")
    plan.add_argument(
        "--config",
        type=Path,
        help="Production TOML; defaults to .audiobook/config/production.toml",
    )
    plan.add_argument("--chapter", type=int, action="append", help="Select one chapter; repeatable")
    plan.add_argument(
        "--chapter-range",
        action="append",
        help="Select an inclusive START:END chapter range; repeatable",
    )
    plan.add_argument("--track", action="append", help="Select a configured Track ID; repeatable")
    plan.add_argument("--plan-id", help="Optional immutable lowercase plan identifier")

    preflight = phases.add_parser(
        "preflight",
        help="Run local bounded checks from explicit non-model evidence",
    )
    preflight.add_argument("--plan", type=Path, required=True)
    preflight.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate scope and show the nonbillable flow without writing evidence",
    )
    preflight.add_argument(
        "--targeted-checks",
        type=Path,
        help="Strict local Targeted_Checks result JSON produced with AWS/model access denied",
    )
    preflight.add_argument(
        "--identity-evidence",
        type=Path,
        help="Strict local three-field identity projection JSON; no live identity call is made",
    )
    preflight.add_argument(
        "--official-rate-document",
        type=Path,
        help="Strict locally retrieved normalized official-rate JSON",
    )
    preflight.add_argument(
        "--required-free-bytes",
        type=int,
        help="Optional explicit local capacity requirement",
    )

    authorize = phases.add_parser(
        "authorize",
        help="Create one exact, expiring, one-shot paid authorization; never calls a model",
    )
    authorize.add_argument("--plan", type=Path, required=True)
    authorize.add_argument("--preflight", type=Path, required=True)
    authorize.add_argument("--authorization-id")
    authorize.add_argument("--expires-at", required=True)
    authorize.add_argument("--max-estimated-pre-tax-usd", required=True)
    authorize.add_argument("--confirm-plan-sha256", required=True)
    authorize.add_argument("--confirm-paid-scope", action="store_true", required=True)

    execute = phases.add_parser(
        "execute",
        help="Execute exactly one validated authorization through direct children",
    )
    execute.add_argument("--authorization", type=Path, required=True)

    validate = phases.add_parser(
        "validate",
        help="Run deterministic local postflight validation; never calls a model",
    )
    validate.add_argument("--plan", type=Path, required=True)

    deliver = phases.add_parser(
        "deliver",
        help="Publish validated Track WAVs collision-safely; never calls a model",
    )
    deliver.add_argument("--plan", type=Path, required=True)

    report = phases.add_parser(
        "report",
        help="Rebuild the sanitized batch report from independent transaction truth",
    )
    report.add_argument("--plan", type=Path, required=True)

    status = phases.add_parser(
        "status",
        help="Reconstruct plan or book status from independent transaction ledgers",
    )
    status_scope = status.add_mutually_exclusive_group(required=True)
    status_scope.add_argument("--plan", type=Path)
    status_scope.add_argument("--book", action="store_true")

    inspect_resume_parser = phases.add_parser(
        "inspect-resume",
        help="Classify local recovery paths without an external call",
    )
    inspect_resume_parser.add_argument("--transaction", type=Path, required=True)

    resolve = phases.add_parser(
        "resolve",
        help="Apply an explicit nonbillable disposition to uncertain local evidence",
    )
    resolve.add_argument("--transaction", type=Path, required=True)
    resolve.add_argument(
        "--disposition",
        required=True,
        choices=(
            "accept-complete-local-artifacts",
            "quarantine-invalid-artifacts",
            "abandon-uncertain-attempt",
        ),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frontier-audiobook",
        description="Guarded Amazon Nova 2 Sonic audiobook voice audition and production",
    )
    parser.add_argument("--workspace-root", type=Path, help="Repository root (normally auto-detected)")
    commands = parser.add_subparsers(dest="command", required=True)
    audition = commands.add_parser("audition", help="Plan, render, package, and reveal a blind voice audition")
    phases = audition.add_subparsers(dest="phase", required=True)

    plan = phases.add_parser("plan", help="Extract source-bound excerpts and create a local plan; never calls AWS")
    plan.add_argument("--config", type=Path, help="Audition TOML; defaults to .audiobook/config/audition.toml")
    plan.add_argument("--audition-id", help="Optional safe run identifier")

    render = phases.add_parser("render", help="Dry-run or execute the planned Bedrock calls")
    render.add_argument("--plan", type=Path, required=True)
    render.add_argument("--voice", action="append", help="Render only this configured voice; repeatable")
    render.add_argument("--excerpt", action="append", help="Render only this excerpt ID; repeatable")
    render.add_argument("--dry-run", action="store_true", help="Validate and list calls without SDK import or AWS access")
    render.add_argument(
        "--confirm-paid-render",
        action="store_true",
        help="Required explicit acknowledgement before any Bedrock model invocation",
    )
    render.add_argument(
        "--accept-verbatim-prefix",
        action="store_true",
        help=(
            "Keep a render when Nova's FINAL transcript is a verbatim in-order prefix of the "
            "excerpt and the audio is long enough to plausibly contain all of it. Nova's FINAL "
            "transcript stream lags its audio, so exact coverage is often unavailable."
        ),
    )

    reconcile = phases.add_parser(
        "reconcile",
        help="Explicitly recover or reset one charge-uncertain call; never calls AWS",
    )
    reconcile.add_argument("--plan", type=Path, required=True)
    reconcile.add_argument("--call-id", required=True)
    reconcile.add_argument(
        "--confirm-possible-duplicate-charge",
        action="store_true",
        required=True,
        help="Acknowledge that a reset may permit a second billable invocation",
    )

    narrate = phases.add_parser("narrate", help="Narrate a whole chapter in short verified segments")
    narrate.add_argument("--chapter", type=int, required=True)
    narrate.add_argument("--voice", default="tiffany")
    narrate.add_argument("--max-words", type=int, default=MAX_SEGMENT_WORDS)
    narrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the segmentation and call count without SDK import or AWS access",
    )
    narrate.add_argument("--confirm-paid-render", action="store_true")
    narrate.add_argument("--accept-verbatim-prefix", action="store_true")

    revalidate = phases.add_parser(
        "revalidate",
        help="Re-apply the fidelity policy to existing artifacts without any Bedrock call",
    )
    revalidate.add_argument("--plan", type=Path, required=True)
    revalidate.add_argument("--voice", action="append")
    revalidate.add_argument("--excerpt", action="append")
    revalidate.add_argument(
        "--accept-verbatim-prefix",
        action="store_true",
        help="Accept a verbatim in-order prefix when the audio is long enough for the whole excerpt",
    )

    package = phases.add_parser("package", help="Create an anonymous listener folder after every clip passes")
    package.add_argument("--plan", type=Path, required=True)
    package.add_argument(
        "--accept-verbatim-prefix",
        action="store_true",
        help="Apply the same explicit verbatim-prefix acceptance policy used during render",
    )

    status = phases.add_parser("status", help="Show plan state and call counts")
    status.add_argument("--plan", type=Path, required=True)

    reveal = phases.add_parser("reveal", help="Reveal the voice mapping only after blind scoring")
    reveal.add_argument("--plan", type=Path, required=True)
    reveal.add_argument("--confirm-scoring-complete", action="store_true", required=True)

    _add_production_parser(commands)

    audit = commands.add_parser(
        "audit",
        help="Verify delivered chapter audio still matches the current manuscript; never calls AWS",
    )
    audit.add_argument(
        "--json",
        action="store_true",
        help="Emit the full audit record as JSON instead of the operator summary",
    )
    audit.add_argument(
        "--skip-unbound",
        action="store_true",
        help="Audit only artifacts that carry their own render evidence",
    )

    worker = commands.add_parser("_production-worker", help=argparse.SUPPRESS)
    worker.add_argument("--plan", type=Path, required=True)
    worker.add_argument("--transaction", required=True)
    worker.add_argument("--track", required=True)
    return parser


def _workspace_root(value: Path | None) -> Path:
    if value is not None:
        root = value.expanduser().resolve()
        config_root = root / ".audiobook" / "config"
        if not (
            (config_root / "audition.toml").is_file()
            or (config_root / "production.toml").is_file()
        ):
            raise InputError(f"Not a frontier-book workspace root: {root}")
        return root

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        config_root = candidate / ".audiobook" / "config"
        if (
            (config_root / "audition.toml").is_file()
            or (config_root / "production.toml").is_file()
        ):
            return candidate
    return find_workspace_root(current)


def _plan_path(value: Path) -> Path:
    return value.expanduser().resolve()


def _production_path(workspace: Path, value: Path) -> Path:
    candidate = value.expanduser()
    if not candidate.is_absolute():
        return resolve_inside(workspace, candidate.as_posix())
    absolute = candidate.resolve()
    workspace_relative(workspace, absolute)
    return absolute


def _production_config_path(workspace: Path, value: Path | None = None) -> Path:
    return (
        _production_path(workspace, value)
        if value is not None
        else resolve_inside(workspace, ".audiobook/config/production.toml")
    )


def _print_json(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    raw = read_bytes_nofollow(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"{label} is not strict UTF-8") from exc
    value = json_loads_strict(text, label)
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise InputError(
            f"{label} fields are invalid; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _require_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _load_targeted_check_binding(workspace: Path, supplied_path: Path):
    from .production_preflight import bind_targeted_check_result

    path = _production_path(workspace, supplied_path)
    value = _load_json_object(path, "Targeted_Checks result")
    _exact_keys(
        value,
        {
            "schema_version",
            "command_sha256",
            "return_code",
            "aws_access_disabled",
            "model_access_disabled",
        },
        "Targeted_Checks result",
    )
    if value["schema_version"] != 1:
        raise InputError("Targeted_Checks result schema_version must be integer 1")
    return_code = value["return_code"]
    if type(return_code) is not int:
        raise InputError("Targeted_Checks return_code must be an integer")
    for name in ("aws_access_disabled", "model_access_disabled"):
        if type(value[name]) is not bool:
            raise InputError(f"Targeted_Checks {name} must be a boolean")
    return bind_targeted_check_result(
        workspace,
        workspace_relative(workspace, path),
        command_sha256=_require_sha256(
            value["command_sha256"], "Targeted_Checks command_sha256"
        ),
        return_code=return_code,
        aws_access_disabled=value["aws_access_disabled"],
        model_access_disabled=value["model_access_disabled"],
    )


def _load_identity_projection(workspace: Path, supplied_path: Path) -> tuple[str, dict[str, bool]]:
    path = _production_path(workspace, supplied_path)
    value = _load_json_object(path, "identity projection")
    _exact_keys(value, {"schema_version", "checked_at_utc", "profiles"}, "identity projection")
    if value["schema_version"] != 1:
        raise InputError("identity projection schema_version must be integer 1")
    checked_at = value["checked_at_utc"]
    if not isinstance(checked_at, str) or not checked_at.endswith("Z"):
        raise InputError("identity projection checked_at_utc must be a UTC timestamp")
    profiles = value["profiles"]
    if not isinstance(profiles, list) or not profiles:
        raise InputError("identity projection profiles must be a nonempty array")
    result: dict[str, bool] = {}
    for index, item in enumerate(profiles):
        if not isinstance(item, dict):
            raise InputError(f"identity projection profiles[{index}] must be an object")
        _exact_keys(
            item,
            {"profile_label", "resolved", "checked_at_utc"},
            f"identity projection profiles[{index}]",
        )
        profile = item["profile_label"]
        if not isinstance(profile, str) or not profile or profile != profile.strip():
            raise InputError("identity projection profile_label must be nonblank")
        if profile in result:
            raise InputError("identity projection profile labels must be unique")
        if type(item["resolved"]) is not bool:
            raise InputError("identity projection resolved must be a boolean")
        if item["checked_at_utc"] != checked_at:
            raise InputError("identity projection timestamps must match checked_at_utc")
        result[profile] = item["resolved"]
    return checked_at, result


def _load_production_context(workspace: Path, supplied_plan: Path):
    from .production import load_production_plan
    from .production_config import load_production_config

    plan_path = _production_path(workspace, supplied_plan)
    plan = load_production_plan(plan_path)
    config_path = resolve_inside(workspace, plan.config_path)
    if sha256_bytes(read_bytes_nofollow(config_path)) != plan.config_sha256:
        raise InputError("Production configuration drifted from Frozen_Plan")
    config = load_production_config(config_path)
    if config.book_id != plan.book_id:
        raise InputError("Production configuration book_id differs from Frozen_Plan")
    return plan_path, plan, config


def _transaction_store(workspace: Path, config):
    from .production_transactions import TransactionStore

    book_root = resolve_inside(
        workspace,
        (PurePosixPath(config.build_root) / config.book_id).as_posix(),
    )
    return TransactionStore(book_root, config.book_id)


def _load_preflight_records(workspace: Path, plan_path: Path, supplied_preflight: Path):
    from .production_models import StrictRecordCodec
    from .production_preflight import BoundedPreflightEstimateResult, LocalPreflightResult

    preflight_path = _production_path(workspace, supplied_preflight)
    if preflight_path.parent != plan_path.parent:
        raise InputError("Preflight evidence must remain beside its exact Frozen_Plan")
    local_path = preflight_path.with_name("local-preflight.json")
    local = StrictRecordCodec(LocalPreflightResult).load(local_path)
    bounded = StrictRecordCodec(BoundedPreflightEstimateResult).load(preflight_path)
    return local_path, preflight_path, local, bounded


def _preflight_paths(plan_path: Path) -> tuple[Path, Path]:
    return plan_path.with_name("local-preflight.json"), plan_path.with_name("preflight.json")


def _run_production_plan(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production import ProductionSelectors, create_production_plan, load_production_plan
    from .production_models import FrozenBatchPlan, StrictRecordCodec

    config_path = _production_config_path(workspace, arguments.config)
    selectors = ProductionSelectors.from_cli(
        chapters=arguments.chapter,
        chapter_ranges=arguments.chapter_range,
        tracks=arguments.track,
    )
    plan_path = create_production_plan(
        config_path,
        selectors,
        plan_id=arguments.plan_id,
        workspace_root=workspace,
    )
    plan = load_production_plan(plan_path)
    _print_json(
        {
            "billable_calls_made": 0,
            "book_id": plan.book_id,
            "external_calls_made": 0,
            "operation": "production-plan",
            "plan": workspace_relative(workspace, plan_path),
            "plan_id": plan.plan_id,
            "plan_sha256": StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            "schema_version": plan.schema_version,
            "tracks": [
                {
                    "maximum_new_calls": track.maximum_new_calls,
                    "sequence": track.sequence,
                    "track_id": track.track_id,
                    "transaction_id": track.transaction_id,
                }
                for track in plan.tracks
            ],
        }
    )
    return EXIT_PASS


def _run_production_preflight(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_config import build_ordered_track_catalog
    from .production_delivery import write_immutable_evidence
    from .production_models import FrozenBatchPlan, StrictRecordCodec, TransactionState, record_to_data
    from .production_preflight import (
        BoundedPreflightEstimateResult,
        LocalPreflightResult,
        run_bounded_identity_rate_preflight,
        run_local_preflight,
    )

    plan_path, plan, config = _load_production_context(workspace, arguments.plan)
    catalog = build_ordered_track_catalog(config, workspace)
    local_path, preflight_path = _preflight_paths(plan_path)
    if arguments.dry_run:
        _print_json(
            {
                "billable_calls_made": 0,
                "external_calls_made": 0,
                "model_calls_made": 0,
                "operation": "production-preflight-dry-run",
                "plan": workspace_relative(workspace, plan_path),
                "plan_sha256": StrictRecordCodec(FrozenBatchPlan).sha256(plan),
                "schema_version": plan.schema_version,
                "selected_track_ids": [track.track_id for track in plan.tracks],
                "would_write": [
                    workspace_relative(workspace, local_path),
                    workspace_relative(workspace, preflight_path),
                ],
            }
        )
        return EXIT_PASS

    missing = [
        option
        for option, value in (
            ("--targeted-checks", arguments.targeted_checks),
            ("--identity-evidence", arguments.identity_evidence),
            ("--official-rate-document", arguments.official_rate_document),
        )
        if value is None
    ]
    if missing:
        raise InputError(
            f"Full preflight requires {', '.join(missing)}; use --dry-run for a no-write preview"
        )
    if arguments.required_free_bytes is not None and arguments.required_free_bytes < 0:
        raise InputError("--required-free-bytes must be nonnegative")

    targeted = _load_targeted_check_binding(workspace, arguments.targeted_checks)
    local = run_local_preflight(
        workspace,
        config,
        catalog,
        plan,
        targeted,
        required_free_bytes=arguments.required_free_bytes,
    )
    local_codec = StrictRecordCodec(LocalPreflightResult)
    write_immutable_evidence(local_path, local_codec.dump_bytes(local))
    if not local.passed:
        _print_json(
            {
                "billable_calls_made": 0,
                "blocking_categories": list(local.blocking_categories),
                "external_calls_made": 0,
                "local_preflight": workspace_relative(workspace, local_path),
                "model_calls_made": 0,
                "operation": "production-preflight",
                "passed": False,
                "schema_version": 1,
            }
        )
        return EXIT_INCOMPLETE

    checked_at, identity_by_profile = _load_identity_projection(
        workspace, arguments.identity_evidence
    )

    def identity_call(profile: str) -> object:
        return {"resolved": True} if identity_by_profile.get(profile) is True else {}

    rate_path = _production_path(workspace, arguments.official_rate_document)
    bounded = run_bounded_identity_rate_preflight(
        config,
        plan,
        local,
        identity_call=identity_call,
        official_rate_document=read_bytes_nofollow(rate_path),
        checked_at_utc=checked_at,
    )
    bounded_codec = StrictRecordCodec(BoundedPreflightEstimateResult)
    write_immutable_evidence(preflight_path, bounded_codec.dump_bytes(bounded))
    if bounded.passed:
        store = _transaction_store(workspace, config)
        store.materialize_plan(plan)
        for track in plan.tracks:
            store.append_transition(
                track.track_id,
                track.transaction_id,
                operation_id="production-preflight-passed",
                event_type="preflight-passed",
                state_after=TransactionState.PREFLIGHT_PASSED,
                details={"preflight_sha256": bounded.canonical_sha256},
            )
            store.append_transition(
                track.track_id,
                track.transaction_id,
                operation_id="production-authorization-required",
                event_type="authorization-required",
                state_after=TransactionState.AUTHORIZATION_REQUIRED,
                details={"preflight_sha256": bounded.canonical_sha256},
            )

    _print_json(
        {
            "billable_calls_made": 0,
            "blocking_categories": list(bounded.blocking_categories),
            "estimate": record_to_data(bounded.estimate),
            "external_calls_made": 0,
            "local_preflight": workspace_relative(workspace, local_path),
            "model_calls_made": 0,
            "operation": "production-preflight",
            "passed": bounded.passed,
            "preflight": workspace_relative(workspace, preflight_path),
            "preflight_sha256": bounded.canonical_sha256,
            "schema_version": 1,
        }
    )
    return EXIT_PASS if bounded.passed else EXIT_INCOMPLETE


def _run_production_authorize(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_authorization import (
        AuthorizationDisplay,
        ExactAuthorizationConfirmation,
        create_paid_authorization_file,
    )
    from .production_models import (
        AuthorizationDecision,
        FrozenBatchPlan,
        PaidAuthorization,
        StrictRecordCodec,
        record_to_data,
    )

    plan_path, plan, config = _load_production_context(workspace, arguments.plan)
    _local_path, preflight_path, local, bounded = _load_preflight_records(
        workspace, plan_path, arguments.preflight
    )
    plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(plan)
    if arguments.confirm_plan_sha256 != plan_sha256:
        raise InputError("--confirm-plan-sha256 does not match the exact Frozen_Plan")
    if not arguments.confirm_paid_scope:
        raise InputError("Exact paid scope was not confirmed")

    authorization_id = arguments.authorization_id or f"authorization-{secrets.token_hex(12)}"
    authorization_path = plan_path.parent / "authorizations" / f"{authorization_id}.json"

    def confirmation_provider(display: AuthorizationDisplay) -> ExactAuthorizationConfirmation:
        print(
            json.dumps(
                {"authorization_scope": record_to_data(display)},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
            flush=True,
        )
        return ExactAuthorizationConfirmation(
            schema_version=1,
            display_sha256=display.canonical_sha256,
            challenge=display.confirmation_challenge,
            decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
        )

    authorization = create_paid_authorization_file(
        authorization_path,
        config,
        plan,
        local,
        bounded,
        workspace_root=workspace,
        authorization_id=authorization_id,
        operator_approved_max_estimated_pre_tax_usd=(
            arguments.max_estimated_pre_tax_usd
        ),
        expires_at_utc=arguments.expires_at,
        confirmation_provider=confirmation_provider,
    )
    _print_json(
        {
            "authorization": workspace_relative(workspace, authorization_path),
            "authorization_sha256": StrictRecordCodec(PaidAuthorization).sha256(
                authorization
            ),
            "billable_calls_made": 0,
            "exact_track_ids": list(authorization.exact_track_ids),
            "model_calls_made": 0,
            "operation": "production-authorize",
            "plan_sha256": plan_sha256,
            "preflight": workspace_relative(workspace, preflight_path),
            "schema_version": authorization.schema_version,
        }
    )
    return EXIT_PASS


def _authorization_layout(workspace: Path, supplied_authorization: Path):
    from .production_authorization import load_paid_authorization

    authorization_path = _production_path(workspace, supplied_authorization)
    if authorization_path.parent.name != "authorizations":
        raise InputError("Authorization artifact is outside the generic plan authorization root")
    plan_path = authorization_path.parent.parent / "plan.json"
    preflight_path = plan_path.with_name("preflight.json")
    authorization = load_paid_authorization(authorization_path)
    return authorization_path, plan_path, preflight_path, authorization


def _run_production_execute(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_authorization import (
        build_authorization_start_request,
        validate_paid_authorization_start,
    )
    from .production_batch import execute_authorized_batch
    from .production_models import record_to_data

    authorization_path, inferred_plan, inferred_preflight, authorization = (
        _authorization_layout(workspace, arguments.authorization)
    )
    plan_path, plan, config = _load_production_context(workspace, inferred_plan)
    _local_path, _preflight_path, local, bounded = _load_preflight_records(
        workspace, plan_path, inferred_preflight
    )
    request = build_authorization_start_request(authorization)
    validate_paid_authorization_start(
        authorization,
        config,
        plan,
        local,
        bounded,
        request,
        workspace_root=workspace,
    )
    result = execute_authorized_batch(
        plan,
        authorization,
        request,
        workspace_root=workspace,
        store=_transaction_store(workspace, config),
        output_stream=sys.stderr,
    )
    _print_json(
        {
            "authorization": workspace_relative(workspace, authorization_path),
            "operation": "production-execute",
            "result": record_to_data(result),
            "schema_version": 1,
        }
    )
    return EXIT_PASS if result.stopped_transaction_id is None else EXIT_INCOMPLETE


def _run_production_validate(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_models import (
        StrictRecordCodec,
        TransactionState,
        ValidationEvidence,
        record_to_data,
    )
    from .production_validation import validate_frozen_track_manifest

    plan_path, plan, config = _load_production_context(workspace, arguments.plan)
    store = _transaction_store(workspace, config)
    outcomes = []
    blocked = False
    for track in plan.tracks:
        evidence = validate_frozen_track_manifest(
            workspace,
            plan_path,
            track.track_id,
            track.transaction_id,
        )
        outcomes.append(record_to_data(evidence))
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        evidence_sha256 = StrictRecordCodec(ValidationEvidence).sha256(evidence)
        if evidence.delivery_gate_passed:
            if snapshot.state is TransactionState.RENDERED:
                store.append_transition(
                    track.track_id,
                    track.transaction_id,
                    operation_id="postflight-validation-v1",
                    event_type="validation-passed",
                    state_after=TransactionState.VALIDATED,
                    details={
                        "model-calls-started": 0,
                        "validation-sha256": evidence_sha256,
                    },
                    occurred_at_utc=evidence.validated_at_utc,
                )
            elif snapshot.state not in {
                TransactionState.VALIDATED,
                TransactionState.DELIVERED,
            }:
                raise InputError("Passing validation requires rendered transaction truth")
        else:
            blocked = True
            if snapshot.state is not TransactionState.BLOCKED:
                store.append_transition(
                    track.track_id,
                    track.transaction_id,
                    operation_id="postflight-validation-v1",
                    event_type="validation-blocked",
                    state_after=TransactionState.BLOCKED,
                    details={
                        "model-calls-started": 0,
                        "validation-sha256": evidence_sha256,
                    },
                    occurred_at_utc=evidence.validated_at_utc,
                )
    _print_json(
        {
            "billable_calls_made": 0,
            "model_calls_made": 0,
            "operation": "production-validate",
            "results": outcomes,
            "schema_version": 1,
        }
    )
    return EXIT_FIDELITY_MISMATCH if blocked else EXIT_PASS


def _run_production_deliver(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_delivery import deliver_validated_track
    from .production_models import DeliveryStatus, record_to_data

    plan_path, plan, _config = _load_production_context(workspace, arguments.plan)
    outcomes = []
    blocked = False
    for track in plan.tracks:
        record = deliver_validated_track(
            workspace,
            plan_path,
            track.track_id,
            track.transaction_id,
        )
        outcomes.append(record_to_data(record))
        blocked = blocked or record.status is DeliveryStatus.CONFLICTING
    _print_json(
        {
            "billable_calls_made": 0,
            "model_calls_made": 0,
            "operation": "production-deliver",
            "results": outcomes,
            "schema_version": 1,
        }
    )
    return EXIT_INCOMPLETE if blocked else EXIT_PASS


def _run_production_report(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_models import record_to_data
    from .production_reporting import write_batch_report

    plan_path, _plan, _config = _load_production_context(workspace, arguments.plan)
    report = write_batch_report(workspace, plan_path)
    _print_json(
        {
            "billable_calls_made": 0,
            "model_calls_made": 0,
            "operation": "production-report",
            "report": record_to_data(report),
            "schema_version": report.schema_version,
        }
    )
    return EXIT_PASS


def _run_production_status(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_config import load_production_config
    from .production_models import record_to_data

    plans = ()
    if arguments.plan is not None:
        _plan_path_value, plan, config = _load_production_context(
            workspace, arguments.plan
        )
        plans = (plan,)
    else:
        config = load_production_config(_production_config_path(workspace))
    result = _transaction_store(workspace, config).read_status(plans=plans)
    _print_json(
        {
            "billable_calls_made": 0,
            "model_calls_made": 0,
            "operation": "production-status",
            "schema_version": result.index.schema_version,
            "status": record_to_data(result),
        }
    )
    return EXIT_PASS


def _transaction_scope_from_path(workspace: Path, supplied_transaction: Path):
    from .production import load_production_plan
    from .production_config import load_production_config
    from .production_models import StrictRecordCodec
    from .production_transactions import TransactionMetadata

    transaction_path = _production_path(workspace, supplied_transaction)
    if transaction_path.is_symlink() or not transaction_path.is_dir():
        raise InputError("Transaction path must be a regular directory")
    metadata = StrictRecordCodec(TransactionMetadata).load(
        transaction_path / "transaction.json"
    )
    config = load_production_config(_production_config_path(workspace))
    if metadata.book_id != config.book_id:
        raise InputError("Transaction book identity differs from production configuration")
    store = _transaction_store(workspace, config)
    expected = store.transaction_path(metadata.track_id, metadata.transaction_id)
    if expected.resolve() != transaction_path:
        raise InputError("Transaction path is outside the generic transaction root")
    plan_path = resolve_inside(
        workspace,
        (
            PurePosixPath(config.build_root)
            / config.book_id
            / "plans"
            / metadata.plan_id
            / "plan.json"
        ).as_posix(),
    )
    plan = load_production_plan(plan_path)
    if not any(
        track.track_id == metadata.track_id
        and track.transaction_id == metadata.transaction_id
        for track in plan.tracks
    ):
        raise InputError("Transaction metadata is not present in its Frozen_Plan")
    return transaction_path, plan_path, metadata


def _run_production_inspect_resume(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_models import record_to_data
    from .production_resume import inspect_resume

    transaction_path, plan_path, metadata = _transaction_scope_from_path(
        workspace, arguments.transaction
    )
    inspection = inspect_resume(
        workspace,
        plan_path,
        metadata.track_id,
        metadata.transaction_id,
    )
    _print_json(
        {
            "billable_calls_made": 0,
            "inspection": record_to_data(inspection),
            "model_calls_made": 0,
            "operation": "production-inspect-resume",
            "schema_version": inspection.schema_version,
            "transaction": workspace_relative(workspace, transaction_path),
        }
    )
    return EXIT_PASS


def _run_production_resolve(workspace: Path, arguments: argparse.Namespace) -> int:
    from .production_models import record_to_data
    from .production_resume import ManualResolutionDisposition, resolve_resume

    transaction_path, plan_path, metadata = _transaction_scope_from_path(
        workspace, arguments.transaction
    )
    result = resolve_resume(
        workspace,
        plan_path,
        metadata.track_id,
        metadata.transaction_id,
        ManualResolutionDisposition(arguments.disposition),
    )
    _print_json(
        {
            "billable_calls_made": 0,
            "model_calls_made": 0,
            "operation": "production-resolve",
            "resolution": record_to_data(result),
            "schema_version": result.schema_version,
            "transaction": workspace_relative(workspace, transaction_path),
        }
    )
    return EXIT_PASS


def _run_production(workspace: Path, arguments: argparse.Namespace) -> int:
    handlers = {
        "plan": _run_production_plan,
        "preflight": _run_production_preflight,
        "authorize": _run_production_authorize,
        "execute": _run_production_execute,
        "validate": _run_production_validate,
        "deliver": _run_production_deliver,
        "report": _run_production_report,
        "status": _run_production_status,
        "inspect-resume": _run_production_inspect_resume,
        "resolve": _run_production_resolve,
    }
    try:
        handler = handlers[arguments.phase]
    except KeyError as exc:  # pragma: no cover - argparse supplies the closed set
        raise InputError(f"Unsupported production phase: {arguments.phase}") from exc
    return handler(workspace, arguments)


def run(arguments: argparse.Namespace) -> int:
    workspace = _workspace_root(arguments.workspace_root)
    if arguments.command == "_production-worker":
        return run_production_worker(
            workspace,
            arguments.plan,
            arguments.transaction,
            arguments.track,
        )
    if arguments.command == "production":
        return _run_production(workspace, arguments)
    if arguments.command == "audit":
        payload = audit_currency(
            workspace,
            include_unbound=not arguments.skip_unbound,
        )
        if arguments.json:
            _print_json(payload)
        else:
            print(format_currency_table(payload))
        return EXIT_PASS if payload["all_current"] else EXIT_FIDELITY_MISMATCH
    if arguments.command != "audition":
        raise InputError(f"Unsupported command: {arguments.command}")

    if arguments.phase == "plan":
        config_path = (
            arguments.config.expanduser().resolve()
            if arguments.config
            else workspace / ".audiobook" / "config" / "audition.toml"
        )
        config = load_audition_config(config_path, workspace)
        plan_path = create_plan(config, arguments.audition_id)
        plan, _ = load_plan(workspace, plan_path)
        print(json.dumps({"plan": str(plan_path), **plan_status(plan)}, indent=2, sort_keys=True))
        return EXIT_PASS

    if arguments.phase == "narrate":
        config = load_audition_config(
            workspace / ".audiobook" / "config" / "audition.toml",
            workspace,
        )
        if arguments.dry_run:
            outline = plan_narration(config, arguments.chapter, arguments.voice, arguments.max_words)
            preview = [
                {"segment_id": item["segment_id"], "words": item["word_count"], "text": item["text"]}
                for item in outline["segments"][:3]
            ]
            print(
                json.dumps(
                    {
                        "billable_calls_made": 0,
                        "chapter": outline["chapter"],
                        "voice_id": outline["voice_id"],
                        "word_count": outline["word_count"],
                        "planned_calls": outline["segment_count"],
                        "first_segments": preview,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return EXIT_PASS
        if not arguments.confirm_paid_render:
            raise InputError(
                "Refusing billable Bedrock calls without --confirm-paid-render; use --dry-run first"
            )

        def _report(segment, status, entry):
            print(
                f"[{segment.segment_id}/{status}] {entry.get('duration_seconds', 0)}s "
                f"words={entry.get('word_count')} exact={entry.get('exact_transcript_match')}",
                flush=True,
            )

        outcome = narrate_chapter(
            config,
            arguments.chapter,
            arguments.voice,
            paid_render_authorized=arguments.confirm_paid_render,
            accept_verbatim_prefix=arguments.accept_verbatim_prefix,
            max_words=arguments.max_words,
            progress=_report,
        )
        print(json.dumps(outcome, indent=2, sort_keys=True))
        return EXIT_PASS

    plan_path = _plan_path(arguments.plan)
    if arguments.phase == "render":
        plan, config = load_plan(workspace, plan_path)
        if arguments.dry_run:
            calls = dry_run_render(plan, config, arguments.voice, arguments.excerpt)
            print(json.dumps({"billable_calls_made": 0, "planned_calls": calls}, indent=2, sort_keys=True))
            return EXIT_PASS
        if not arguments.confirm_paid_render:
            raise InputError(
                "Refusing billable Bedrock calls without --confirm-paid-render; use --dry-run first"
            )
        rendered = render_plan(
            workspace,
            plan_path,
            arguments.voice,
            arguments.excerpt,
            paid_render_authorized=arguments.confirm_paid_render,
            accept_verbatim_prefix=arguments.accept_verbatim_prefix,
        )
        print(json.dumps({"rendered_calls": rendered, "plan": str(plan_path)}, indent=2, sort_keys=True))
        return EXIT_PASS

    if arguments.phase == "reconcile":
        outcome = reconcile_uncertain_call(
            workspace,
            plan_path,
            arguments.call_id,
            duplicate_charge_acknowledged=arguments.confirm_possible_duplicate_charge,
        )
        print(json.dumps({"plan": str(plan_path), **outcome}, indent=2, sort_keys=True))
        return EXIT_PASS

    if arguments.phase == "revalidate":
        outcomes = revalidate_plan(
            workspace,
            plan_path,
            arguments.voice,
            arguments.excerpt,
            accept_verbatim_prefix=arguments.accept_verbatim_prefix,
        )
        print(
            json.dumps(
                {"billable_calls_made": 0, "revalidated_calls": outcomes},
                indent=2,
                sort_keys=True,
            )
        )
        return EXIT_PASS

    if arguments.phase == "package":
        package_path = package_blind_audition(
            workspace,
            plan_path,
            accept_verbatim_prefix=arguments.accept_verbatim_prefix,
        )
        print(json.dumps({"package": str(package_path)}, indent=2, sort_keys=True))
        return EXIT_PASS

    if arguments.phase == "status":
        plan, _ = load_plan(workspace, plan_path)
        print(json.dumps(plan_status(plan), indent=2, sort_keys=True))
        return EXIT_PASS

    if arguments.phase == "reveal":
        print(json.dumps(reveal_blind_key(workspace, plan_path), indent=2, sort_keys=True))
        return EXIT_PASS

    raise InputError(f"Unsupported audition phase: {arguments.phase}")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(_parser().parse_args(argv))
    except AudiobookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return EXIT_INCOMPLETE


if __name__ == "__main__":
    raise SystemExit(main())
