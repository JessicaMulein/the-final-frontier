"""Central collection, denial, and result reporting for the production test gate."""

from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from frontier_audiobook.production_test_gate import (
    BROADER_ONLY_TEST_NODES,
    TARGETED_CATEGORIES,
    TARGETED_MARKER,
    TARGETED_TEST_FILE_CATEGORIES,
    TARGETED_TEST_NODE_CATEGORIES,
    SuiteOutcome,
    build_broader_suite_report,
    categories_for_test_node,
    inspect_property_runs,
    targeted_manifest_sha256,
    test_node_key,
    write_json_report,
)

_AWS_ENVIRONMENT_NAMES = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_SECURITY_TOKEN",
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_CONFIG_FILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_ROLE_ARN",
    "AWS_CONTAINER_CREDENTIALS_FULL_URI",
    "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
)


@dataclass(slots=True)
class _GateState:
    mode: str | None
    command: tuple[str, ...]
    targeted_report_path: Path | None
    broader_report_path: Path | None
    all_nodeids: list[str] = field(default_factory=list)
    targeted_nodeids: list[str] = field(default_factory=list)
    category_nodeids: dict[str, list[str]] = field(
        default_factory=lambda: {category: [] for category in TARGETED_CATEGORIES}
    )
    outcomes: dict[str, str] = field(default_factory=dict)
    property_runs: tuple[object, ...] = ()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("production-test-gate")
    group.addoption(
        "--production-suite",
        choices=("targeted", "broader"),
        default=None,
        help="Run the explicit production targeted gate or a separately reported broader suite.",
    )
    group.addoption(
        "--production-targeted-report",
        default=None,
        metavar="PATH",
        help="Write the exact targeted collection/result JSON to PATH.",
    )
    group.addoption(
        "--production-broader-report",
        default=None,
        metavar="PATH",
        help="Write the separate broader-suite classification JSON to PATH.",
    )


def _option_path(config: pytest.Config, name: str) -> Path | None:
    value = config.getoption(name)
    return None if value is None else Path(value)


def pytest_configure(config: pytest.Config) -> None:
    for category in TARGETED_CATEGORIES:
        marker = f"production_{category.replace('-', '_')}"
        config.addinivalue_line("markers", f"{marker}: production {category} contract")
    config.addinivalue_line(
        "markers", f"{TARGETED_MARKER}: affected production test in the authorization gate"
    )

    mode = config.getoption("production_suite")
    targeted_path = _option_path(config, "production_targeted_report")
    broader_path = _option_path(config, "production_broader_report")
    if mode == "targeted" and (targeted_path is None or broader_path is None):
        raise pytest.UsageError(
            "The targeted production gate requires both targeted and broader report paths"
        )
    if mode == "broader" and broader_path is None:
        raise pytest.UsageError("The broader production suite requires its report path")

    if mode is not None:
        os.environ["FRONTIER_AUDIOBOOK_DISABLE_AWS"] = "1"
        os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
        os.environ["UV_OFFLINE"] = "1"
        for name in _AWS_ENVIRONMENT_NAMES:
            os.environ.pop(name, None)
    if mode == "targeted":
        config.option.maxfail = 1

    state = _GateState(
        mode=mode,
        command=tuple(sys.argv),
        targeted_report_path=targeted_path,
        broader_report_path=broader_path,
    )
    setattr(config, "_production_gate_state", state)


def _state(config: pytest.Config) -> _GateState:
    return getattr(config, "_production_gate_state")


def _production_test_files(tests_root: Path) -> set[str]:
    return {
        path.name
        for path in tests_root.glob("test_production*.py")
        if path.is_file() and not path.is_symlink()
    } | {"test_property_render_once_catalog.py"}


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    state = _state(config)
    tests_root = Path(__file__).resolve().parent
    actual_files = _production_test_files(tests_root)
    explicit_node_keys = set(TARGETED_TEST_NODE_CATEGORIES) | set(
        BROADER_ONLY_TEST_NODES
    )
    mapped_files = set(TARGETED_TEST_FILE_CATEGORIES) | {
        key.split("::", 1)[0] for key in explicit_node_keys
    }
    missing_mappings = sorted(actual_files.difference(mapped_files))
    missing_files = sorted(mapped_files.difference(actual_files))
    if missing_mappings or missing_files:
        raise pytest.UsageError(
            "Production targeted manifest mismatch: "
            f"unclassified={missing_mappings}, missing={missing_files}"
        )

    state.property_runs = inspect_property_runs(tests_root)
    state.all_nodeids = [item.nodeid for item in items]
    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    seen_explicit_nodes: set[str] = set()
    for item in items:
        file_name = Path(str(item.path)).name
        test_name = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
        key = test_node_key(file_name, test_name)
        if key in explicit_node_keys:
            seen_explicit_nodes.add(key)
        categories = categories_for_test_node(file_name, test_name)
        if not categories:
            if file_name in actual_files and key not in BROADER_ONLY_TEST_NODES:
                raise pytest.UsageError(f"Unclassified production test node: {key}")
            if state.mode == "targeted":
                deselected.append(item)
            continue
        item.add_marker(TARGETED_MARKER)
        selected.append(item)
        state.targeted_nodeids.append(item.nodeid)
        for category in categories:
            item.add_marker(f"production_{category.replace('-', '_')}")
            state.category_nodeids[category].append(item.nodeid)

    missing_explicit_nodes = sorted(explicit_node_keys.difference(seen_explicit_nodes))
    if missing_explicit_nodes:
        raise pytest.UsageError(
            f"Production targeted manifest names missing tests: {missing_explicit_nodes}"
        )
    if not state.targeted_nodeids:
        raise pytest.UsageError("Production targeted gate collected no affected tests")
    empty_categories = [
        category for category, nodeids in state.category_nodeids.items() if not nodeids
    ]
    if empty_categories:
        raise pytest.UsageError(
            f"Production targeted gate has uncovered categories: {empty_categories}"
        )
    if state.mode == "targeted":
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.fixture(autouse=True)
def deny_targeted_network_and_aws_adapters(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
):
    """Deny Python sockets and real AWS/model adapters for every targeted item."""

    if request.node.get_closest_marker(TARGETED_MARKER) is None:
        yield
        return

    def blocked(*_args, **_kwargs):
        raise AssertionError("targeted production tests deny Python network and AWS adapters")

    async def blocked_async(*_args, **_kwargs):
        raise AssertionError("targeted production tests deny Python network and AWS adapters")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("UV_OFFLINE", "1")
    for name in _AWS_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)

    from frontier_audiobook import narrate, nova

    monkeypatch.setattr(narrate, "render_text", blocked)
    for name in ("_render_async", "_render_text_sequence_async"):
        if hasattr(nova, name):
            monkeypatch.setattr(nova, name, blocked_async)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    state = _state(item.config)
    if report.when == "setup" and report.skipped:
        state.outcomes[item.nodeid] = "skipped"
    elif report.when == "setup" and report.failed:
        state.outcomes[item.nodeid] = "failed"
    elif report.when == "call":
        if report.failed:
            state.outcomes[item.nodeid] = "failed"
        elif report.skipped or hasattr(report, "wasxfail"):
            state.outcomes[item.nodeid] = "skipped"
        else:
            state.outcomes[item.nodeid] = "passed"
    elif report.when == "teardown" and report.failed:
        state.outcomes[item.nodeid] = "failed"


def _suite_outcome(exit_code: int) -> SuiteOutcome:
    if exit_code == int(pytest.ExitCode.OK):
        return SuiteOutcome.PASSED
    if exit_code == int(pytest.ExitCode.TESTS_FAILED):
        return SuiteOutcome.FAILED
    if exit_code == int(pytest.ExitCode.INTERRUPTED):
        return SuiteOutcome.INTERRUPTED
    return SuiteOutcome.ERROR


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    state = _state(session.config)
    if state.mode is None:
        return

    if state.mode == "targeted":
        skipped = sorted(
            nodeid
            for nodeid in state.targeted_nodeids
            if state.outcomes.get(nodeid) == "skipped"
        )
        missing = sorted(set(state.targeted_nodeids).difference(state.outcomes))
        if exitstatus == int(pytest.ExitCode.OK) and (skipped or missing):
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
            exitstatus = int(pytest.ExitCode.TESTS_FAILED)
        failures = sorted(
            nodeid
            for nodeid in state.targeted_nodeids
            if state.outcomes.get(nodeid) == "failed"
        )
        target_report = {
            "schema_version": 1,
            "suite": "targeted",
            "requirements": ["4.2", "4.3", "16.1-16.7"],
            "status": _suite_outcome(exitstatus).value,
            "command": list(state.command),
            "return_code": exitstatus,
            "stop_on_first_failure": True,
            "access_controls": {
                "python_network_disabled": True,
                "aws_environment_scrubbed": True,
                "aws_adapter_disabled": True,
                "model_adapter_disabled": True,
                "subprocess_aws_denial_inherited": True,
            },
            "collected_count": len(state.targeted_nodeids),
            "collected_nodeids": state.targeted_nodeids,
            "targeted_manifest_sha256": targeted_manifest_sha256(
                state.targeted_nodeids
            ),
            "categories": state.category_nodeids,
            "property_runs": [run.as_json() for run in state.property_runs],
            "outcomes": {
                "passed": sum(value == "passed" for value in state.outcomes.values()),
                "failed": len(failures),
                "skipped": len(skipped),
                "not_run": len(missing),
            },
            "failed_nodeids": failures,
            "skipped_nodeids": skipped,
            "not_run_nodeids": missing,
        }
        assert state.targeted_report_path is not None
        assert state.broader_report_path is not None
        target_sha256 = write_json_report(state.targeted_report_path, target_report)
        broader_report = build_broader_suite_report(
            outcome=SuiteOutcome.NOT_RUN,
            command=None,
            collected_nodeids=(),
            targeted_nodeids=state.targeted_nodeids,
            failed_nodeids=(),
            reason="not separately requested; implementation acceptance used only the targeted gate",
        )
        broader_report["targeted_result_sha256"] = target_sha256
        write_json_report(state.broader_report_path, broader_report)
        return

    failures = sorted(
        nodeid for nodeid, outcome in state.outcomes.items() if outcome == "failed"
    )
    broader_report = build_broader_suite_report(
        outcome=_suite_outcome(exitstatus),
        command=state.command,
        collected_nodeids=state.all_nodeids,
        targeted_nodeids=state.targeted_nodeids,
        failed_nodeids=failures,
    )
    assert state.broader_report_path is not None
    write_json_report(state.broader_report_path, broader_report)
