"""Repository-level structural checks for the reusable production workflow."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from frontier_audiobook.production_preflight import (
    ReadOnlyLegacyAdapter,
    _DEPENDENCY_PATHS,
    _GOVERNING_SPEC_ROOT,
    _HISTORICAL_SPEC_ROOTS,
)


AUDIOBOOK_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = AUDIOBOOK_ROOT.parent
README_PATH = AUDIOBOOK_ROOT / "README.md"

EXPECTED_RUNTIME_DEPENDENCIES = (
    "aws-sdk-bedrock-runtime==0.10.0",
    "smithy-http[awscrt]==0.4.4",
)
EXPECTED_DEV_DEPENDENCIES = ("pytest==9.1.1",)
EXPECTED_DEPENDENCY_PATHS = (
    ".audiobook/pyproject.toml",
    ".audiobook/uv.lock",
    ".audiobook/requirements/dev.txt",
    ".audiobook/requirements/runtime.txt",
)
EXPECTED_HISTORICAL_SPEC_ROOTS = (
    ".kiro/specs/chapter-2-audio-proof",
    ".kiro/specs/chapter-3-audio-proof",
)
EXPECTED_GOVERNING_SPEC_ROOT = ".kiro/specs/The-Final-Frontier-novel"
STABLE_PRODUCTION_COMMANDS = (
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
)
TRANSACTION_STATES = (
    "discovered",
    "planned",
    "preflight-passed",
    "authorization-required",
    "running",
    "charge-uncertain",
    "rendered",
    "validated",
    "delivered",
    "blocked",
)


def _requirements(path: Path) -> tuple[str, ...]:
    return tuple(
        line
        for raw_line in path.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith(("#", "-r "))
    )


def _locked_project_requirements(lock: dict[str, object]) -> tuple[dict[str, object], ...]:
    packages = lock.get("package")
    assert isinstance(packages, list)
    project = next(
        package
        for package in packages
        if isinstance(package, dict) and package.get("name") == "frontier-audiobook"
    )
    metadata = project.get("metadata")
    assert isinstance(metadata, dict)
    requirements = metadata.get("requires-dist")
    assert isinstance(requirements, list)
    return tuple(
        sorted(
            (requirement for requirement in requirements if isinstance(requirement, dict)),
            key=lambda requirement: str(requirement["name"]),
        )
    )


def _protected_regular_files() -> tuple[Path, ...]:
    paths: set[Path] = set()
    for relative_root in (*EXPECTED_HISTORICAL_SPEC_ROOTS, EXPECTED_GOVERNING_SPEC_ROOT):
        root = WORKSPACE_ROOT / relative_root
        assert root.is_dir(), f"required protected root is missing: {relative_root}"
        paths.update(path for path in root.rglob("*") if path.is_file())

    narration_root = AUDIOBOOK_ROOT / "build" / "narration"
    if narration_root.is_dir():
        for chapter in (1, 2):
            for root in narration_root.glob(f"chapter-{chapter:03d}-*"):
                if root.is_dir():
                    paths.update(path for path in root.rglob("*") if path.is_file())

    proof_root = WORKSPACE_ROOT / "voice-samples"
    if proof_root.is_dir():
        for chapter in (1, 2):
            paths.update(
                path
                for path in proof_root.glob(f"chapter-{chapter}-*.wav")
                if path.is_file()
            )

    return tuple(sorted(paths))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(paths: tuple[Path, ...]) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path in paths:
        assert not path.is_symlink(), f"protected path must not be a symlink: {path}"
        stat = path.stat()
        result[path.relative_to(WORKSPACE_ROOT).as_posix()] = (stat.st_size, _sha256(path))
    return result


def test_readme_documents_the_complete_reusable_operator_contract() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    for command in STABLE_PRODUCTION_COMMANDS:
        assert f"production {command}" in readme
    for state in TRANSACTION_STATES:
        assert state in readme
    for required_text in (
        ".audiobook/config/production.toml",
        "Normal single-track example",
        "Normal bounded-batch example",
        "Exact paid authorization boundary",
        "fail-fast behavior",
        "Inspection and manual resolution",
        "Cost_Estimate",
        "Computed_Pre_Tax_Service_Cost",
        "Billing_Confirmation",
        "Privacy, generated data, and protected paths",
        "Chapter 3 pilot instructions",
        "discovery-part-003-the-failed-check.md",
        "future normal tracks use this reusable workflow",
        "A future dependency must be proposed separately",
    ):
        assert required_text in readme


def test_dependency_contract_remains_exactly_pinned_without_additions() -> None:
    pyproject = tomllib.loads((AUDIOBOOK_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert tuple(pyproject["project"]["dependencies"]) == EXPECTED_RUNTIME_DEPENDENCIES
    assert tuple(pyproject["project"]["optional-dependencies"]["dev"]) == EXPECTED_DEV_DEPENDENCIES
    assert _requirements(AUDIOBOOK_ROOT / "requirements" / "runtime.txt") == (
        EXPECTED_RUNTIME_DEPENDENCIES
    )
    assert _requirements(AUDIOBOOK_ROOT / "requirements" / "dev.txt") == (
        EXPECTED_DEV_DEPENDENCIES
    )

    lock = tomllib.loads((AUDIOBOOK_ROOT / "uv.lock").read_text(encoding="utf-8"))
    assert _locked_project_requirements(lock) == (
        {"name": "aws-sdk-bedrock-runtime", "specifier": "==0.10.0"},
        {
            "marker": "extra == 'dev'",
            "name": "pytest",
            "specifier": "==9.1.1",
        },
        {
            "extras": ["awscrt"],
            "name": "smithy-http",
            "specifier": "==0.4.4",
        },
    )


def test_protected_roots_and_dependency_manifests_are_in_the_inventory_contract() -> None:
    assert _HISTORICAL_SPEC_ROOTS == EXPECTED_HISTORICAL_SPEC_ROOTS
    assert _GOVERNING_SPEC_ROOT == EXPECTED_GOVERNING_SPEC_ROOT
    assert _DEPENDENCY_PATHS == EXPECTED_DEPENDENCY_PATHS


def test_historical_specs_and_chapter_1_2_artifacts_are_observed_without_mutation() -> None:
    protected_paths = _protected_regular_files()
    before = _snapshot(protected_paths)

    observations = ReadOnlyLegacyAdapter(WORKSPACE_ROOT).observe((1, 2))

    after = _snapshot(protected_paths)
    assert after == before
    assert {observation.chapter for observation in observations} <= {1, 2}
    assert {observation.path for observation in observations} <= set(before)
    assert all(observation.byte_count == before[observation.path][0] for observation in observations)
    assert all(observation.sha256 == before[observation.path][1] for observation in observations)

    observed_paths = {observation.path for observation in observations}
    expected_legacy_paths = {
        path
        for path in before
        if path.startswith(
            (
                ".audiobook/build/narration/chapter-001-",
                ".audiobook/build/narration/chapter-002-",
                "voice-samples/chapter-1-",
                "voice-samples/chapter-2-",
            )
        )
    }
    assert observed_paths == expected_legacy_paths
