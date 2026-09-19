from __future__ import annotations

import json
import socket
import time
from dataclasses import replace
from pathlib import Path

import pytest

import frontier_audiobook.production_transactions as transactions_module
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_models import (
    AudioEncoding,
    AudioFormat,
    EffectiveTrackConfig,
    FidelityPolicy,
    FrozenBatchPlan,
    FrozenTrackPlan,
    SegmentSnapshot,
    SourceKind,
    SourceSnapshot,
    StrictRecordCodec,
    TrackKind,
    TransactionState,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_transactions import (
    DerivedStatusIndex,
    LedgerPayload,
    StatusCacheDisposition,
    TransactionCorruption,
    TransactionHealth,
    TransactionLockUnavailable,
    TransactionSpec,
    TransactionStore,
    reduce_ledger_events,
)


@pytest.fixture(autouse=True)
def deny_python_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("transaction tests must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _hash(character: str) -> str:
    return character * 64


def _spec(
    number: int,
    *,
    plan_id: str = "plan-ledger",
    plan_hash_character: str = "a",
) -> TransactionSpec:
    return TransactionSpec(
        book_id="the-final-frontier",
        plan_id=plan_id,
        plan_sha256=_hash(plan_hash_character),
        transaction_id=f"transaction-{number:03d}",
        track_id=f"chapter-{number:03d}",
        sequence=number,
        track_plan_sha256=_hash(str(number % 10)),
    )


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _effective_config(track_id: str, sequence: int) -> EffectiveTrackConfig:
    return EffectiveTrackConfig(
        track_id=track_id,
        track_kind=TrackKind.CHAPTER,
        sequence=sequence,
        voice="tiffany",
        model_id="amazon.nova-2-sonic-v1:0",
        region="us-east-1",
        profile_label="frontier-audiobook",
        target_segment_words=5,
        fidelity_policy=FidelityPolicy.EXACT,
        normalization="frontier-word-sequence-v1",
        audio_format=AudioFormat(24000, 16, 1, AudioEncoding.PCM_S16LE),
        output_path=f"audiobook-studio/dist/audiobook/{sequence:03d}-{track_id}.wav",
        resolution_provenance={"voice": "defaults", "model_id": "defaults"},
    )


def _track_plan(number: int) -> FrozenTrackPlan:
    track_id = f"chapter-{number:03d}"
    render_hash = _hash(str((number + 2) % 10))
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_hash(str((number + 3) % 10)),
        normalized_tokens_sha256=_hash(str((number + 4) % 10)),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=render_hash,
        render_identity_sha256=_hash(str((number + 5) % 10)),
        spoken_token_count=1,
        narration_only_punctuation=False,
    )
    source = SourceSnapshot(
        track_id=track_id,
        source_path=f"The Final Frontier Novel/chapters/chapter-{number:03d}.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_hash(str((number + 6) % 10)),
        normalized_body_sha256=_hash(str((number + 7) % 10)),
        spoken_sha256=_hash(str((number + 8) % 10)),
        declared_word_count=None,
        normalized_word_count=1,
        spoken_token_count=1,
        segment_count=1,
        segmentation_policy="frontier-safe-segments-v1",
        render_identity_schema="frontier-render-identity-v1",
        render_context_radius=0,
        segments=(segment,),
    )
    argv = (
        "frontier-audiobook",
        "_production-worker",
        "--transaction",
        f"transaction-{number:03d}",
    )
    return FrozenTrackPlan(
        transaction_id=f"transaction-{number:03d}",
        track_id=track_id,
        sequence=number,
        effective_config=_effective_config(track_id, number),
        source=source,
        command_argv=argv,
        command_sha256=canonical_sha256(argv),
        maximum_new_calls=1,
        legacy_candidates=(),
        protected_inventory_sha256=_hash(str((number + 9) % 10)),
    )


def _plan(*numbers: int) -> FrozenBatchPlan:
    return seal_record(
        FrozenBatchPlan(
            schema_version=1,
            plan_id="plan-ledger",
            created_at_utc="2026-09-12T00:00:00Z",
            book_id="the-final-frontier",
            config_path="audiobook-studio/config/production.toml",
            config_sha256=_hash("f"),
            selectors=tuple(f"chapter:{number}" for number in numbers),
            tracks=tuple(_track_plan(number) for number in numbers),
            canonical_sha256="",
        )
    )


def test_materialize_creates_independent_hash_chains_and_is_idempotent(tmp_path):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    first_spec = _spec(1)
    second_spec = _spec(2)

    first = store.materialize_transaction(
        first_spec, occurred_at_utc="2026-09-12T00:00:00Z"
    )
    second = store.materialize_transaction(
        second_spec, occurred_at_utc="2026-09-12T00:00:01Z"
    )

    assert first.state is TransactionState.PLANNED
    assert second.state is TransactionState.PLANNED
    assert tuple(event.sequence for event in first.events) == (1, 2)
    assert first.events[0].previous_event_sha256 is None
    assert first.events[1].previous_event_sha256 == first.events[0].event_sha256
    assert first.metadata.transaction_id != second.metadata.transaction_id
    assert store.transaction_path(first_spec.track_id, first_spec.transaction_id).parent != (
        store.transaction_path(second_spec.track_id, second_spec.transaction_id).parent
    )

    first_root = store.transaction_path(first_spec.track_id, first_spec.transaction_id)
    before = _tree_bytes(first_root)
    repeated = store.materialize_transaction(
        first_spec, occurred_at_utc="2026-09-12T23:59:59Z"
    )
    assert repeated == first
    assert _tree_bytes(first_root) == before

    for event, payload in zip(first.events, first.payloads, strict=True):
        event_path = first_root / "events" / f"{event.sequence:06d}-{event.event_type}.json"
        payload_path = first_root / "payloads" / f"{event.payload_sha256}.json"
        assert StrictRecordCodec(type(event)).load(event_path) == event
        assert StrictRecordCodec(LedgerPayload).load(payload_path) == payload
        assert canonical_sha256(json.loads(payload_path.read_text())) == event.payload_sha256


def test_append_transition_is_strict_and_operation_idempotent(tmp_path):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    spec = _spec(1)
    store.materialize_transaction(spec, occurred_at_utc="2026-09-12T00:00:00Z")

    event = store.append_transition(
        spec.track_id,
        spec.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": _hash("b")},
        occurred_at_utc="2026-09-12T00:01:00Z",
    )
    repeated = store.append_transition(
        spec.track_id,
        spec.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": _hash("b")},
        occurred_at_utc="2026-09-12T00:02:00Z",
    )
    assert repeated == event
    assert len(store.inspect_transaction(spec.track_id, spec.transaction_id).events) == 3

    root = store.transaction_path(spec.track_id, spec.transaction_id)
    before_collision = _tree_bytes(root)
    with pytest.raises(InputError, match="already binds different input"):
        store.append_transition(
            spec.track_id,
            spec.transaction_id,
            operation_id="preflight-passed",
            event_type="preflight-passed",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"preflight_sha256": _hash("c")},
            occurred_at_utc="2026-09-12T00:03:00Z",
        )
    assert _tree_bytes(root) == before_collision

    other = _spec(2)
    store.materialize_transaction(other, occurred_at_utc="2026-09-12T00:00:00Z")
    other_root = store.transaction_path(other.track_id, other.transaction_id)
    before_invalid = _tree_bytes(other_root)
    with pytest.raises(InputError, match="Invalid transaction transition"):
        store.append_transition(
            other.track_id,
            other.transaction_id,
            operation_id="invalid-render",
            event_type="track-rendered",
            state_after=TransactionState.RENDERED,
            details={},
            occurred_at_utc="2026-09-12T00:01:00Z",
        )
    assert _tree_bytes(other_root) == before_invalid


def test_reducer_rejects_gap_broken_hash_and_invalid_transition(tmp_path):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    spec = _spec(1)
    snapshot = store.materialize_transaction(
        spec, occurred_at_utc="2026-09-12T00:00:00Z"
    )
    first, second = snapshot.events

    gap = seal_record(replace(second, sequence=3, event_sha256=""))
    with pytest.raises(TransactionCorruption, match="sequence"):
        reduce_ledger_events((first, gap), transaction_id=spec.transaction_id)

    broken = seal_record(
        replace(second, previous_event_sha256=_hash("d"), event_sha256="")
    )
    with pytest.raises(TransactionCorruption, match="previous-event"):
        reduce_ledger_events((first, broken), transaction_id=spec.transaction_id)

    invalid = seal_record(
        replace(second, state_after=TransactionState.RUNNING, event_sha256="")
    )
    with pytest.raises(TransactionCorruption, match="invalid state transition"):
        reduce_ledger_events((first, invalid), transaction_id=spec.transaction_id)


def test_scoped_lock_fails_fast_without_mutating_and_other_track_remains_available(tmp_path):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    first = _spec(1)
    second = _spec(2)
    store.materialize_transaction(first, occurred_at_utc="2026-09-12T00:00:00Z")
    store.materialize_transaction(second, occurred_at_utc="2026-09-12T00:00:00Z")
    first_root = store.transaction_path(first.track_id, first.transaction_id)
    before = _tree_bytes(first_root)

    with store.track_lock(first.track_id):
        started = time.monotonic()
        with pytest.raises(TransactionLockUnavailable, match="already held"):
            store.append_transition(
                first.track_id,
                first.transaction_id,
                operation_id="preflight-passed",
                event_type="preflight-passed",
                state_after=TransactionState.PREFLIGHT_PASSED,
                details={"preflight_sha256": _hash("b")},
                occurred_at_utc="2026-09-12T00:01:00Z",
            )
        assert time.monotonic() - started < 0.5
        store.append_transition(
            second.track_id,
            second.transaction_id,
            operation_id="preflight-passed",
            event_type="preflight-passed",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"preflight_sha256": _hash("c")},
            occurred_at_utc="2026-09-12T00:01:00Z",
        )

    assert _tree_bytes(first_root) == before
    assert (
        store.inspect_transaction(second.track_id, second.transaction_id).state
        is TransactionState.PREFLIGHT_PASSED
    )


def test_plan_status_lists_every_selected_track_including_missing(tmp_path):
    plan = _plan(1, 2)
    store = TransactionStore(tmp_path / "book", plan.book_id)
    store.materialize_transaction(
        TransactionSpec.from_plan(plan, plan.tracks[0]),
        occurred_at_utc="2026-09-12T00:00:00Z",
    )

    status = store.inspect_plan_status(plan)

    assert status.selected_count == 2
    assert tuple(item.track_id for item in status.tracks) == (
        "chapter-001",
        "chapter-002",
    )
    assert tuple(item.health for item in status.tracks) == (
        TransactionHealth.VALID,
        TransactionHealth.MISSING,
    )
    assert status.unstarted_count == 2


def test_corrupt_transaction_is_fault_isolated_and_status_skips_runtime_audio(
    tmp_path, monkeypatch
):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    first = _spec(1)
    second = _spec(2)
    store.materialize_transaction(first, occurred_at_utc="2026-09-12T00:00:00Z")
    store.materialize_transaction(second, occurred_at_utc="2026-09-12T00:00:00Z")
    store.append_transition(
        second.track_id,
        second.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": _hash("e")},
        occurred_at_utc="2026-09-12T00:01:00Z",
    )

    first_root = store.transaction_path(first.track_id, first.transaction_id)
    event_path = first_root / "events" / "000002-track-planned.json"
    tampered = json.loads(event_path.read_text())
    tampered["unexpected"] = True
    event_path.write_text(json.dumps(tampered, sort_keys=True, separators=(",", ":")))

    second_root = store.transaction_path(second.track_id, second.transaction_id)
    runtime = second_root / "runtime"
    runtime.mkdir()
    (runtime / "segment-001.wav").write_bytes(b"audio-must-not-be-read")
    second_before = _tree_bytes(second_root)

    read_paths: list[Path] = []
    original_read = transactions_module.read_bytes_nofollow

    def recording_read(path: Path) -> bytes:
        read_paths.append(path)
        return original_read(path)

    monkeypatch.setattr(transactions_module, "read_bytes_nofollow", recording_read)
    index = store.rebuild_status_index(rebuilt_at_utc="2026-09-12T00:02:00Z")

    by_track = {item.track_id: item for item in index.transactions}
    assert by_track[first.track_id].health is TransactionHealth.CORRUPT
    assert by_track[first.track_id].corruption_category == "event-chain-invalid"
    assert by_track[second.track_id].health is TransactionHealth.VALID
    assert by_track[second.track_id].state is TransactionState.PREFLIGHT_PASSED
    assert all(path.suffix != ".wav" for path in read_paths)
    assert _tree_bytes(second_root) == second_before
    assert index.plans[0].blocked_count == 1


def test_status_cache_is_rebuilt_from_truth_when_missing_stale_or_corrupt(tmp_path):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    spec = _spec(1)
    store.materialize_transaction(spec, occurred_at_utc="2026-09-12T00:00:00Z")

    missing = store.read_status(rebuilt_at_utc="2026-09-12T00:01:00Z")
    assert missing.cache_disposition is StatusCacheDisposition.MISSING_REBUILT
    first_cache_bytes = store.index_path.read_bytes()

    current = store.read_status(rebuilt_at_utc="2026-09-12T00:02:00Z")
    assert current.cache_disposition is StatusCacheDisposition.CURRENT
    assert current.index == missing.index
    assert store.index_path.read_bytes() == first_cache_bytes

    store.append_transition(
        spec.track_id,
        spec.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": _hash("b")},
        occurred_at_utc="2026-09-12T00:03:00Z",
    )
    stale = store.read_status(rebuilt_at_utc="2026-09-12T00:04:00Z")
    assert stale.cache_disposition is StatusCacheDisposition.STALE_REBUILT
    assert stale.index.transactions[0].state is TransactionState.PREFLIGHT_PASSED

    transaction_root = store.transaction_path(spec.track_id, spec.transaction_id)
    truth_before = _tree_bytes(transaction_root)
    store.index_path.write_bytes(b"{malformed-cache")
    repaired = store.read_status(rebuilt_at_utc="2026-09-12T00:05:00Z")
    assert repaired.cache_disposition is StatusCacheDisposition.CORRUPT_REBUILT
    assert repaired.index.transactions[0].state is TransactionState.PREFLIGHT_PASSED
    assert _tree_bytes(transaction_root) == truth_before
    assert StrictRecordCodec(DerivedStatusIndex).load(store.index_path) == repaired.index


def test_interrupted_materialization_retains_staging_and_never_publishes_partial_root(
    tmp_path, monkeypatch
):
    store = TransactionStore(tmp_path / "book", "the-final-frontier")
    spec = _spec(1)
    original_replace = transactions_module.durable_replace

    def fail_final_directory(source: Path, destination: Path, *, source_kind: str):
        if source_kind == "directory":
            raise InputError("injected final transaction commit failure")
        return original_replace(source, destination, source_kind=source_kind)

    monkeypatch.setattr(transactions_module, "durable_replace", fail_final_directory)
    with pytest.raises(InputError, match="injected final transaction commit failure"):
        store.materialize_transaction(
            spec, occurred_at_utc="2026-09-12T00:00:00Z"
        )

    final_root = store.transaction_path(spec.track_id, spec.transaction_id)
    assert not final_root.exists()
    staging = tuple(
        path
        for path in final_root.parent.iterdir()
        if path.name.startswith(f".{spec.transaction_id}.staging-")
    )
    assert len(staging) == 1

    monkeypatch.setattr(transactions_module, "durable_replace", original_replace)
    with pytest.raises(TransactionCorruption, match="requires inspection"):
        store.materialize_transaction(
            spec, occurred_at_utc="2026-09-12T00:01:00Z"
        )
