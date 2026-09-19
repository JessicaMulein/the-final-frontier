"""Manifest and result codecs for the nonbillable production test gate.

The targeted gate is intentionally explicit: every affected test module belongs to
one or more production-contract categories, and every designed correctness property
has a fixed seed and a minimum deterministic case count.  A broader suite is a
separate result whose failures are classified against the exact targeted collection.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Sequence

TARGETED_MARKER = "production_targeted"
TARGETED_CATEGORIES = (
    "config",
    "plan",
    "ledger",
    "auth",
    "attempt",
    "batch",
    "reuse",
    "validation",
    "cost",
    "delivery",
    "isolation",
    "sanitization",
    "legacy",
    "special-track",
)

# File-level classification is deliberate.  Pytest expands each file to exact node
# IDs in the result artifact, so this remains maintainable without repeating every
# function name here while still failing closed on a newly added, unclassified
# production test module.
TARGETED_TEST_FILE_CATEGORIES: Mapping[str, tuple[str, ...]] = {
    "test_production.py": ("config", "plan", "special-track"),
    "test_production_accounting.py": ("validation", "cost"),
    "test_production_attempt.py": ("auth", "attempt", "sanitization"),
    "test_production_authorization.py": ("auth", "cost"),
    "test_production_batch.py": ("ledger", "auth", "attempt", "batch"),
    "test_production_cli.py": TARGETED_CATEGORIES,
    "test_production_config.py": ("config", "plan", "special-track"),
    "test_production_delivery_reporting.py": (
        "batch",
        "validation",
        "cost",
        "delivery",
        "isolation",
        "sanitization",
    ),
    "test_production_evidence.py": ("isolation", "sanitization"),
    "test_production_models.py": (
        "config",
        "plan",
        "ledger",
        "auth",
        "attempt",
        "validation",
        "cost",
        "delivery",
        "sanitization",
    ),
    "test_production_preflight.py": (
        "plan",
        "reuse",
        "cost",
        "delivery",
        "isolation",
        "legacy",
    ),
    "test_production_property_1.py": ("config", "plan", "special-track"),
    "test_production_property_2.py": ("plan", "auth", "cost"),
    "test_production_property_3.py": ("ledger", "isolation"),
    "test_production_property_4.py": ("auth", "attempt"),
    "test_production_property_5.py": ("attempt", "sanitization"),
    "test_production_property_6.py": ("ledger", "auth", "attempt", "batch"),
    "test_production_property_7.py": ("attempt", "batch", "reuse"),
    "test_production_property_8.py": ("validation",),
    "test_production_property_9.py": ("validation",),
    "test_production_property_10.py": ("validation",),
    "test_production_property_11.py": ("validation", "cost"),
    "test_production_property_12.py": ("delivery",),
    "test_production_property_13.py": ("isolation",),
    "test_production_property_14.py": ("attempt", "isolation", "sanitization"),
    "test_production_property_15.py": ("reuse", "isolation", "legacy"),
    "test_production_resume.py": ("ledger", "attempt", "reuse"),
    "test_production_test_gate.py": TARGETED_CATEGORIES,
    "test_production_transactions.py": ("ledger", "isolation"),
    "test_production_validation.py": ("reuse", "validation", "cost"),
    "test_production_worker.py": ("attempt", "batch", "reuse", "validation"),
    "test_property_render_once_catalog.py": ("config", "plan", "special-track"),
}

# Task 8.3's repository-constraint module is intentionally split at item level:
# its inventory/legacy checks overlap the task 8.2 contracts, while documentation
# and dependency-governance checks remain broader-only until separately requested.
TARGETED_TEST_NODE_CATEGORIES: Mapping[str, tuple[str, ...]] = {
    "test_production_repository_constraints.py::test_protected_roots_and_dependency_manifests_are_in_the_inventory_contract": (
        "isolation",
        "legacy",
    ),
    "test_production_repository_constraints.py::test_historical_specs_and_chapter_1_2_artifacts_are_observed_without_mutation": (
        "isolation",
        "legacy",
    ),
}
BROADER_ONLY_TEST_NODES = frozenset(
    {
        "test_production_repository_constraints.py::test_readme_documents_the_complete_reusable_operator_contract",
        "test_production_repository_constraints.py::test_dependency_contract_remains_exactly_pinned_without_additions",
    }
)


@dataclass(frozen=True, slots=True)
class PropertySpec:
    number: int
    file_name: str
    case_constant: str
    title: str


PROPERTY_SPECS = (
    PropertySpec(1, "test_production_property_1.py", "GENERATED_CASES", "Effective configuration and source planning are deterministic"),
    PropertySpec(2, "test_production_property_2.py", "GENERATED_CASES", "Frozen plans and preflight scopes are immutable and bounded"),
    PropertySpec(3, "test_production_property_3.py", "GENERATED_SEQUENCES", "Transaction truth is independently reconstructable"),
    PropertySpec(4, "test_production_property_4.py", "GENERATED_CASES", "Authorization is exact, finite, current, and one-shot"),
    PropertySpec(5, "test_production_property_5.py", "GENERATED_CASES", "Paid attempt state is definitive or explicitly uncertain"),
    PropertySpec(6, "test_production_property_6.py", "GENERATED_CASES", "Batch execution is fail-fast with independent transactions"),
    PropertySpec(7, "test_production_property_7.py", "GENERATED_CASES", "Reuse and resume never create unapproved calls"),
    PropertySpec(8, "test_production_property_8.py", "GENERATED_CASES", "Active manifests are complete and unambiguous"),
    PropertySpec(9, "test_production_property_9.py", "GENERATED_CASES", "Exact transcript and LPCM replay are preserved"),
    PropertySpec(10, "test_production_property_10.py", "GENERATED_CASES", "Assembly integrity is preserved"),
    PropertySpec(11, "test_production_property_11.py", "GENERATED_CASES", "Journal aggregation and exact cost are modality-complete"),
    PropertySpec(12, "test_production_property_12.py", "GENERATED_CASES", "Delivery is collision-safe and idempotent"),
    PropertySpec(13, "test_production_property_13.py", "GENERATED_CASES", "Protected isolation is per-file and attributable"),
    PropertySpec(14, "test_production_property_14.py", "GENERATED_CASES", "Evidence and identity persistence obey explicit allowlists"),
    PropertySpec(15, "test_production_property_15.py", "GENERATED_CASES", "Legacy import is observational and byte-preserving"),
    PropertySpec(16, "test_property_render_once_catalog.py", "GENERATED_CASES", "Render-once book tracks are catalog-unique"),
)


class TestGateConfigurationError(ValueError):
    """The explicit gate manifest or deterministic property metadata is invalid."""


@dataclass(frozen=True, slots=True)
class PropertyRun:
    number: int
    file_name: str
    title: str
    seed: int
    cases: int
    case_unit: str

    def as_json(self) -> dict[str, object]:
        return {
            "property": self.number,
            "file": self.file_name,
            "title": self.title,
            "seed": self.seed,
            "seed_hex": f"0x{self.seed:X}",
            "cases": self.cases,
            "case_unit": self.case_unit,
        }


class SuiteOutcome(StrEnum):
    NOT_RUN = "not-run"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


class BroaderFailureDisposition(StrEnum):
    BLOCKING_OVERLAP = "blocking-targeted-overlap"
    NON_GATING_DIAGNOSTIC = "non-gating-diagnostic"


@dataclass(frozen=True, slots=True)
class BroaderFailure:
    nodeid: str
    disposition: BroaderFailureDisposition

    def as_json(self) -> dict[str, str]:
        return {"nodeid": self.nodeid, "classification": self.disposition.value}


def categories_for_test_file(file_name: str) -> tuple[str, ...]:
    """Return default gate categories, or an empty tuple for item-classified files."""

    categories = TARGETED_TEST_FILE_CATEGORIES.get(file_name, ())
    unknown = sorted(set(categories).difference(TARGETED_CATEGORIES))
    if unknown:
        raise TestGateConfigurationError(
            f"Targeted test file {file_name!r} has unknown categories: {unknown}"
        )
    return categories


def test_node_key(file_name: str, test_name: str) -> str:
    if not file_name or not test_name:
        raise TestGateConfigurationError("Test file and test name must be nonempty")
    return f"{file_name}::{test_name}"


def categories_for_test_node(file_name: str, test_name: str) -> tuple[str, ...]:
    """Return item override categories before falling back to its file categories."""

    key = test_node_key(file_name, test_name)
    categories = TARGETED_TEST_NODE_CATEGORIES.get(
        key, categories_for_test_file(file_name)
    )
    unknown = sorted(set(categories).difference(TARGETED_CATEGORIES))
    if unknown:
        raise TestGateConfigurationError(
            f"Targeted test node {key!r} has unknown categories: {unknown}"
        )
    return categories


def _safe_constant_expression(node: ast.AST, values: Mapping[str, object]) -> object:
    """Evaluate only deterministic constant arithmetic used by property metadata."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        members = [_safe_constant_expression(member, values) for member in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(members)
        if isinstance(node, ast.Set):
            return set(members)
        return members
    if isinstance(node, ast.UnaryOp):
        operand = _safe_constant_expression(node.operand, values)
        if type(operand) is not int:
            raise ValueError("non-integer unary operand")
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return -operand
    if isinstance(node, ast.BinOp):
        left = _safe_constant_expression(node.left, values)
        right = _safe_constant_expression(node.right, values)
        if type(left) is not int or type(right) is not int:
            raise ValueError("non-integer arithmetic operand")
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        arguments = [_safe_constant_expression(argument, values) for argument in node.args]
        if node.func.id == "len" and len(arguments) == 1:
            return len(arguments[0])  # type: ignore[arg-type]
        if node.func.id == "range" and 1 <= len(arguments) <= 3:
            if not all(type(argument) is int for argument in arguments):
                raise ValueError("range arguments must be integers")
            return range(*arguments)  # type: ignore[arg-type]
        if node.func.id == "sum" and len(arguments) == 1:
            return sum(arguments[0])  # type: ignore[arg-type]
    raise ValueError("expression is not deterministic constant metadata")


def _literal_assignments(path: Path) -> tuple[dict[str, object], str]:
    if path.is_symlink() or not path.is_file():
        raise TestGateConfigurationError(f"Property test is not a regular file: {path}")
    try:
        source = path.read_text(encoding="utf-8", errors="strict")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise TestGateConfigurationError(f"Cannot inspect property test {path}: {exc}") from exc

    values: dict[str, object] = {}
    for statement in tree.body:
        target: ast.expr | None = None
        expression: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            expression = statement.value
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
            expression = statement.value
        if not isinstance(target, ast.Name) or expression is None:
            continue
        try:
            values[target.id] = _safe_constant_expression(expression, values)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    return values, source


def inspect_property_runs(tests_root: Path) -> tuple[PropertyRun, ...]:
    """Validate and report the fixed seed/case contract for all 16 properties."""

    root = tests_root.expanduser().resolve()
    runs: list[PropertyRun] = []
    for spec in PROPERTY_SPECS:
        path = root / spec.file_name
        values, source = _literal_assignments(path)
        seed = values.get("PROPERTY_SEED")
        cases = values.get(spec.case_constant)
        if type(seed) is not int or seed < 0:
            raise TestGateConfigurationError(
                f"Property {spec.number} must declare a nonnegative integer PROPERTY_SEED"
            )
        if type(cases) is not int or cases < 100:
            raise TestGateConfigurationError(
                f"Property {spec.number} must declare at least 100 deterministic cases"
            )
        required_label = f"Property {spec.number}: {spec.title}"
        if required_label not in source:
            raise TestGateConfigurationError(
                f"{spec.file_name} does not contain its designed property label"
            )
        if "**Validates: Requirements" not in source:
            raise TestGateConfigurationError(
                f"{spec.file_name} does not contain a requirements validation annotation"
            )
        runs.append(
            PropertyRun(
                number=spec.number,
                file_name=spec.file_name,
                title=spec.title,
                seed=seed,
                cases=cases,
                case_unit="sequences" if spec.case_constant == "GENERATED_SEQUENCES" else "cases",
            )
        )
    if tuple(run.number for run in runs) != tuple(range(1, 17)):
        raise TestGateConfigurationError("Property manifest must contain Properties 1 through 16")
    return tuple(runs)


def _normalize_nodeid(nodeid: str) -> str:
    if not isinstance(nodeid, str) or not nodeid.strip():
        raise TestGateConfigurationError("Test node IDs must be nonempty strings")
    normalized = nodeid.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _node_file(nodeid: str) -> str:
    return _normalize_nodeid(nodeid).split("::", 1)[0]


def classify_broader_failures(
    targeted_nodeids: Sequence[str],
    failed_nodeids: Sequence[str],
) -> tuple[BroaderFailure, ...]:
    """Classify broader failures against exact targeted nodes and their files."""

    targeted = {_normalize_nodeid(value) for value in targeted_nodeids}
    targeted_files = {_node_file(value) for value in targeted}
    classified: list[BroaderFailure] = []
    seen: set[str] = set()
    for raw_nodeid in failed_nodeids:
        nodeid = _normalize_nodeid(raw_nodeid)
        if nodeid in seen:
            continue
        seen.add(nodeid)
        overlaps = nodeid in targeted or _node_file(nodeid) in targeted_files
        classified.append(
            BroaderFailure(
                nodeid=nodeid,
                disposition=(
                    BroaderFailureDisposition.BLOCKING_OVERLAP
                    if overlaps
                    else BroaderFailureDisposition.NON_GATING_DIAGNOSTIC
                ),
            )
        )
    return tuple(classified)


def targeted_manifest_sha256(nodeids: Sequence[str]) -> str:
    normalized = sorted({_normalize_nodeid(value) for value in nodeids})
    content = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def build_broader_suite_report(
    *,
    outcome: SuiteOutcome,
    command: Sequence[str] | None,
    collected_nodeids: Sequence[str],
    targeted_nodeids: Sequence[str],
    failed_nodeids: Sequence[str],
    reason: str | None = None,
) -> dict[str, object]:
    """Build a separate broader-suite result with targeted-overlap classification."""

    if not isinstance(outcome, SuiteOutcome):
        raise TestGateConfigurationError("Broader suite outcome must be SuiteOutcome")
    if outcome is SuiteOutcome.NOT_RUN:
        if command or collected_nodeids or failed_nodeids:
            raise TestGateConfigurationError("A not-run broader suite cannot claim execution data")
        if not reason:
            raise TestGateConfigurationError("A not-run broader suite requires a reason")
    elif command is None:
        raise TestGateConfigurationError("An executed broader suite requires its exact command")

    failures = classify_broader_failures(targeted_nodeids, failed_nodeids)
    blocking = sum(
        failure.disposition is BroaderFailureDisposition.BLOCKING_OVERLAP
        for failure in failures
    )
    diagnostic = len(failures) - blocking
    if blocking:
        gate_effect = "blocking-targeted-overlap"
    elif diagnostic:
        gate_effect = "non-gating-diagnostic-only"
    else:
        gate_effect = "none"
    return {
        "schema_version": 1,
        "suite": "broader",
        "reported_separately_from_targeted": True,
        "status": outcome.value,
        "reason": reason,
        "command": list(command) if command is not None else None,
        "collected_count": len(tuple(collected_nodeids)),
        "collected_nodeids": list(collected_nodeids),
        "targeted_manifest_sha256": targeted_manifest_sha256(targeted_nodeids),
        "failure_count": len(failures),
        "blocking_overlap_count": blocking,
        "non_gating_diagnostic_count": diagnostic,
        "targeted_gate_effect": gate_effect,
        "failures": [failure.as_json() for failure in failures],
    }


def write_json_report(path: Path, value: Mapping[str, object]) -> str:
    """Atomically write one deterministic UTF-8 JSON result and return its SHA-256."""

    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        if os.name == "posix":
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(content).hexdigest()
