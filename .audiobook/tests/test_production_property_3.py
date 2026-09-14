"""Deterministic model-based checks for production correctness Property 3."""

from __future__ import annotations

import json
import os
import random
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

import pytest

import frontier_audiobook.production_transactions as transactions_module
from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_models import (
    LedgerEvent,
    StrictRecordCodec,
    TransactionState,
    seal_record,
)
from frontier_audiobook.production_transactions import (
    DerivedStatusIndex,
    LedgerPayload,
    StatusCacheDisposition,
    TransactionCorruption,
    TransactionHealth,
    TransactionSpec,
    TransactionStore,
    reduce_ledger_events,
)
from frontier_audiobook.util import sha256_bytes


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 3: Transaction truth is independently reconstructable"
PROPERTY_SEED = 0x3A11CE55
GENERATED_SEQUENCES = 100

# **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8,
# 5.9, 5.10, 5.11, 5.12**

_MODEL_TRANSITIONS: dict[TransactionState, tuple[TransactionState, ...]] = {
    TransactionState.PLANNED: (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.BLOCKED,
    ),
    TransactionState.PREFLIGHT_PASSED: (
        TransactionState.AUTHORIZATION_REQUIRED,
    ),
    TransactionState.AUTHORIZATION_REQUIRED: (
        TransactionState.RUNNING,
        TransactionState.BLOCKED,
    ),
    TransactionState.RUNNING: (
        TransactionState.RENDERED,
        TransactionState.CHARGE_UNCERTAIN,
        TransactionState.BLOCKED,
    ),
    TransactionState.CHARGE_UNCERTAIN: (
        TransactionState.RENDERED,
        TransactionState.BLOCKED,
    ),
    TransactionState.RENDERED: (
        TransactionState.VALIDATED,
        TransactionState.BLOCKED,
    ),
    TransactionState.VALIDATED: (
        TransactionState.DELIVERED,
        TransactionState.BLOCKED,
    ),
    TransactionState.DELIVERED: (),
    TransactionState.BLOCKED: (),
}

_MODEL_PATHS: tuple[tuple[TransactionState, ...], ...] = (
    (),
    (TransactionState.PREFLIGHT_PASSED,),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.RENDERED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
        TransactionState.DELIVERED,
    ),
    (TransactionState.BLOCKED,),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.BLOCKED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.BLOCKED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.CHARGE_UNCERTAIN,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.CHARGE_UNCERTAIN,
        TransactionState.RENDERED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.CHARGE_UNCERTAIN,
        TransactionState.BLOCKED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.CHARGE_UNCERTAIN,
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
        TransactionState.DELIVERED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.RENDERED,
        TransactionState.BLOCKED,
    ),
    (
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
        TransactionState.BLOCKED,
    ),
)

_CORRUPTION_KINDS = (
    "event-unknown-field",
    "event-malformed",
    "event-digest",
    "event-previous-hash",
    "event-sequence-gap",
    "event-invalid-transition",
    "payload-missing",
    "payload-unknown-field",
)
_CACHE_MODES = ("missing", "corrupt", "stale")
_INTERRUPTION_POINTS = (
    "metadata-write",
    "payload-write",
    "event-write",
    "final-publish",
    "append-event-write",
)
_BASE_TIME = datetime(2026, 9, 12, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class _GeneratedSequence:
    model_path: tuple[TransactionState, ...]
    corruption_kind: str
    cache_mode: str
    interruption_point: str | None
    detail_nonce: int


@pytest.fixture(autouse=True)
def deny_network_aws_model_and_render(monkeypatch):
    """Fail immediately if a local ledger property crosses an external boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 3 must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _shuffled_cycle(rng: random.Random, values: tuple[object, ...]) -> Iterator[object]:
    while True:
        batch = list(values)
        rng.shuffle(batch)
        yield from batch


def _generated_sequences(rng: random.Random) -> Iterator[_GeneratedSequence]:
    paths = _shuffled_cycle(rng, _MODEL_PATHS)
    corruptions = _shuffled_cycle(rng, _CORRUPTION_KINDS)
    cache_modes = _shuffled_cycle(rng, _CACHE_MODES)
    interruption_choices: tuple[str | None, ...] = (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        *_INTERRUPTION_POINTS,
    )
    interruptions = _shuffled_cycle(rng, interruption_choices)
    for _ in range(GENERATED_SEQUENCES):
        yield _GeneratedSequence(
            model_path=next(paths),  # type: ignore[arg-type]
            corruption_kind=next(corruptions),  # type: ignore[arg-type]
            cache_mode=next(cache_modes),  # type: ignore[arg-type]
            interruption_point=next(interruptions),  # type: ignore[arg-type]
            detail_nonce=rng.randrange(1_000_000_000),
        )


def _digest(value: int) -> str:
    return f"{value:064x}"


def _timestamp(case_index: int, step: int) -> str:
    value = _BASE_TIME + timedelta(seconds=case_index * 120 + step)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _spec(case_index: int, track_number: int) -> TransactionSpec:
    return TransactionSpec(
        book_id="the-final-frontier",
        plan_id=f"property-three-{case_index:03d}",
        plan_sha256=_digest((case_index + 1) * 1_000),
        transaction_id=f"transaction-{case_index:03d}-{track_number:03d}",
        track_id=f"chapter-{case_index * 3 + track_number:03d}",
        sequence=track_number,
        track_plan_sha256=_digest((case_index + 1) * 1_000 + track_number),
    )


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _assert_snapshot_matches_model(
    store: TransactionStore,
    spec: TransactionSpec,
    model_path: tuple[TransactionState, ...],
) -> None:
    snapshot = store.inspect_transaction(spec.track_id, spec.transaction_id)
    expected_states = (
        TransactionState.DISCOVERED,
        TransactionState.PLANNED,
        *model_path,
    )
    assert tuple(event.state_after for event in snapshot.events) == expected_states
    assert snapshot.state is expected_states[-1]
    assert reduce_ledger_events(
        snapshot.events, transaction_id=spec.transaction_id
    ) is expected_states[-1]

    previous_hash: str | None = None
    previous_state: TransactionState | None = None
    previous_timestamp = ""
    for expected_sequence, (event, payload) in enumerate(
        zip(snapshot.events, snapshot.payloads, strict=True), start=1
    ):
        event_bytes = StrictRecordCodec(LedgerEvent).dump_bytes(event)
        assert StrictRecordCodec(LedgerEvent).loads(event_bytes) == event
        payload_bytes = StrictRecordCodec(LedgerPayload).dump_bytes(payload)
        assert StrictRecordCodec(LedgerPayload).loads(payload_bytes) == payload
        assert sha256_bytes(payload_bytes) == event.payload_sha256
        assert event.sequence == expected_sequence
        assert event.previous_event_sha256 == previous_hash
        assert event.state_before is previous_state
        assert event.occurred_at_utc >= previous_timestamp
        assert payload.transaction_id == spec.transaction_id
        assert payload.event_type == event.event_type
        assert payload.state_after is event.state_after
        previous_hash = event.event_sha256
        previous_state = event.state_after
        previous_timestamp = event.occurred_at_utc


def _apply_model_sequence(
    store: TransactionStore,
    spec: TransactionSpec,
    sequence: _GeneratedSequence,
    case_index: int,
) -> None:
    initial = store.materialize_transaction(
        spec, occurred_at_utc=_timestamp(case_index, 0)
    )
    transaction_root = store.transaction_path(spec.track_id, spec.transaction_id)
    initial_bytes = _tree_bytes(transaction_root)
    repeated_materialization = store.materialize_transaction(
        spec, occurred_at_utc=_timestamp(case_index, 100)
    )
    assert repeated_materialization == initial
    assert _tree_bytes(transaction_root) == initial_bytes

    current_state = TransactionState.PLANNED
    for step, target_state in enumerate(sequence.model_path, start=1):
        assert target_state in _MODEL_TRANSITIONS[current_state]
        operation_id = f"model-step-{step:02d}"
        event_type = f"model-{target_state.value}"
        details = {
            "case_index": case_index,
            "detail_nonce": sequence.detail_nonce,
            "model_step": step,
        }
        before_count = len(
            store.inspect_transaction(spec.track_id, spec.transaction_id).events
        )
        event = store.append_transition(
            spec.track_id,
            spec.transaction_id,
            operation_id=operation_id,
            event_type=event_type,
            state_after=target_state,
            details=details,
            occurred_at_utc=_timestamp(case_index, step),
        )
        assert event.sequence == before_count + 1
        after_first_write = _tree_bytes(transaction_root)
        repeated = store.append_transition(
            spec.track_id,
            spec.transaction_id,
            operation_id=operation_id,
            event_type=event_type,
            state_after=target_state,
            details=details,
            occurred_at_utc=_timestamp(case_index, 60 + step),
        )
        assert repeated == event
        assert _tree_bytes(transaction_root) == after_first_write
        current_state = target_state

    _assert_snapshot_matches_model(store, spec, sequence.model_path)


def _race_same_next_sequence(
    store: TransactionStore,
    spec: TransactionSpec,
    case_index: int,
    detail_nonce: int,
) -> None:
    store.materialize_transaction(spec, occurred_at_utc=_timestamp(case_index, 0))
    transaction_root = store.transaction_path(spec.track_id, spec.transaction_id)
    before_count = len(store.inspect_transaction(spec.track_id, spec.transaction_id).events)
    barrier = threading.Barrier(2)

    def writer(name: str) -> tuple[str, str, LedgerEvent | InputError]:
        barrier.wait(timeout=10)
        try:
            event = store.append_transition(
                spec.track_id,
                spec.transaction_id,
                operation_id=f"race-{name}",
                event_type="race-preflight-passed",
                state_after=TransactionState.PREFLIGHT_PASSED,
                details={"detail_nonce": detail_nonce, "writer": name},
                occurred_at_utc=_timestamp(case_index, 20),
            )
        except InputError as exc:
            return "rejected", name, exc
        return "committed", name, event

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(writer, ("left", "right")))

    committed = tuple(result for result in results if result[0] == "committed")
    rejected = tuple(result for result in results if result[0] == "rejected")
    assert len(committed) == 1
    assert len(rejected) == 1
    assert isinstance(committed[0][2], LedgerEvent)
    assert isinstance(rejected[0][2], InputError)

    winner = committed[0][1]
    winning_event = committed[0][2]
    assert isinstance(winning_event, LedgerEvent)
    snapshot = store.inspect_transaction(spec.track_id, spec.transaction_id)
    assert len(snapshot.events) == before_count + 1
    assert snapshot.events[-1] == winning_event
    assert snapshot.state is TransactionState.PREFLIGHT_PASSED

    after_race = _tree_bytes(transaction_root)
    repeated = store.append_transition(
        spec.track_id,
        spec.transaction_id,
        operation_id=f"race-{winner}",
        event_type="race-preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"detail_nonce": detail_nonce, "writer": winner},
        occurred_at_utc=_timestamp(case_index, 21),
    )
    assert repeated == winning_event
    assert _tree_bytes(transaction_root) == after_race


def _exercise_interruption(
    store: TransactionStore,
    spec: TransactionSpec,
    point: str,
    case_index: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    final_root = store.transaction_path(spec.track_id, spec.transaction_id)

    if point == "append-event-write":
        store.materialize_transaction(spec, occurred_at_utc=_timestamp(case_index, 30))
        original_write = transactions_module._write_exclusive_atomic

        def fail_append_event(path: Path, content: bytes) -> None:
            if path.parent == final_root / "events" and path.name.startswith("000003-"):
                raise InputError("injected append event interruption")
            original_write(path, content)

        with monkeypatch.context() as patch:
            patch.setattr(
                transactions_module, "_write_exclusive_atomic", fail_append_event
            )
            with pytest.raises(InputError, match="injected append event interruption"):
                store.append_transition(
                    spec.track_id,
                    spec.transaction_id,
                    operation_id="interrupted-preflight",
                    event_type="interrupted-preflight",
                    state_after=TransactionState.PREFLIGHT_PASSED,
                    details={"interruption": point},
                    occurred_at_utc=_timestamp(case_index, 31),
                )

        interrupted = store.inspect_transaction(spec.track_id, spec.transaction_id)
        assert interrupted.state is TransactionState.PLANNED
        assert len(interrupted.events) == 2
        recovered = store.append_transition(
            spec.track_id,
            spec.transaction_id,
            operation_id="interrupted-preflight",
            event_type="interrupted-preflight",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"interruption": point},
            occurred_at_utc=_timestamp(case_index, 32),
        )
        recovered_bytes = _tree_bytes(final_root)
        assert (
            store.append_transition(
                spec.track_id,
                spec.transaction_id,
                operation_id="interrupted-preflight",
                event_type="interrupted-preflight",
                state_after=TransactionState.PREFLIGHT_PASSED,
                details={"interruption": point},
                occurred_at_utc=_timestamp(case_index, 33),
            )
            == recovered
        )
        assert _tree_bytes(final_root) == recovered_bytes
        return

    original_write = transactions_module._write_exclusive_atomic
    original_replace = transactions_module.durable_replace

    def fail_materialization_write(path: Path, content: bytes) -> None:
        should_fail = (
            point == "metadata-write"
            and path.name == "transaction.json"
            or point == "payload-write"
            and path.parent.name == "payloads"
            or point == "event-write"
            and path.parent.name == "events"
        )
        if should_fail:
            raise InputError(f"injected {point} interruption")
        original_write(path, content)

    def fail_final_publish(
        source: Path, destination: Path, *, source_kind: str
    ) -> None:
        if (
            point == "final-publish"
            and source_kind == "directory"
            and destination == final_root
        ):
            raise InputError("injected final-publish interruption")
        original_replace(source, destination, source_kind=source_kind)

    with monkeypatch.context() as patch:
        patch.setattr(
            transactions_module,
            "_write_exclusive_atomic",
            fail_materialization_write,
        )
        patch.setattr(transactions_module, "durable_replace", fail_final_publish)
        with pytest.raises(InputError, match=f"injected {point} interruption"):
            store.materialize_transaction(
                spec, occurred_at_utc=_timestamp(case_index, 30)
            )

    assert not os.path.lexists(final_root)
    staging = tuple(
        path
        for path in final_root.parent.iterdir()
        if path.name.startswith(f".{spec.transaction_id}.staging-")
    )
    assert len(staging) == 1
    with pytest.raises(TransactionCorruption, match="requires inspection"):
        store.materialize_transaction(
            spec, occurred_at_utc=_timestamp(case_index, 31)
        )


def _event_path(root: Path, event: LedgerEvent) -> Path:
    return root / "events" / f"{event.sequence:06d}-{event.event_type}.json"


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _corrupt_transaction(
    store: TransactionStore,
    spec: TransactionSpec,
    corruption_kind: str,
) -> str:
    snapshot = store.inspect_transaction(spec.track_id, spec.transaction_id)
    root = store.transaction_path(spec.track_id, spec.transaction_id)
    event = snapshot.events[-1]
    event_path = _event_path(root, event)

    if corruption_kind == "event-unknown-field":
        value = json.loads(event_path.read_bytes())
        value["unexpected"] = True
        _write_json(event_path, value)
    elif corruption_kind == "event-malformed":
        event_path.write_bytes(b"{malformed-event")
    elif corruption_kind == "event-digest":
        value = json.loads(event_path.read_bytes())
        value["event_sha256"] = "0" * 64
        _write_json(event_path, value)
    elif corruption_kind == "event-previous-hash":
        value = json.loads(event_path.read_bytes())
        value["previous_event_sha256"] = "f" * 64
        _write_json(event_path, value)
    elif corruption_kind == "event-sequence-gap":
        event_path.rename(
            root
            / "events"
            / f"{event.sequence + 1:06d}-{event.event_type}.json"
        )
    elif corruption_kind == "event-invalid-transition":
        planned_event = snapshot.events[1]
        invalid_event = seal_record(
            replace(
                planned_event,
                state_after=TransactionState.RUNNING,
                event_sha256="",
            )
        )
        _event_path(root, planned_event).write_bytes(
            StrictRecordCodec(LedgerEvent).dump_bytes(invalid_event)
        )
    elif corruption_kind == "payload-missing":
        (root / "payloads" / f"{event.payload_sha256}.json").unlink()
    elif corruption_kind == "payload-unknown-field":
        payload_path = root / "payloads" / f"{event.payload_sha256}.json"
        value = json.loads(payload_path.read_bytes())
        value["unexpected"] = True
        _write_json(payload_path, value)
    else:  # pragma: no cover - generated values are closed above
        raise AssertionError(f"unknown corruption kind: {corruption_kind}")

    expected_category = (
        "payload-invalid"
        if corruption_kind.startswith("payload-")
        else "event-chain-invalid"
    )
    with pytest.raises(TransactionCorruption) as raised:
        store.inspect_transaction(spec.track_id, spec.transaction_id)
    assert raised.value.category == expected_category
    return expected_category


def _status_truth(status) -> tuple[object, ...]:
    return (
        status.health,
        status.state,
        status.event_count,
        status.head_event_sha256,
        status.corruption_category,
    )


def test_property_3_transaction_truth_is_independently_reconstructable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert GENERATED_SEQUENCES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; sequences={GENERATED_SEQUENCES}")
    rng = random.Random(PROPERTY_SEED)
    generated = tuple(_generated_sequences(rng))
    assert len(generated) == GENERATED_SEQUENCES

    observed_paths: set[tuple[TransactionState, ...]] = set()
    observed_edges: set[tuple[TransactionState, TransactionState]] = set()
    observed_corruptions: set[str] = set()
    observed_cache_modes: set[str] = set()
    observed_interruptions: set[str] = set()

    for case_index, sequence in enumerate(generated):
        context = f"seed={PROPERTY_SEED}, sequence={case_index}, case={sequence!r}"
        try:
            case_root = tmp_path / f"sequence-{case_index:03d}"
            store = TransactionStore(case_root / "book", "the-final-frontier")
            subject_spec = _spec(case_index, 1)
            witness_spec = _spec(case_index, 2)

            observed_paths.add(sequence.model_path)
            previous = TransactionState.PLANNED
            for state in sequence.model_path:
                observed_edges.add((previous, state))
                previous = state

            _apply_model_sequence(
                store, subject_spec, sequence, case_index
            )
            _race_same_next_sequence(
                store,
                witness_spec,
                case_index,
                sequence.detail_nonce,
            )
            assert store.transaction_path(
                subject_spec.track_id, subject_spec.transaction_id
            ) != store.transaction_path(
                witness_spec.track_id, witness_spec.transaction_id
            )

            if sequence.interruption_point is not None:
                observed_interruptions.add(sequence.interruption_point)
                _exercise_interruption(
                    store,
                    _spec(case_index, 3),
                    sequence.interruption_point,
                    case_index,
                    monkeypatch,
                )

            baseline = store.read_status(
                rebuilt_at_utc=_timestamp(case_index, 40)
            )
            assert (
                baseline.cache_disposition
                is StatusCacheDisposition.MISSING_REBUILT
            )
            baseline_by_transaction = {
                item.transaction_id: item for item in baseline.index.transactions
            }
            assert (
                baseline_by_transaction[subject_spec.transaction_id].health
                is TransactionHealth.VALID
            )
            assert (
                baseline_by_transaction[witness_spec.transaction_id].state
                is TransactionState.PREFLIGHT_PASSED
            )
            unaffected_truth = {
                transaction_id: _status_truth(status)
                for transaction_id, status in baseline_by_transaction.items()
                if transaction_id != subject_spec.transaction_id
            }
            witness_root = store.transaction_path(
                witness_spec.track_id, witness_spec.transaction_id
            )
            witness_bytes = _tree_bytes(witness_root)

            observed_cache_modes.add(sequence.cache_mode)
            if sequence.cache_mode == "missing":
                store.index_path.unlink()
                expected_disposition = StatusCacheDisposition.MISSING_REBUILT
            elif sequence.cache_mode == "corrupt":
                store.index_path.write_bytes(b"{malformed-derived-index")
                expected_disposition = StatusCacheDisposition.CORRUPT_REBUILT
            else:
                expected_disposition = StatusCacheDisposition.STALE_REBUILT

            observed_corruptions.add(sequence.corruption_kind)
            expected_category = _corrupt_transaction(
                store, subject_spec, sequence.corruption_kind
            )
            repaired = store.read_status(
                rebuilt_at_utc=_timestamp(case_index, 41)
            )
            assert repaired.cache_disposition is expected_disposition
            repaired_by_transaction = {
                item.transaction_id: item for item in repaired.index.transactions
            }
            corrupt_status = repaired_by_transaction[subject_spec.transaction_id]
            assert corrupt_status.health is TransactionHealth.CORRUPT
            assert corrupt_status.state is None
            assert corrupt_status.corruption_category == expected_category
            for transaction_id, truth in unaffected_truth.items():
                assert _status_truth(repaired_by_transaction[transaction_id]) == truth
            assert _tree_bytes(witness_root) == witness_bytes

            plan_status = next(
                item
                for item in repaired.index.plans
                if item.plan_id == subject_spec.plan_id
                and item.plan_sha256 == subject_spec.plan_sha256
            )
            assert plan_status.blocked_count >= 1
            assert (
                StrictRecordCodec(DerivedStatusIndex).load(store.index_path)
                == repaired.index
            )

            cache_bytes = store.index_path.read_bytes()
            repeated_status = store.read_status(
                rebuilt_at_utc=_timestamp(case_index, 42)
            )
            assert (
                repeated_status.cache_disposition
                is StatusCacheDisposition.CURRENT
            )
            assert repeated_status.index == repaired.index
            assert store.index_path.read_bytes() == cache_bytes
            assert _tree_bytes(witness_root) == witness_bytes
        except Exception as exc:
            exc.add_note(context)
            raise

    expected_edges = {
        (source, target)
        for source, targets in _MODEL_TRANSITIONS.items()
        for target in targets
    }
    assert observed_paths == set(_MODEL_PATHS)
    assert observed_edges == expected_edges
    assert observed_corruptions == set(_CORRUPTION_KINDS)
    assert observed_cache_modes == set(_CACHE_MODES)
    assert observed_interruptions == set(_INTERRUPTION_POINTS)
