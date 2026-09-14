"""Deterministic generated checks for audiobook production correctness Property 13."""

from __future__ import annotations

import hashlib
import random
import socket
from dataclasses import dataclass
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_config import parse_production_toml
from frontier_audiobook.production_preflight import (
    FileAttribution,
    InventoryKind,
    build_protected_inventory,
    derive_workflow_write_allowlist,
    evaluate_isolation,
)
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes, workspace_relative


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 13: Protected isolation is per-file and attributable"
PROPERTY_SEED = 0x13A77B1E
GENERATED_CASES = 128

# **Validates: Requirements 1.6, 1.7, 4.4, 13.1, 13.2, 13.3, 13.4,
# 13.5, 13.6, 13.7, 13.8, 13.9, 13.10**

_UNSELECTED_CHAPTERS = (1, 2, 4, 5)
_HARD_TARGET_KEYS = (
    "selected-source",
    "production-config",
    "runtime",
    "dependency",
    "chapter-1-audio",
    "chapter-2-audio",
    "chapter-2-spec",
    "chapter-3-spec",
    "governing-spec",
)
_ALLOWED_WRITE_KINDS = (
    "plan-root",
    "batch-root",
    "transaction-root",
    "status-index",
    "delivery-destination",
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    hard_target_key: str | None
    changed_unselected_count: int
    include_outside_workflow_write: bool
    allowed_write_kind: str
    mutation_offset: int


@pytest.fixture(autouse=True)
def deny_network_aws_model_and_render(monkeypatch, tmp_path):
    """Fail the property immediately if isolation inspection crosses an external boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 13 must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "denied-aws-config"))
    monkeypatch.setenv(
        "AWS_SHARED_CREDENTIALS_FILE",
        str(tmp_path / "denied-aws-credentials"),
    )
    for variable in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
    ):
        monkeypatch.delenv(variable, raising=False)


def _generated_case(rng: random.Random, case_index: int) -> _GeneratedCase:
    hard_target_key = (
        None
        if case_index % 4 == 0
        else _HARD_TARGET_KEYS[(case_index - case_index // 4) % len(_HARD_TARGET_KEYS)]
    )
    return _GeneratedCase(
        hard_target_key=hard_target_key,
        changed_unselected_count=case_index % (len(_UNSELECTED_CHAPTERS) + 1),
        include_outside_workflow_write=case_index % 6 == 0,
        allowed_write_kind=_ALLOWED_WRITE_KINDS[case_index % len(_ALLOWED_WRITE_KINDS)],
        mutation_offset=rng.randrange(1, 31),
    )


def _write_bytes(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _chapter_relative(chapter: int) -> str:
    return (
        "manuscript/chapters/discovery-part/"
        f"discovery-part-{chapter:03d}-property-isolation.md"
    )


def _write_chapter(workspace: Path, chapter: int, case_index: int) -> Path:
    body = (
        f"Beacon chapter {chapter} case {case_index} remains locally protected. "
        "Signal paths stay finite and attributable."
    )
    path = workspace / _chapter_relative(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                "pov_id: property-pov",
                "timeline_id: property-timeline",
                "motif_events: none",
                "hook: property-hook",
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
    return path


def _write_config(workspace: Path) -> Path:
    path = workspace / ".audiobook" / "config" / "production.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "manuscript"
build_root = ".audiobook/build/production"
delivery_root = ".audiobook/dist/audiobook"
max_tracks_per_plan = 16
tracks = []

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{sequence:03d}-{track_slug}-{voice}.wav"

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
''',
        encoding="utf-8",
    )
    return path


def _write_protected_tree(
    workspace: Path,
    rng: random.Random,
    case_index: int,
) -> tuple[Path, dict[str, Path], tuple[Path, ...]]:
    chapters = {
        chapter: _write_chapter(workspace, chapter, case_index)
        for chapter in (*_UNSELECTED_CHAPTERS, 3)
    }
    config_path = _write_config(workspace)

    runtime = _write_bytes(
        workspace / ".audiobook/src/frontier_audiobook/runtime_guard.py",
        f'RUNTIME_MARKER = "case-{case_index:03d}"\n'.encode("utf-8"),
    )
    dependency_paths = (
        _write_bytes(
            workspace / ".audiobook/pyproject.toml",
            f"[project]\nname = \"fixture-{case_index:03d}\"\n".encode("utf-8"),
        ),
        _write_bytes(workspace / ".audiobook/uv.lock", rng.randbytes(48)),
        _write_bytes(workspace / ".audiobook/requirements/dev.txt", b"pytest==9.1.1\n"),
        _write_bytes(workspace / ".audiobook/requirements/runtime.txt", b"runtime==1.0.0\n"),
    )
    chapter_2_spec = _write_bytes(
        workspace / ".kiro/specs/chapter-2-audio-proof/design.md",
        f"protected chapter 2 spec case {case_index:03d}\n".encode("utf-8"),
    )
    chapter_3_spec = _write_bytes(
        workspace / ".kiro/specs/chapter-3-audio-proof/tasks.md",
        f"protected chapter 3 spec case {case_index:03d}\n".encode("utf-8"),
    )
    governing_spec = _write_bytes(
        workspace / ".kiro/specs/The-Final-Frontier-novel/requirements.md",
        f"governing novel spec case {case_index:03d}\n".encode("utf-8"),
    )

    chapter_audio: dict[int, Path] = {}
    for chapter in (1, 2):
        proof = _write_bytes(
            workspace / "voice-samples" / f"chapter-{chapter}-tiffany-proof.wav",
            b"RIFF" + chapter.to_bytes(1, "big") + rng.randbytes(43),
        )
        chapter_audio[chapter] = proof
        legacy_root = (
            workspace
            / ".audiobook/build/narration"
            / f"chapter-{chapter:03d}-property-{case_index:03d}"
        )
        _write_bytes(legacy_root / "manifest.json", b'{"schema":"legacy"}\n')
        _write_bytes(
            legacy_root / "segments/segment-001.wav",
            b"RIFF" + chapter.to_bytes(1, "big") + rng.randbytes(27),
        )
        _write_bytes(legacy_root / "transcripts/segment-001.txt", b"legacy transcript\n")
        _write_bytes(legacy_root / "events/segment-001.jsonl", b"{}\n")

    hard_targets = {
        "selected-source": chapters[3],
        "production-config": config_path,
        "runtime": runtime,
        "dependency": dependency_paths[0],
        "chapter-1-audio": chapter_audio[1],
        "chapter-2-audio": chapter_audio[2],
        "chapter-2-spec": chapter_2_spec,
        "chapter-3-spec": chapter_3_spec,
        "governing-spec": governing_spec,
    }
    unselected = tuple(chapters[chapter] for chapter in _UNSELECTED_CHAPTERS)
    return config_path, hard_targets, unselected


def _create_case_scope(workspace: Path, config_path: Path, case_index: int):
    plan_path = create_production_plan(
        config_path,
        ProductionSelectors.from_cli(chapters=[3]),
        plan_id=f"property-13-{case_index:03d}",
        workspace_root=workspace,
        created_at_utc="2026-09-12T00:00:00Z",
    )
    plan = load_production_plan(plan_path)
    config = parse_production_toml(
        read_bytes_nofollow(config_path),
        label=str(config_path),
    )
    return config, plan


def _mutate_same_size(path: Path, offset: int) -> None:
    content = bytearray(read_bytes_nofollow(path))
    assert content
    index = offset % len(content)
    content[index] ^= 0x01
    path.write_bytes(content)


def _manuscript_aggregate(workspace: Path) -> tuple[int, str]:
    root = workspace / "manuscript"
    digest = hashlib.sha256()
    total_bytes = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = read_bytes_nofollow(path)
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        total_bytes += len(content)
    return total_bytes, digest.hexdigest()


def _instrument_allowed_write(
    workspace: Path,
    allowlist,
    write_kind: str,
    case_index: int,
) -> str:
    roots_by_kind = {
        "plan-root": next(root for root in allowlist.recursive_roots if "/plans/" in root),
        "batch-root": next(root for root in allowlist.recursive_roots if "/batches/" in root),
        "transaction-root": next(
            root for root in allowlist.recursive_roots if "/transactions/" in root
        ),
    }
    if write_kind in roots_by_kind:
        relative = f"{roots_by_kind[write_kind]}/instrumented-{case_index:03d}.json"
    elif write_kind == "status-index":
        relative = next(path for path in allowlist.exact_paths if path.endswith("/indexes/status.json"))
    else:
        relative = next(path for path in allowlist.exact_paths if not path.endswith("/indexes/status.json"))
    _write_bytes(workspace / relative, f"allowed-write-{case_index:03d}".encode("utf-8"))
    return relative


def _existing_inventory_bytes(workspace: Path, inventory) -> dict[str, bytes]:
    return {
        item.path: read_bytes_nofollow(workspace / item.path)
        for item in inventory.files
        if item.exists
    }


# Feature: audiobook-production-workflow, Property 13: Protected isolation is per-file and attributable
# **Validates: Requirements 1.6, 1.7, 4.4, 13.1-13.10**
def test_property_13_protected_isolation_is_per_file_and_attributable(tmp_path):
    """Feature: audiobook-production-workflow, Property 13: Protected isolation is per-file and attributable"""

    assert GENERATED_CASES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    observed_hard_targets: set[str] = set()
    observed_allowed_writes: set[str] = set()
    observed_unselected_aggregate_drift_pass = False
    observed_same_size_selected_drift_block = False
    observed_outside_write_block = False

    for case_index in range(GENERATED_CASES):
        case = _generated_case(rng, case_index)
        context = f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; input={case!r}"
        workspace = tmp_path / f"case-{case_index:03d}"
        config_path, hard_targets, unselected_paths = _write_protected_tree(
            workspace,
            rng,
            case_index,
        )
        config, plan = _create_case_scope(workspace, config_path, case_index)
        hard_targets["selected-source"] = workspace / plan.tracks[0].source.source_path

        baseline = build_protected_inventory(
            workspace,
            config,
            plan,
            git_statuses={},
        )
        allowlist = derive_workflow_write_allowlist(config, plan)
        baseline_bytes = _existing_inventory_bytes(workspace, baseline)
        baseline_files = {item.path: item for item in baseline.files}
        baseline_unselected = {item.path: item for item in baseline.unselected_manuscript_files}
        before_total_bytes, before_aggregate_sha256 = _manuscript_aggregate(workspace)

        expected_kinds = {
            workspace_relative(workspace, hard_targets["selected-source"]): InventoryKind.SELECTED_SOURCE,
            workspace_relative(workspace, hard_targets["production-config"]): InventoryKind.PRODUCTION_CONFIG,
            workspace_relative(workspace, hard_targets["runtime"]): InventoryKind.RUNTIME,
            workspace_relative(workspace, hard_targets["dependency"]): InventoryKind.DEPENDENCY,
            workspace_relative(workspace, hard_targets["chapter-1-audio"]): InventoryKind.PRIOR_AUDIO,
            workspace_relative(workspace, hard_targets["chapter-2-audio"]): InventoryKind.PRIOR_AUDIO,
            workspace_relative(workspace, hard_targets["chapter-2-spec"]): InventoryKind.HISTORICAL_SPEC,
            workspace_relative(workspace, hard_targets["chapter-3-spec"]): InventoryKind.HISTORICAL_SPEC,
            workspace_relative(workspace, hard_targets["governing-spec"]): InventoryKind.GOVERNING_SPEC,
        }
        assert expected_kinds.keys() <= baseline_files.keys(), context
        assert all(baseline_files[path].kind is kind for path, kind in expected_kinds.items()), context
        assert all(item.attribution is FileAttribution.BASELINE for item in baseline.files), context
        assert len(baseline.inventory_sha256) == 64, context
        for relative, content in baseline_bytes.items():
            observation = baseline_files[relative]
            assert observation.exists is True, context
            assert observation.byte_count == len(content), context
            assert observation.sha256 == sha256_bytes(content), context
            assert observation.git_status == "not-repository", context

        expected_unselected = {
            workspace_relative(workspace, path) for path in unselected_paths
        }
        assert set(baseline_unselected) == expected_unselected, context
        assert all(
            item.kind is InventoryKind.UNSELECTED_MANUSCRIPT
            and item.attribution is FileAttribution.BASELINE
            for item in baseline.unselected_manuscript_files
        ), context

        base = f"{config.build_root}/{config.book_id}"
        transaction_root = (
            f"{base}/transactions/{plan.tracks[0].track_id}/"
            f"{plan.tracks[0].transaction_id}"
        )
        assert f"{base}/plans/{plan.plan_id}" in allowlist.recursive_roots, context
        assert f"{base}/batches/{plan.plan_id}" in allowlist.recursive_roots, context
        assert transaction_root in allowlist.recursive_roots, context
        assert f"{base}/indexes/status.json" in allowlist.exact_paths, context
        assert plan.tracks[0].effective_config.output_path in allowlist.exact_paths, context

        allowed_write = _instrument_allowed_write(
            workspace,
            allowlist,
            case.allowed_write_kind,
            case_index,
        )
        observed_allowed_writes.add(case.allowed_write_kind)
        assert allowlist.contains(allowed_write), context
        workflow_written_paths = [allowed_write]

        outside_write: str | None = None
        if case.include_outside_workflow_write:
            outside_write = f".audiobook/build/unapproved/property-13-{case_index:03d}.json"
            _write_bytes(
                workspace / outside_write,
                f"outside-write-{case_index:03d}".encode("utf-8"),
            )
            workflow_written_paths.append(outside_write)
            assert not allowlist.contains(outside_write), context

        changed_unselected_paths = tuple(
            unselected_paths[index]
            for index in range(case.changed_unselected_count)
        )
        for index, path in enumerate(changed_unselected_paths):
            _mutate_same_size(path, case.mutation_offset + index)

        hard_target_path: Path | None = None
        if case.hard_target_key is not None:
            observed_hard_targets.add(case.hard_target_key)
            hard_target_path = hard_targets[case.hard_target_key]
            _mutate_same_size(hard_target_path, case.mutation_offset + 17)

        status_rows = {
            workspace_relative(workspace, path): "modified"
            for path in changed_unselected_paths
        }
        if hard_target_path is not None:
            status_rows[workspace_relative(workspace, hard_target_path)] = "modified"
        current = build_protected_inventory(
            workspace,
            config,
            plan,
            git_statuses=status_rows,
        )
        assessment = evaluate_isolation(
            baseline,
            current,
            allowlist,
            workflow_written_paths=workflow_written_paths,
        )
        current_files = {item.path: item for item in current.files}
        current_unselected = {item.path: item for item in current.unselected_manuscript_files}
        after_total_bytes, after_aggregate_sha256 = _manuscript_aggregate(workspace)

        expected_hard = (
            ()
            if hard_target_path is None
            else (workspace_relative(workspace, hard_target_path),)
        )
        expected_concurrent = tuple(
            sorted(workspace_relative(workspace, path) for path in changed_unselected_paths)
        )
        expected_outside = () if outside_write is None else (outside_write,)
        assert assessment.hard_protected_drift_paths == expected_hard, context
        assert assessment.concurrent_manuscript_change_paths == expected_concurrent, context
        assert assessment.workflow_writes_outside_allowlist == expected_outside, context
        assert assessment.passed is (hard_target_path is None and outside_write is None), context

        for relative in expected_concurrent:
            assert current_unselected[relative].attribution is FileAttribution.CONCURRENT_OR_UNATTRIBUTED, context
            assert relative not in assessment.hard_protected_drift_paths, context
        for relative in expected_unselected - set(expected_concurrent):
            assert current_unselected[relative].attribution is FileAttribution.BASELINE, context
        if hard_target_path is not None:
            hard_relative = workspace_relative(workspace, hard_target_path)
            assert current_files[hard_relative].attribution is FileAttribution.PREEXISTING, context

        for relative, original in baseline_bytes.items():
            current_content = read_bytes_nofollow(workspace / relative)
            if hard_target_path is not None and relative == workspace_relative(
                workspace,
                hard_target_path,
            ):
                assert len(current_content) == len(original), context
                assert current_content != original, context
                assert current_files[relative].sha256 != baseline_files[relative].sha256, context
            else:
                assert current_content == original, context
                assert current_files[relative].byte_count == baseline_files[relative].byte_count, context
                assert current_files[relative].sha256 == baseline_files[relative].sha256, context

        assert after_total_bytes == before_total_bytes, context
        if changed_unselected_paths:
            assert after_aggregate_sha256 != before_aggregate_sha256, context
            if hard_target_path is None and outside_write is None:
                assert assessment.passed is True, context
                observed_unselected_aggregate_drift_pass = True
        if case.hard_target_key == "selected-source":
            assert assessment.passed is False, context
            observed_same_size_selected_drift_block = True
        if outside_write is not None:
            assert assessment.passed is False, context
            observed_outside_write_block = True

    assert observed_hard_targets == set(_HARD_TARGET_KEYS)
    assert observed_allowed_writes == set(_ALLOWED_WRITE_KINDS)
    assert observed_unselected_aggregate_drift_pass is True
    assert observed_same_size_selected_drift_block is True
    assert observed_outside_write_block is True
