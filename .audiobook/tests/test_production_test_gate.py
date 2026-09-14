from __future__ import annotations

import json
from pathlib import Path

from frontier_audiobook.production_test_gate import (
    BROADER_ONLY_TEST_NODES,
    PROPERTY_SPECS,
    TARGETED_CATEGORIES,
    TARGETED_TEST_FILE_CATEGORIES,
    TARGETED_TEST_NODE_CATEGORIES,
    BroaderFailureDisposition,
    SuiteOutcome,
    build_broader_suite_report,
    classify_broader_failures,
    inspect_property_runs,
    write_json_report,
)


def _actual_production_test_files() -> set[str]:
    tests_root = Path(__file__).resolve().parent
    return {
        path.name
        for path in tests_root.glob("test_production*.py")
        if path.is_file() and not path.is_symlink()
    } | {"test_property_render_once_catalog.py"}


def test_targeted_manifest_classifies_every_production_test_and_required_category():
    """Requirements 16.1: every affected module is explicit and every category is covered."""

    known_files = set(TARGETED_TEST_FILE_CATEGORIES) | {
        key.split("::", 1)[0]
        for key in (*TARGETED_TEST_NODE_CATEGORIES, *BROADER_ONLY_TEST_NODES)
    }
    assert known_files == _actual_production_test_files()
    assert set(TARGETED_TEST_NODE_CATEGORIES).isdisjoint(BROADER_ONLY_TEST_NODES)
    assert set(TARGETED_CATEGORIES) == {
        category
        for categories in (
            *TARGETED_TEST_FILE_CATEGORIES.values(),
            *TARGETED_TEST_NODE_CATEGORIES.values(),
        )
        for category in categories
    }
    assert all(categories for categories in TARGETED_TEST_FILE_CATEGORIES.values())
    assert all(categories for categories in TARGETED_TEST_NODE_CATEGORIES.values())


def test_property_manifest_reports_all_fixed_seeds_and_at_least_100_cases():
    """Requirement 16.3: all designed properties report deterministic seeds and cases."""

    tests_root = Path(__file__).resolve().parent
    runs = inspect_property_runs(tests_root)

    assert tuple(run.number for run in runs) == tuple(range(1, 17))
    assert tuple(spec.number for spec in PROPERTY_SPECS) == tuple(range(1, 17))
    assert all(run.seed >= 0 for run in runs)
    assert all(run.cases >= 100 for run in runs)
    assert len({(run.file_name, run.seed) for run in runs}) == 16
    assert {run.case_unit for run in runs} == {"cases", "sequences"}


def test_broader_failures_are_separately_classified_by_targeted_overlap():
    """Requirements 16.5-16.7: broader failures retain blocking/diagnostic meaning."""

    targeted = (
        "tests/test_production_config.py::test_parse",
        "tests/test_production_config.py::test_print",
    )
    failures = (
        "tests/test_production_config.py::test_new_case",
        "tests/test_audition.py::test_unrelated",
    )

    classified = classify_broader_failures(targeted, failures)

    assert tuple(item.disposition for item in classified) == (
        BroaderFailureDisposition.BLOCKING_OVERLAP,
        BroaderFailureDisposition.NON_GATING_DIAGNOSTIC,
    )
    report = build_broader_suite_report(
        outcome=SuiteOutcome.FAILED,
        command=("python", "-m", "pytest"),
        collected_nodeids=targeted + failures,
        targeted_nodeids=targeted,
        failed_nodeids=failures,
    )
    assert report["reported_separately_from_targeted"] is True
    assert report["blocking_overlap_count"] == 1
    assert report["non_gating_diagnostic_count"] == 1
    assert report["targeted_gate_effect"] == "blocking-targeted-overlap"


def test_not_run_broader_result_is_separate_and_json_report_is_deterministic(tmp_path):
    """Requirement 16.5: an unrequested broader suite is explicit, never implied passed."""

    report = build_broader_suite_report(
        outcome=SuiteOutcome.NOT_RUN,
        command=None,
        collected_nodeids=(),
        targeted_nodeids=("tests/test_production.py::test_plan",),
        failed_nodeids=(),
        reason="not separately requested",
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    first_sha256 = write_json_report(first, report)
    second_sha256 = write_json_report(second, report)

    assert report["status"] == "not-run"
    assert report["reported_separately_from_targeted"] is True
    assert first_sha256 == second_sha256
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8")) == report
