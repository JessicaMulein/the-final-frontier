"""Command-line entry point for the guarded blind voice audition."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import EXIT_INCOMPLETE, EXIT_PASS
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
from .errors import AudiobookError, InputError
from .narrate import MAX_SEGMENT_WORDS, narrate_chapter, plan_narration
from .util import find_workspace_root


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frontier-audiobook",
        description="Guarded Amazon Nova 2 Sonic audiobook voice audition",
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
    return parser


def _workspace_root(value: Path | None) -> Path:
    if value is not None:
        root = value.expanduser().resolve()
        if not (root / ".audiobook" / "config" / "audition.toml").is_file():
            raise InputError(f"Not a frontier-book workspace root: {root}")
        return root
    return find_workspace_root(Path.cwd())


def _plan_path(value: Path) -> Path:
    return value.expanduser().resolve()


def run(arguments: argparse.Namespace) -> int:
    workspace = _workspace_root(arguments.workspace_root)
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
