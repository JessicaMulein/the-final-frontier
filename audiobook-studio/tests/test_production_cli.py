from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
import venv
from dataclasses import dataclass
from pathlib import Path

import pytest


AUDIOBOOK_ROOT = Path(__file__).resolve().parents[1]
SPECIAL_SOURCE = """\
# Written Front Matter

## Spoken Title

Approved spoken opening words only.

## Copyright

This section is not approved for narration.
"""
CHAPTER_SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
    "Charlie one two three four.",
)


@dataclass(frozen=True)
class InstalledWheel:
    python: Path
    console: Path
    environment: dict[str, str]


@pytest.fixture(scope="module")
def installed_wheel(tmp_path_factory: pytest.TempPathFactory) -> InstalledWheel:
    root = tmp_path_factory.mktemp("production-cli-wheel")
    uv = shutil.which("uv")
    assert uv is not None, "uv is required by this project's validated build workflow"
    wheelhouse = root / "wheelhouse"
    environment = os.environ.copy()
    environment["UV_OFFLINE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["FRONTIER_AUDIOBOOK_DISABLE_AWS"] = "1"
    environment["AWS_EC2_METADATA_DISABLED"] = "true"
    environment.pop("PYTHONPATH", None)
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
    ):
        environment.pop(name, None)

    subprocess.run(
        [uv, "build", "--wheel", "--offline", "--out-dir", str(wheelhouse)],
        cwd=AUDIOBOOK_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    wheels = list(wheelhouse.glob("*.whl"))
    assert len(wheels) == 1

    installed = root / "installed"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(installed)
    scripts = installed / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    console = scripts / (
        "frontier-audiobook.exe" if os.name == "nt" else "frontier-audiobook"
    )
    install = subprocess.run(
        [uv, "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert install.returncode == 0, install.stderr

    network_guard = root / "network-guard"
    network_guard.mkdir()
    (network_guard / "sitecustomize.py").write_text(
        textwrap.dedent(
            """
            import socket

            def _blocked(*_args, **_kwargs):
                raise AssertionError("network access is forbidden in installed-wheel CLI tests")

            socket.create_connection = _blocked
            socket.socket.connect = _blocked
            socket.socket.connect_ex = _blocked
            """
        ),
        encoding="utf-8",
    )
    environment["PYTHONPATH"] = str(network_guard)
    environment["PATH"] = os.pathsep.join((str(scripts), environment.get("PATH", "")))

    imported = subprocess.run(
        [str(python), "-c", "import frontier_audiobook; print(frontier_audiobook.__file__)"],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert str(AUDIOBOOK_ROOT / "src") not in imported.stdout
    assert str(installed) in imported.stdout
    return InstalledWheel(python, console, environment)


def _chapter_path(workspace: Path, chapter: int) -> Path:
    names = {
        1: "discovery-part-001-first-contact.md",
        2: "discovery-part-002-second-signal.md",
    }
    return (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / names[chapter]
    )


def _write_chapter(workspace: Path, chapter: int) -> None:
    path = _chapter_path(workspace, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(CHAPTER_SENTENCES)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                'title: "Test Chapter"',
                "pov_id: test-pov",
                "timeline_id: test-timeline",
                "motif_events: none",
                "hook: test-hook",
                f"words: {len(body.split())}",
                "length_class: short",
                "status: draft",
                "---",
                body,
                "",
            )
        ),
        encoding="utf-8",
    )


def _sha256_bytes(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()


def _write_workspace(root: Path) -> Path:
    workspace = root / "workspace"
    workspace.mkdir()
    for chapter in (1, 2):
        _write_chapter(workspace, chapter)

    special_path = workspace / "audiobook-studio" / "config" / "tracks" / "opening-credits.md"
    special_path.parent.mkdir(parents=True)
    special_path.write_text(SPECIAL_SOURCE, encoding="utf-8")
    special_sha256 = _sha256_bytes(SPECIAL_SOURCE.encode("utf-8"))
    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    config_path.write_text(
        f'''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
max_tracks_per_plan = 8

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{{sequence:03d}}-{{track_slug}}-{{voice}}.wav"

[defaults.audio]
sample_rate_hz = 24000
sample_size_bits = 16
channels = 1

[estimate]
rate_max_age_hours = 24
preflight_max_age_hours = 24
input_speech_tokens_per_call = 0
input_text_tokens_per_call = 8192
output_speech_tokens_per_call = 8192
output_text_tokens_per_call = 8192

[[tracks]]
id = "opening-credits"
kind = "opening_credits"
sequence = 1
source_path = "audiobook-studio/config/tracks/opening-credits.md"
source_section = "spoken-title"
approved_sha256 = "{special_sha256}"
enabled = true
approval_status = "approved"
render_once = true

[tracks.override]
''',
        encoding="utf-8",
    )
    return workspace


def _run_cli(
    installed: InstalledWheel,
    workspace: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            str(installed.console),
            "--workspace-root",
            str(workspace),
            *arguments,
        ],
        cwd=workspace,
        env=installed.environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if check:
        assert completed.returncode == 0, completed.stderr
    return completed


def _json_output(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    value = json.loads(completed.stdout)
    assert isinstance(value, dict)
    return value


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_installed_wheel_plans_single_range_and_render_once_tracks_in_generic_roots(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    workspace = _write_workspace(tmp_path)
    help_result = _run_cli(installed_wheel, workspace, "production", "--help")
    for command in (
        "plan",
        "preflight",
        "authorize",
        "execute",
        "validate",
        "deliver",
        "report",
        "status",
        "inspect-resume",
        "resolve",
    ):
        assert re.search(rf"\b{re.escape(command)}\b", help_result.stdout)
    audition_help = _run_cli(installed_wheel, workspace, "audition", "--help")
    assert "narrate" in audition_help.stdout
    assert "render" in audition_help.stdout

    single = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "plan",
            "--chapter",
            "1",
            "--plan-id",
            "installed-single",
        )
    )
    assert single["schema_version"] == 1
    assert single["billable_calls_made"] == 0
    assert single["external_calls_made"] == 0
    assert [item["track_id"] for item in single["tracks"]] == ["chapter-001"]

    ranged = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "plan",
            "--chapter-range",
            "1:2",
            "--plan-id",
            "installed-range",
        )
    )
    assert [item["track_id"] for item in ranged["tracks"]] == [
        "chapter-001",
        "chapter-002",
    ]

    special = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "plan",
            "--track",
            "opening-credits",
            "--plan-id",
            "installed-special",
        )
    )
    assert [item["track_id"] for item in special["tracks"]] == ["opening-credits"]
    assert special["tracks"][0]["sequence"] == 1

    for payload in (single, ranged, special):
        plan_relative = payload["plan"]
        assert isinstance(plan_relative, str)
        assert plan_relative.startswith(
            "audiobook-studio/build/production/the-final-frontier/plans/"
        )
        assert plan_relative.endswith("/plan.json")
        plan_bytes = (workspace / plan_relative).read_bytes()
        assert b"Alpha one two three four" not in plan_bytes
        assert b"Approved spoken opening words only" not in plan_bytes

    assert not (workspace / ".kiro").exists()
    assert not list(workspace.rglob("chapter*_proof.py"))
    assert not list(workspace.rglob("chapter-*-proof.py"))
    generated_files = [
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file() and "audiobook-studio/build" in path.as_posix()
    ]
    assert generated_files
    assert all(
        path.startswith("audiobook-studio/build/production/the-final-frontier/plans/")
        for path in generated_files
    )


def test_installed_wheel_dry_flow_rebuilds_status_and_rejects_invalid_authorization(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    workspace = _write_workspace(tmp_path)
    planned = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "plan",
            "--chapter",
            "1",
            "--plan-id",
            "installed-status",
        )
    )
    plan_path = workspace / str(planned["plan"])
    local_preflight = plan_path.with_name("local-preflight.json")
    bounded_preflight = plan_path.with_name("preflight.json")

    dry = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "preflight",
            "--plan",
            str(plan_path),
            "--dry-run",
        )
    )
    assert dry["operation"] == "production-preflight-dry-run"
    assert dry["billable_calls_made"] == 0
    assert dry["external_calls_made"] == 0
    assert dry["model_calls_made"] == 0
    assert not local_preflight.exists()
    assert not bounded_preflight.exists()

    materialize = textwrap.dedent(
        """
        import sys
        from pathlib import Path
        from frontier_audiobook.production import load_production_plan
        from frontier_audiobook.production_config import load_production_config
        from frontier_audiobook.production_transactions import TransactionStore

        workspace = Path(sys.argv[1]).resolve()
        plan_path = Path(sys.argv[2]).resolve()
        plan = load_production_plan(plan_path)
        config = load_production_config(workspace / plan.config_path)
        store = TransactionStore(workspace / config.build_root / config.book_id, config.book_id)
        snapshots = store.materialize_plan(plan)
        print(store.transaction_path(snapshots[0].metadata.track_id, snapshots[0].metadata.transaction_id))
        """
    )
    materialized = subprocess.run(
        [str(installed_wheel.python), "-c", materialize, str(workspace), str(plan_path)],
        cwd=workspace,
        env=installed_wheel.environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    transaction_path = Path(materialized.stdout.strip())

    first_status = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "status",
            "--plan",
            str(plan_path),
        )
    )
    status_value = first_status["status"]
    assert status_value["cache_disposition"] == "missing-rebuilt"
    assert status_value["index"]["transactions"][0]["state"] == "planned"
    assert status_value["index"]["transactions"][0]["health"] == "valid"

    report_first = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "report",
            "--plan",
            str(plan_path),
        )
    )
    report_second = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "report",
            "--plan",
            str(plan_path),
        )
    )
    assert report_second == report_first
    assert report_first["report"]["tracks"][0]["state"] == "planned"

    inspection = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "inspect-resume",
            "--transaction",
            str(transaction_path),
        )
    )
    assert inspection["inspection"]["classification"] == "blocked-new-plan-required"
    assert inspection["inspection"]["finding_categories"] == [
        "source-config-runtime-binding-invalid"
    ]
    assert inspection["billable_calls_made"] == 0

    transaction_before = _tree_bytes(transaction_path)
    index_path = (
        workspace
        / "audiobook-studio"
        / "build"
        / "production"
        / "the-final-frontier"
        / "indexes"
        / "status.json"
    )
    index_path.write_bytes(b"{corrupt-status-cache")
    rebuilt = _json_output(
        _run_cli(installed_wheel, workspace, "production", "status", "--book")
    )
    assert rebuilt["status"]["cache_disposition"] == "corrupt-rebuilt"
    assert rebuilt["status"]["index"]["transactions"][0]["state"] == "planned"
    assert _tree_bytes(transaction_path) == transaction_before
    current = _json_output(
        _run_cli(installed_wheel, workspace, "production", "status", "--book")
    )
    assert current["status"]["cache_disposition"] == "current"
    assert current["status"]["index"]["transactions"] == rebuilt["status"]["index"][
        "transactions"
    ]

    invalid_authorization = plan_path.parent / "authorizations" / "invalid.json"
    invalid_authorization.parent.mkdir()
    invalid_authorization.write_text("{}", encoding="utf-8")
    rejected = _run_cli(
        installed_wheel,
        workspace,
        "production",
        "execute",
        "--authorization",
        str(invalid_authorization),
        check=False,
    )
    assert rejected.returncode == 2
    assert "error:" in rejected.stderr
    assert not (transaction_path / "attempts").exists()
    assert _tree_bytes(transaction_path) == transaction_before
    assert not (workspace / ".kiro").exists()
    assert not list(workspace.rglob("chapter*_proof.py"))


def test_installed_wheel_execute_uses_one_synthetic_direct_child_without_external_calls(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    workspace = _write_workspace(tmp_path)
    child = workspace / "synthetic_direct_child.py"
    child.write_text(
        "import json\nprint(json.dumps({'event': 'synthetic-local-child'}, sort_keys=True))\n",
        encoding="utf-8",
    )
    setup_script = workspace / "prepare_synthetic_execution.py"
    setup_script.write_text(
        textwrap.dedent(
            """
            import json
            import sys
            from dataclasses import replace
            from datetime import UTC, datetime, timedelta
            from pathlib import Path

            from frontier_audiobook.production import (
                ProductionSelectors,
                create_production_plan,
                load_production_plan,
            )
            from frontier_audiobook.production_authorization import (
                AuthorizationDisplay,
                ExactAuthorizationConfirmation,
                create_paid_authorization_file,
            )
            from frontier_audiobook.production_config import (
                build_ordered_track_catalog,
                load_production_config,
            )
            from frontier_audiobook.production_delivery import write_immutable_evidence
            from frontier_audiobook.production_models import (
                AuthorizationDecision,
                FrozenBatchPlan,
                StrictRecordCodec,
                TransactionState,
                canonical_sha256,
                seal_record,
            )
            from frontier_audiobook.production_preflight import (
                BoundedPreflightEstimateResult,
                LocalPreflightResult,
                bind_targeted_check_result,
                run_bounded_identity_rate_preflight,
                run_local_preflight,
            )
            from frontier_audiobook.production_transactions import TransactionStore
            from frontier_audiobook.util import workspace_relative

            def fmt(value):
                return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

            workspace = Path(sys.argv[1]).resolve()
            python = sys.argv[2]
            child = Path(sys.argv[3]).resolve()
            config_path = workspace / "audiobook-studio/config/production.toml"
            plan_path = create_production_plan(
                config_path,
                ProductionSelectors.from_cli(chapters=[1]),
                plan_id="installed-synthetic-execution",
                workspace_root=workspace,
            )
            original = load_production_plan(plan_path)
            argv = (python, str(child))
            track = replace(
                original.tracks[0],
                command_argv=argv,
                command_sha256=canonical_sha256(argv),
            )
            plan = seal_record(replace(original, tracks=(track,), canonical_sha256=""))
            plan_path.write_bytes(StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan))

            config = load_production_config(config_path)
            catalog = build_ordered_track_catalog(config, workspace)
            targeted_path = workspace / "audiobook-studio/build/targeted/installed-cli.json"
            targeted_path.parent.mkdir(parents=True, exist_ok=True)
            targeted_path.write_text('{"passed":true,"external_access":false}', encoding="utf-8")
            targeted = bind_targeted_check_result(
                workspace,
                workspace_relative(workspace, targeted_path),
                command_sha256=canonical_sha256(("pytest", "installed-wheel-cli")),
                return_code=0,
                aws_access_disabled=True,
                model_access_disabled=True,
            )
            local = run_local_preflight(
                workspace,
                config,
                catalog,
                plan,
                targeted,
                required_free_bytes=0,
                git_statuses={},
            )
            assert local.passed

            now = datetime.now(UTC)
            checked = now - timedelta(minutes=2)
            checked_text = fmt(checked)
            day = checked.date().isoformat()
            offers = []
            for modality, rate in (
                ("input_speech", "0.001"),
                ("input_text", "0.002"),
                ("output_speech", "0.003"),
                ("output_text", "0.004"),
            ):
                offers.append(
                    {
                        "model_id": "amazon.nova-2-sonic-v1:0",
                        "region": "us-east-1",
                        "purchase_option": "on-demand",
                        "currency": "USD",
                        "unit": "per-1k-tokens",
                        "modality": modality,
                        "rate_per_1k_tokens": rate,
                    }
                )
            rates = json.dumps(
                {
                    "schema_version": 1,
                    "source_url": "https://aws.amazon.com/bedrock/pricing/",
                    "offer_publication_date": day,
                    "retrieved_at_utc": checked_text,
                    "effective_date": day,
                    "offers": offers,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            bounded = run_bounded_identity_rate_preflight(
                config,
                plan,
                local,
                identity_call=lambda profile: {"resolved_profile": profile},
                official_rate_document=rates,
                checked_at_utc=checked_text,
            )
            assert bounded.passed
            write_immutable_evidence(
                plan_path.with_name("local-preflight.json"),
                StrictRecordCodec(LocalPreflightResult).dump_bytes(local),
            )
            write_immutable_evidence(
                plan_path.with_name("preflight.json"),
                StrictRecordCodec(BoundedPreflightEstimateResult).dump_bytes(bounded),
            )

            store = TransactionStore(workspace / config.build_root / config.book_id, config.book_id)
            store.materialize_plan(plan, occurred_at_utc=fmt(checked))
            store.append_transition(
                track.track_id,
                track.transaction_id,
                operation_id="installed-preflight-passed",
                event_type="preflight-passed",
                state_after=TransactionState.PREFLIGHT_PASSED,
                details={"preflight_sha256": bounded.canonical_sha256},
                occurred_at_utc=fmt(checked + timedelta(seconds=1)),
            )
            store.append_transition(
                track.track_id,
                track.transaction_id,
                operation_id="installed-authorization-required",
                event_type="authorization-required",
                state_after=TransactionState.AUTHORIZATION_REQUIRED,
                details={"preflight_sha256": bounded.canonical_sha256},
                occurred_at_utc=fmt(checked + timedelta(seconds=2)),
            )

            def confirm(display: AuthorizationDisplay):
                return ExactAuthorizationConfirmation(
                    schema_version=1,
                    display_sha256=display.canonical_sha256,
                    challenge=display.confirmation_challenge,
                    decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
                )

            moments = iter((now - timedelta(minutes=1), now - timedelta(seconds=50)))
            authorization_path = (
                plan_path.parent / "authorizations" / "installed-synthetic-authorization.json"
            )
            create_paid_authorization_file(
                authorization_path,
                config,
                plan,
                local,
                bounded,
                workspace_root=workspace,
                authorization_id="installed-synthetic-authorization",
                operator_approved_max_estimated_pre_tax_usd="10",
                expires_at_utc=fmt(now + timedelta(hours=1)),
                confirmation_provider=confirm,
                clock=lambda: next(moments),
            )
            print(authorization_path)
            """
        ),
        encoding="utf-8",
    )
    prepared = subprocess.run(
        [
            str(installed_wheel.python),
            str(setup_script),
            str(workspace),
            str(installed_wheel.python),
            str(child),
        ],
        cwd=workspace,
        env=installed_wheel.environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert prepared.returncode == 0, prepared.stderr
    authorization_path = Path(prepared.stdout.strip())

    executed = _json_output(
        _run_cli(
            installed_wheel,
            workspace,
            "production",
            "execute",
            "--authorization",
            str(authorization_path),
        )
    )
    result = executed["result"]
    assert executed["operation"] == "production-execute"
    assert result["stopped_transaction_id"] is None
    assert len(result["started_transaction_ids"]) == 1
    assert len(result["attempt_results"]) == 1
    assert result["attempt_results"][0]["native_return_code"] == 0
    assert result["attempt_results"][0]["child_launched"] is True
    assert result["attempt_results"][0]["automatic_retry_performed"] is False
    assert result["plan_status"]["tracks"][0]["state"] == "rendered"

    attempts = list(
        (
            workspace
            / "audiobook-studio/build/production/the-final-frontier/transactions"
        ).glob("*/transaction-*/attempts/attempt-001/attempt.json")
    )
    assert len(attempts) == 1
    attempt = json.loads(attempts[0].read_text(encoding="utf-8"))
    assert attempt["argv"] == [str(installed_wheel.python), str(child)]
    assert attempt["native_return_code"] == 0
    assert attempt["environment_persisted"] is False
    assert not (workspace / ".kiro").exists()
    assert not list(workspace.rglob("chapter*_proof.py"))
