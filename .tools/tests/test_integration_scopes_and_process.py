"""Integration and process-smoke tests for task 8.26.

Validates: Requirements 9.3, 9.11, 10.1, 11.1-11.9, 13.3, 14.1-14.14, and
15.1-15.4.

The property and focused suites test rules one at a time against records held in
memory. This file runs the checker the way a person runs it: over a workspace on
disk, at each of the three runnable scopes, and then across the whole approval
process from planning to reapproval.

What is being proved
--------------------
That the pieces compose. A rule that works in isolation can still be unreachable
in the assembled program -- which is exactly what happened to the planning-side
reference checks, defined and tested and never called by any scope until the gap
was found. These tests exercise the entry points a caller actually uses, so a
check that stops being wired in fails here.

The process flow test is the one that spans the most: it walks a Baseline from
provisional through exploratory calibration, full-suite evidence, one
Baseline_Revision_Pass, author approval, a revision that supersedes it, and
reapproval. It asserts the evidence obligations at each step, and nothing about
whether any of the prose is good.

Synthetic records and prose throughout. No test here evaluates artistry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pytest

import novel_fixtures as nf

checker = nf.load_checker()

CALIBRATION_CHAPTERS = (1, 2, 3, 4, 5, 73, 118, 124)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exit_status(diagnostics: Sequence[Any]) -> int:
    """The process exit status for a set of diagnostics, via the real contract."""

    return checker.exit_status_for_result(checker.classify_result(diagnostics))


def _codes(diagnostics: Sequence[Any]) -> List[str]:
    return [item.code for item in diagnostics]


def _chapter_paths(workspace: Any) -> Tuple[Any, ...]:
    """Every Chapter_File in a workspace, in path order."""

    return tuple(sorted(workspace.manuscript_root.rglob("chapters/**/*.md")))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def calibration(tmp_path_factory) -> Any:
    """The eight-chapter calibration workspace, built once for the module."""

    return nf.calibration_workspace(tmp_path_factory.mktemp("calibration"))


@pytest.fixture(scope="module")
def manuscript(tmp_path_factory) -> Any:
    """The complete 128-chapter workspace, built once for the module.

    Building this is the expensive part of the suite, so it is shared. Every test
    using it treats it as read-only.
    """

    return nf.manuscript_workspace(tmp_path_factory.mktemp("manuscript"))


# ---------------------------------------------------------------------------
# Site isolation
# ---------------------------------------------------------------------------


def test_the_site_generator_is_isolated_from_the_manuscript(calibration) -> None:
    """Requirement 13.3: novel prose is outside the site's publishing surface.

    The site run succeeds by *collecting nothing* from the manuscript. Asserting on
    the collected set rather than on an exit code is what makes the claim specific:
    a run that silently skipped the scan would also raise no error.
    """

    result = checker.run_site_exclusion(calibration.root)
    collected = sorted(source.relative_path for source in result.sources)
    assert collected == ["songs/control-song.md"], collected
    assert not any(
        path.startswith(nf.MANUSCRIPT_ROOT_NAME) for path in collected
    ), collected


def test_site_isolation_and_the_manuscript_gate_are_separate_runs(
    calibration,
) -> None:
    """Two contracts, two runs: a clean site says nothing about a clean manuscript.

    Collapsing them would let a passing site exclusion be read as evidence about
    the prose, or a manuscript violation as a publishing failure. The site run also
    refuses to claim external adoption, which is a promise about the real
    generator that no local run is in a position to make.
    """

    site = checker.run_site_exclusion(calibration.root)
    gate = checker.run_scope(
        _chapter_paths(calibration)[:1],
        scope=checker.SCOPE_CHAPTER,
        manuscript_root=calibration.manuscript_root,
    )
    assert site.external_adoption_verified is False
    assert _exit_status(gate.diagnostics) == 0, _codes(gate.diagnostics)


# ---------------------------------------------------------------------------
# The three runnable scopes
# ---------------------------------------------------------------------------


def test_the_minimal_calibration_gate_passes_on_the_eight_chapters(
    calibration,
) -> None:
    """Requirement 10.1: the calibration set gates as one batch at exit 0."""

    paths = _chapter_paths(calibration)
    assert len(paths) == len(CALIBRATION_CHAPTERS), [p.name for p in paths]

    run = checker.run_scope(
        paths,
        scope=checker.SCOPE_BATCH,
        manuscript_root=calibration.manuscript_root,
        batch_kind="calibration",
    )
    assert _exit_status(run.diagnostics) == 0, _codes(run.diagnostics)


@pytest.mark.parametrize("position", (0, 3, 7))
def test_chapter_local_scope_gates_one_chapter_at_a_time(
    calibration, position: int
) -> None:
    """A Chapter_Local_Gate reads one Chapter_File and its local references."""

    path = _chapter_paths(calibration)[position]
    run = checker.run_scope(
        (path,),
        scope=checker.SCOPE_CHAPTER,
        manuscript_root=calibration.manuscript_root,
    )
    assert run.scope == checker.SCOPE_CHAPTER
    assert _exit_status(run.diagnostics) == 0, _codes(run.diagnostics)


def test_a_changed_reference_batch_gates_the_affected_chapters(
    calibration,
) -> None:
    """A batch run carries the changed references that caused it.

    The batch exists because something upstream moved, so the run records what
    moved rather than leaving the reason outside the evidence.
    """

    paths = _chapter_paths(calibration)
    run = checker.run_scope(
        paths,
        scope=checker.SCOPE_BATCH,
        manuscript_root=calibration.manuscript_root,
        batch_kind="calibration",
        changed_references=("planning/arc-outline.md", "planning/motif-ledger.md"),
    )
    assert run.batch_kind == "calibration"
    assert run.changed_references == (
        "planning/arc-outline.md",
        "planning/motif-ledger.md",
    )
    assert _exit_status(run.diagnostics) == 0, _codes(run.diagnostics)


def test_a_drafting_batch_outside_its_size_range_is_rejected(calibration) -> None:
    """A drafting batch has a size range, and two chapters is below it.

    The same eight files pass as a calibration batch and fail as a drafting one,
    which is the point: the kind of batch changes what counts as a batch.
    """

    paths = _chapter_paths(calibration)[:2]
    run = checker.run_scope(
        paths,
        scope=checker.SCOPE_BATCH,
        manuscript_root=calibration.manuscript_root,
        batch_kind="drafting",
    )
    assert "BATCH_SIZE_OUT_OF_RANGE" in _codes(run.diagnostics), _codes(
        run.diagnostics
    )


def test_the_complete_global_scope_passes_on_128_entries(manuscript) -> None:
    """Requirements 11.1 to 11.9: the whole book gates at exit 0.

    This is the run task 8.27 records as `baseline-objective` evidence, so it has
    to be clean for the right reason -- a complete, consistent manuscript -- and
    not because some check quietly failed to run.
    """

    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=manuscript.manuscript_root
    )
    assert run.scope == checker.SCOPE_GLOBAL
    assert run.diagnostics == (), _codes(run.diagnostics)
    assert _exit_status(run.diagnostics) == 0


def test_the_global_scope_reaches_the_planning_reference_checks(
    manuscript,
) -> None:
    """The mechanism, pairing, and cross-cut checks run at whole-book scope.

    A regression test with a history: `check_planning_references` was defined,
    exercised by its own tests, and called by nothing. The global gate passed a
    manuscript whose mechanism state was never validated. Injecting a mechanism
    fault and requiring the global run to notice is what keeps it wired in.
    """

    # The TimelineEntry records live in the Canon_Bible document, which is where
    # the fixture writes them; there is no separate timeline file to reach for.
    timeline = manuscript.manuscript_root / "planning" / "canon-bible.md"
    original = timeline.read_text(encoding="utf-8")
    try:
        broken = original.replace('"mode": "PAIR"', '"mode": "TRANSMIT"', 1)
        assert broken != original, "no PAIR entry to break"
        timeline.write_text(broken, encoding="utf-8")

        run = checker.run_scope(
            (), scope=checker.SCOPE_GLOBAL, manuscript_root=manuscript.manuscript_root
        )
        assert "TIMELINE_TECHNICAL_STATE_MALFORMED" in _codes(run.diagnostics), _codes(
            run.diagnostics
        )
    finally:
        timeline.write_text(original, encoding="utf-8")

    restored = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=manuscript.manuscript_root
    )
    assert restored.diagnostics == (), _codes(restored.diagnostics)


def test_an_unrunnable_scope_is_refused_rather_than_guessed() -> None:
    """`planning` is a diagnostic label, not a scope anything can be run at."""

    with pytest.raises(ValueError):
        checker.run_scope(
            (), scope=checker.SCOPE_PLANNING, manuscript_root=nf.Path(".")
        )


# ---------------------------------------------------------------------------
# Front matter: prose rights, source acknowledgment, no recording claims
# ---------------------------------------------------------------------------


def _front_matter_codes(tmp_path, text: str) -> List[str]:
    """Front_Matter diagnostics for a document written to a temporary path."""

    nf.write_text(tmp_path, "front-matter.md", text)
    return _codes(
        checker.check_front_matter(
            tmp_path / "front-matter.md", relative_path="front-matter.md"
        )
    )


def test_conforming_front_matter_is_accepted(tmp_path) -> None:
    """Author, prose copyright, and all five source songs."""

    assert _front_matter_codes(tmp_path, nf.CONFORMING_FRONT_MATTER) == []


@pytest.mark.parametrize(
    "removed", ("A novel by Fixture Author", "Novel prose copyright 2026 Fixture Author.")
)
def test_missing_prose_rights_fields_are_rejected(tmp_path, removed: str) -> None:
    """Requirement 9.11: the author and the prose copyright holder are both named."""

    text = nf.CONFORMING_FRONT_MATTER.replace(removed, "")
    codes = _front_matter_codes(tmp_path, text)
    assert "FRONT_MATTER_RIGHTS_FIELD_MISSING" in codes, (removed, codes)


def test_all_five_songs_are_acknowledged_or_none_are(tmp_path) -> None:
    """Requirement 9.12: a partial acknowledgment is the failure.

    Omitting the section entirely is the author's choice. Naming four of five
    reads as a decision about the fifth, which is why the incomplete list is what
    gets reported.
    """

    partial = nf.CONFORMING_FRONT_MATTER.replace(", and *Case Zero*", "")
    codes = _front_matter_codes(tmp_path, partial)
    assert "FRONT_MATTER_SOURCE_ACKNOWLEDGMENT_INCOMPLETE" in codes, codes


def test_acknowledging_one_time_pad_is_rejected(tmp_path) -> None:
    """The excluded draft is not a Canon_Source and is not acknowledged as one."""

    text = nf.CONFORMING_FRONT_MATTER.replace(
        ", and *Case Zero*", ", *Case Zero*, and *One-Time Pad*"
    )
    codes = _front_matter_codes(tmp_path, text)
    assert "FRONT_MATTER_EXCLUDED_SOURCE_ACKNOWLEDGED" in codes, codes


def test_recording_and_performance_ownership_language_is_rejected(
    tmp_path,
) -> None:
    """Requirement 9.11: prose rights are stated without claiming the recordings.

    The novel's rights and the songs' rights are different things held by
    different people. Front_Matter that blurs them is a rights problem, not a
    stylistic one, so it is objectively reportable.
    """

    text = nf.CONFORMING_FRONT_MATTER + (
        "\nAll sound recording rights in the source songs are owned by the author.\n"
    )
    codes = _front_matter_codes(tmp_path, text)
    assert "FRONT_MATTER_RECORDING_OWNERSHIP_CLAIM" in codes, codes


# ---------------------------------------------------------------------------
# Canon-source authority smoke flow
# ---------------------------------------------------------------------------


def _canon_smoke_records(**changes: Any) -> Dict[str, List[Dict[str, Any]]]:
    """A Canon_Bible slice: attributed lyric facts plus advisory metadata.

    Each keyword replaces one part of the slice, so a rejection case differs from
    the accepted one in exactly the way its name says.
    """

    lyric_facts = changes.get(
        "lyric_facts",
        [
            nf.canon_fact(
                canon_id="CF-SMOKE-{0:03d}".format(number),
                authority_basis="lyric",
                source_material_class="lyric",
                source_path=path,
                source_location="page one",
                first_person_testimony=True,
                truth_scope="attributed-testimony",
            )
            for number, path in enumerate(nf.CANON_SOURCE_PATHS, start=1)
        ],
    )
    advisory = changes.get(
        "advisory",
        [
            nf.canon_fact(
                canon_id="CF-SMOKE-NOTE",
                authority_basis="ratified-note",
                source_material_class="credits",
                source_path="songs/Case Zero.md",
                source_location="credits",
                truth_scope="ratified-proposition",
            )
        ],
    )
    return {"CanonFact": list(lyric_facts) + list(advisory)}


def _canon_smoke_codes(**changes: Any) -> List[str]:
    """Canon_Bible and inventory diagnostics for one smoke slice."""

    index = nf.record_index(supporting=False, **_canon_smoke_records(**changes))
    return _codes(
        checker.check_canon_facts(index) + checker.check_canon_source_inventory(index)
    )


def test_the_canon_source_authority_slice_is_accepted() -> None:
    """Five attributed lyric sources, plus ratified credits kept advisory."""

    assert _canon_smoke_codes() == []


def test_the_smoke_slice_rejects_an_added_one_time_pad() -> None:
    """Readmitting the excluded draft is caught in the assembled slice too."""

    extra = nf.canon_fact(
        canon_id="CF-SMOKE-PAD",
        authority_basis="lyric",
        source_material_class="lyric",
        source_path="songs/One-Time Pad.md",
        source_location="page one",
        first_person_testimony=True,
        truth_scope="attributed-testimony",
    )
    codes = _canon_smoke_codes(
        lyric_facts=_canon_smoke_records()["CanonFact"][:5] + [extra]
    )
    assert "CANON_SOURCE_EXCLUDED" in codes, codes


def test_the_smoke_slice_rejects_a_demoted_lyric() -> None:
    """A lyric source filed as advisory metadata is caught in the whole slice."""

    demoted = [dict(fact) for fact in _canon_smoke_records()["CanonFact"][:5]]
    demoted[0]["source_material_class"] = "production-note"
    codes = _canon_smoke_codes(lyric_facts=demoted)
    assert "CANON_SOURCE_MATERIAL_CLASS_MISMATCH" in codes, codes


def test_the_smoke_slice_rejects_promoted_production_metadata() -> None:
    """Credits cannot be relabelled into the top authority tier."""

    promoted = nf.canon_fact(
        canon_id="CF-SMOKE-NOTE",
        authority_basis="ratified-note",
        source_material_class="credits",
        source_path="songs/Case Zero.md",
        source_location="credits",
        truth_scope="authoritative-proposition",
    )
    codes = _canon_smoke_codes(advisory=[promoted])
    assert "CANON_RATIFIED_NOTE_TRUTH_SCOPE" in codes, codes


def test_the_smoke_slice_rejects_testimony_used_as_causal_proof() -> None:
    """A first-person account stays an account inside the assembled slice."""

    facts = [dict(fact) for fact in _canon_smoke_records()["CanonFact"][:5]]
    facts[0]["truth_scope"] = "authoritative-proposition"
    codes = _canon_smoke_codes(lyric_facts=facts)
    assert "CANON_TESTIMONY_TRUTH_SCOPE" in codes, codes


# ---------------------------------------------------------------------------
# Pairing mode and evidence smoke flow
# ---------------------------------------------------------------------------


def _mode_entry(
    timeline_id: str, state: Mapping[str, Any], *participants: str
) -> Dict[str, Any]:
    return nf.timeline_entry(
        timeline_id=timeline_id,
        chronology_kind="point",
        participants=list(participants) or ["CHAR-001"],
        state=state,
    )


def _mechanism_flow_codes(entries: Sequence[Mapping[str, Any]]) -> List[str]:
    """Every mechanism and reference diagnostic for a session flow."""

    index = nf.record_index(
        supporting=False,
        POVProfile=[
            nf.pov_profile(
                character_id="CHAR-001",
                pov_id="POV-MARA",
                voice_brief_id="VOICE-A",
                anchor=True,
            ),
            nf.pov_profile(
                character_id="CHAR-002",
                pov_id="POV-NIA",
                voice_brief_id="VOICE-B",
                anchor=False,
            ),
        ],
        VoiceBrief=[
            nf.voice_brief(pov_id="POV-MARA", voice_brief_id="VOICE-A"),
            nf.voice_brief(pov_id="POV-NIA", voice_brief_id="VOICE-B"),
        ],
        TimelineEntry=list(entries),
    )
    diagnostics: Tuple[Any, ...] = ()
    for record in index.of_type("TimelineEntry"):
        diagnostics = diagnostics + checker.check_technical_state(record, index)
    diagnostics = diagnostics + checker.check_pair_calibration_uniqueness(index)
    diagnostics = diagnostics + checker.check_character_references(index)
    return _codes(diagnostics)


def _session_flow(**pair_changes: Any) -> List[Dict[str, Any]]:
    """A three-mode flow: a reception, an intrusion, and a pairing session.

    The pairing session is the one that varies, because it carries the consent,
    calibration, and evidence obligations the rejection cases probe.
    """

    receive = _mode_entry(
        "TL-FLOW-RECEIVE",
        nf.technical_state(
            mode="RECEIVE",
            source_side_continuity="continuous",
            apparatus_mode="receive-only",
            transmit_stage_present=False,
            person_specific_address_state="locked",
        ),
    )
    intrude = _mode_entry(
        "TL-FLOW-INTRUDE",
        nf.technical_state(
            mode="INTRUDE",
            apparatus_mode="bench-transmit",
            transmit_stage_present=True,
            person_specific_address_state="identified",
        ),
    )
    pair_options: Dict[str, Any] = {
        "participants": ("CHAR-001", "CHAR-002"),
        "calibration_participants": ("CHAR-001", "CHAR-002"),
        "calibration_id": "CAL-FLOW-001",
    }
    pair_options.update(pair_changes.pop("pair_state", {}))
    evidence_options: Dict[str, Any] = pair_changes.pop("evidence", {})
    pair = _mode_entry(
        "TL-FLOW-PAIR",
        nf.technical_state(
            mode="PAIR",
            apparatus_mode="bench-transmit",
            transmit_stage_present=True,
            person_specific_address_state="locked",
            pair_state=nf.pair_state(**pair_options),
            pairing_evidence=nf.pairing_evidence(**evidence_options),
        ),
        *pair_options["participants"]
    )
    return [receive, intrude, pair]


def test_the_three_mode_session_flow_is_accepted() -> None:
    """A reception, an addressed intrusion, and a consented pairing coexist."""

    assert _mechanism_flow_codes(_session_flow()) == []


@pytest.mark.parametrize("send_state", ("paused", "revoked", "integrity-failed"))
def test_a_stopped_or_failed_session_is_declared_not_hidden(
    send_state: str,
) -> None:
    """Pause, revocation, and integrity failure are recordable session states.

    The flow stays valid because the state is *named*. What the design refuses is
    a session that carries on with the fault unrecorded, and naming it is how the
    records make that refusable.
    """

    codes = _mechanism_flow_codes(
        _session_flow(pair_state={"deliberate_send_state": send_state})
    )
    assert "PAIR_STATE_MALFORMED" not in codes, (send_state, codes)


def test_the_flow_records_only_transported_contributions() -> None:
    """A transcript is scoped to the session and exists only with mutual consent."""

    consented = _session_flow(
        evidence={
            "content_recording_enabled": True,
            "recording_consent_a": True,
            "recording_consent_b": True,
            "transcript": {
                "transcript_id": "TR-FLOW-001",
                "session_timeline_id": "TL-FLOW-PAIR",
                "content_scope": "Only contributions both participants transported.",
            },
        }
    )
    assert _mechanism_flow_codes(consented) == []

    one_sided = _session_flow(
        evidence={
            "content_recording_enabled": True,
            "recording_consent_a": True,
            "recording_consent_b": False,
        }
    )
    assert "PAIRING_EVIDENCE_INVARIANT" in _mechanism_flow_codes(one_sided)


def test_the_flow_rejects_semantic_metadata() -> None:
    """Transport metadata proves a session happened; it never says what passed."""

    codes = _mechanism_flow_codes(
        _session_flow(evidence={"overrides": {"metadata_semantically_opaque": False}})
    )
    assert "PAIRING_EVIDENCE_INVARIANT" in codes, codes


def test_the_flow_rejects_a_substituted_participant() -> None:
    """A stand-in has no place on the roster and so no place in the session."""

    codes = _mechanism_flow_codes(
        _session_flow(
            pair_state={
                "participants": ("CHAR-001", "RECON-001"),
                "calibration_participants": ("CHAR-001", "RECON-001"),
            }
        )
    )
    assert "CHARACTER_REFERENCE_DANGLING" in codes, codes


def test_the_flow_rejects_a_transferred_calibration() -> None:
    """The calibration belongs to its pair even inside a longer flow."""

    codes = _mechanism_flow_codes(
        _session_flow(pair_state={"calibration_transferable": True})
    )
    assert "PAIR_STATE_INVARIANT" in codes, codes


def test_the_flow_rejects_provenance_closure() -> None:
    """A cancellation that yields provenance would answer the open question.

    The flow's `CANCEL` beat is added here rather than in the base flow because a
    cancellation is a different kind of event from a session, and this is the one
    property it must not have.
    """

    cancel = _mode_entry(
        "TL-FLOW-CANCEL",
        nf.technical_state(
            mode="CANCEL",
            apparatus_mode="bidirectional-architecture",
            transmit_stage_present=True,
            person_specific_address_state="not-applicable",
            cancel_state=nf.cancel_state(
                overrides={"provenance_yield": "The field names its sender."}
            ),
        ),
    )
    codes = _mechanism_flow_codes(_session_flow() + [cancel])
    assert "CANCEL_STATE_INVARIANT" in codes, codes


# ---------------------------------------------------------------------------
# The approval process, end to end
# ---------------------------------------------------------------------------


def _baseline_codes(
    baseline: Mapping[str, Any], *gates: Mapping[str, Any]
) -> List[str]:
    """Baseline diagnostics with the gates it cites present in the index."""

    index = nf.record_index(
        supporting=False, Baseline=[baseline], GateResult=list(gates)
    )
    _state, diagnostics = checker.check_baseline(index)
    return _codes(diagnostics)


def _gate(gate_result_id: str, gate_type: str, **options: Any) -> Dict[str, Any]:
    values: Dict[str, Any] = {
        "gate_result_id": gate_result_id,
        "gate_type": gate_type,
        "result": "pass",
        "checker_exit_status": 0,
    }
    values.update(options)
    return nf.gate_result(**values)


def test_a_provisional_baseline_needs_no_approval_evidence() -> None:
    """Planning is allowed to be in progress; that is what provisional means."""

    assert _baseline_codes(nf.baseline(state="provisional")) == []


def test_an_approved_baseline_without_evidence_is_rejected() -> None:
    """Approval is a claim about evidence, so the evidence has to be there.

    All four obligations are asserted together because the failure mode worth
    guarding is a baseline approved with *none* of them, and naming each one shows
    which are independent.
    """

    codes = _baseline_codes(nf.baseline(state="approved"))
    for expected in (
        "BASELINE_AUTHOR_APPROVAL_MISSING",
        "BASELINE_FINAL_TARGETS_MISSING",
        "BASELINE_GATE_EVIDENCE_MISSING",
        "BASELINE_REVISION_PASS_MISSING",
    ):
        assert expected in codes, (expected, codes)


def test_the_process_flow_from_planning_to_reapproval() -> None:
    """Planning, calibration, full-suite evidence, one revision pass, approval.

    This walks the whole sequence in order and asserts what each step requires.
    The revision and reapproval at the end matter because approval is not
    terminal: a superseded baseline gives way to a new approved one, and the new
    one carries its own evidence rather than inheriting the old one's.
    """

    minimal = _gate(
        "GATE-CALIBRATION-001",
        "calibration-objective",
        chapter_numbers=CALIBRATION_CHAPTERS,
    )
    full_suite = _gate("GATE-BASELINE-001", "baseline-objective")

    # 1. Planning in progress: no evidence owed yet.
    provisional = nf.baseline(baseline_id="BASELINE-001", state="provisional")
    assert _baseline_codes(provisional, minimal, full_suite) == []

    # 2. Exploratory calibration run, and its gate cited.
    calibrated = nf.baseline(
        baseline_id="BASELINE-001",
        state="provisional",
        calibration_chapters=CALIBRATION_CHAPTERS,
        minimal_checker_gate_result_id=minimal["gate_result_id"],
    )
    assert _baseline_codes(calibrated, minimal, full_suite) == []

    # 3. Full objective suite, one Baseline_Revision_Pass, author approval.
    approved = nf.baseline(
        baseline_id="BASELINE-001",
        state="approved",
        calibration_chapters=CALIBRATION_CHAPTERS,
        minimal_checker_gate_result_id=minimal["gate_result_id"],
        full_suite_gate_result_id=full_suite["gate_result_id"],
        baseline_revision_pass=nf.baseline_revision_pass(),
        author_approval=nf.author_approval(),
        final_targets={
            "chapter_count": 128,
            "minimum_words": 130000,
            "maximum_words": 150000,
        },
    )
    assert _baseline_codes(approved, minimal, full_suite) == []

    # 4. Revision supersedes it, and the replacement carries its own evidence.
    superseded = dict(approved, state="superseded")
    reapproval_gate = _gate("GATE-BASELINE-002", "baseline-objective")
    reapproved = nf.baseline(
        baseline_id="BASELINE-002",
        state="approved",
        calibration_chapters=CALIBRATION_CHAPTERS,
        minimal_checker_gate_result_id=minimal["gate_result_id"],
        full_suite_gate_result_id=reapproval_gate["gate_result_id"],
        baseline_revision_pass=nf.baseline_revision_pass(),
        author_approval=nf.author_approval(),
        final_targets={
            "chapter_count": 128,
            "minimum_words": 130000,
            "maximum_words": 150000,
        },
    )
    index = nf.record_index(
        supporting=False,
        Baseline=[superseded, reapproved],
        GateResult=[minimal, full_suite, reapproval_gate],
    )
    _state, diagnostics = checker.check_baseline(index)
    assert diagnostics == (), _codes(diagnostics)


def test_an_approved_baseline_cannot_cite_a_gate_that_does_not_exist() -> None:
    """Evidence is a reference, and a reference that resolves to nothing is not evidence."""

    approved = nf.baseline(
        baseline_id="BASELINE-003",
        state="approved",
        calibration_chapters=CALIBRATION_CHAPTERS,
        minimal_checker_gate_result_id="GATE-DOES-NOT-EXIST",
        full_suite_gate_result_id="GATE-ALSO-MISSING",
        baseline_revision_pass=nf.baseline_revision_pass(),
        author_approval=nf.author_approval(),
        final_targets={
            "chapter_count": 128,
            "minimum_words": 130000,
            "maximum_words": 150000,
        },
    )
    codes = _baseline_codes(approved)
    assert "BASELINE_GATE_REFERENCE_DANGLING" in codes, codes


def test_final_targets_outside_the_provisional_range_need_a_rationale() -> None:
    """A target range may move, but not silently.

    The provisional range is a plan, not a law. Changing it is allowed and
    recording why is required, which keeps the change reviewable instead of
    invisible.
    """

    options: Dict[str, Any] = {
        "baseline_id": "BASELINE-004",
        "state": "approved",
        "calibration_chapters": CALIBRATION_CHAPTERS,
        "minimal_checker_gate_result_id": "GATE-CALIBRATION-001",
        "full_suite_gate_result_id": "GATE-BASELINE-001",
        "baseline_revision_pass": nf.baseline_revision_pass(),
        "author_approval": nf.author_approval(),
        "final_targets": {
            "chapter_count": 128,
            "minimum_words": 90000,
            "maximum_words": 110000,
        },
    }
    gates = (
        _gate("GATE-CALIBRATION-001", "calibration-objective"),
        _gate("GATE-BASELINE-001", "baseline-objective"),
    )
    codes = _baseline_codes(nf.baseline(**options), *gates)
    assert "BASELINE_OUT_OF_RANGE_RATIONALE_MISSING" in codes, codes

    with_rationale = dict(options)
    with_rationale["out_of_range_rationale"] = (
        "The author shortened the Mindwars movement after calibration."
    )
    assert _baseline_codes(nf.baseline(**with_rationale), *gates) == []
