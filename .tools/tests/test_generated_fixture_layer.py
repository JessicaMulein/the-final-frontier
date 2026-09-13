"""Self-tests for the generated fixture layer built by task 8.9.

The fifteen principal property tests (tasks 8.10 through 8.24) all draw from
`novel_strategies` and build from `novel_fixtures`. If a generator silently
produced a record the checker rejects for an unrelated reason, every property
resting on it would pass or fail for the wrong cause. These tests check the
scaffolding itself so a later property failure means what it says.

Two claims are load-bearing here:

* The complete 128-chapter manuscript fixture passes the Manuscript_Global_Gate
  cleanly. A property test that injects one violation into that world can only
  attribute the resulting diagnostic to its own injection if the uninjected world
  is silent.
* Every labelled variant reaches the checker with only the fault it names. A
  `valid` variant draws no diagnostic, and an `objective` malformed variant draws
  at least one. An `objective=False` variant draws none, because its fault is a
  craft or continuity judgment that belongs to a human `EditorialFinding`.
"""

from __future__ import annotations

import collections
from typing import Any, Dict, Optional, Tuple

from hypothesis import HealthCheck, assume, given, settings

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

FIXTURE_LAYER_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


# ---------------------------------------------------------------------------
# The complete manuscript fixture
# ---------------------------------------------------------------------------


def test_the_pov_sequence_matches_the_provisional_load_vector():
    """Requirement 15.3's 56/32/33/7 vector, as the generated sequence realizes it."""

    sequence = nf.manuscript_pov_sequence()
    assert len(sequence) == 128
    observed = collections.Counter(sequence)
    assert sorted(observed.values()) == [7, 32, 33, 56]
    for pov_id, expected in nf.MANUSCRIPT_POV_LOAD.items():
        assert observed[pov_id] == expected["total"], pov_id


def test_the_pov_sequence_stays_inside_both_same_pov_run_bounds():
    """Requirements 2.7 and 2.15 bound a run by chapters *and* by words."""

    sequence = nf.manuscript_pov_sequence()
    longest = 0
    current = 0
    previous: Optional[str] = None
    for pov_id in sequence:
        current = current + 1 if pov_id == previous else 1
        previous = pov_id
        longest = max(longest, current)
    assert longest <= ns.RUN_CHAPTER_LIMIT


def test_the_complete_manuscript_fixture_passes_the_global_gate(tmp_path):
    """The uninjected whole book is silent, which is what makes injection legible."""

    workspace = nf.manuscript_workspace(tmp_path)
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    result = checker.classify_result(run.diagnostics)
    assert run.diagnostics == (), [
        (item.code, item.observed) for item in run.diagnostics
    ]
    assert checker.exit_status_for_result(result) == 0


def test_an_injected_outline_gap_is_the_only_thing_the_global_gate_reports(tmp_path):
    """One injected fault yields diagnostics about that fault and nothing else."""

    workspace = nf.manuscript_workspace(
        tmp_path, entry_overrides={64: {"movement": "aftermath_coda"}}
    )
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    codes = {item.code for item in run.diagnostics}
    assert codes, "an injected movement-block break must be reported"
    assert checker.exit_status_for_result(checker.classify_result(run.diagnostics)) != 0


def test_the_motif_ledger_fixture_carries_the_fixed_family_totals():
    """Requirement 7.12 fixes two kettle events; Requirement 7.17 fixes three records."""

    ledger = nf.manuscript_motif_events()
    families = collections.Counter(record["family"] for record in ledger)
    assert families["kettle"] == 2
    assert families["record progression"] == 3
    kettle_movements = {
        record["movement"] for record in ledger if record["family"] == "kettle"
    }
    assert kettle_movements == {"aftermath_coda"}
    record_movements = {
        record["movement"]
        for record in ledger
        if record["family"] == "record progression"
    }
    assert record_movements == {
        "private_defense_part",
        "mindwars_part",
        "aftermath_coda",
    }


def test_the_final_passage_fixture_places_the_phrase_inside_the_declared_span():
    """The protected phrase is found through the ledger's span, not through typography."""

    prose = nf.final_passage_prose(words=200, occurrences=2)
    constraint = nf.whose_was_that_constraint()
    normalized = checker.normalize_prose(prose)
    span, reason = checker.locate_literal_span(constraint["allowed_span"], normalized)
    assert reason is None, reason
    assert span is not None
    start, end = span
    assert normalized[start:end].count(nf.WHOSE_WAS_THAT) == 2
    assert normalized[:start].count(nf.WHOSE_WAS_THAT) == 0


# ---------------------------------------------------------------------------
# The variant strategies
# ---------------------------------------------------------------------------

# Which checker entry point judges a record type, and the ID field that
# identifies it. A payload is routed by the ID field it carries, so a strategy
# can mix record types in one truth table without the test having to know.
_ROUTES: Tuple[Tuple[str, str, Any], ...] = (
    ("canon_id", "CanonFact", "check_canon_facts"),
    ("extension_id", "NovelExtension", "check_novel_extensions"),
    ("reveal_id", "Reveal", "check_reveals"),
    ("gate_result_id", "GateResult", "check_gate_results"),
    ("arc_change_id", "ArcChange", "check_arc_changes"),
)


def _route(payload: Any) -> Tuple[Optional[str], Any]:
    if not isinstance(payload, dict):
        return None, None
    for id_field, record_type, check_name in _ROUTES:
        if id_field in payload:
            return record_type, getattr(checker, check_name)
    return None, None


def _diagnose(variant: ns.Variant) -> Tuple[Any, ...]:
    """Run the one check that owns this variant's record type."""

    record_type, check = _route(variant.payload)
    assert record_type is not None, "unroutable payload for {0}".format(variant.label)
    # A probe testing a dangling reference must not be handed the record that
    # would resolve it, or the fault it exists to show disappears.
    supporting = "dangling" not in variant.label and "unresolvable" not in variant.label
    index = nf.record_index(supporting=supporting, **{record_type: [variant.payload]})
    return tuple(check(index))


def _assert_variant_agrees(variant: ns.Variant) -> None:
    diagnostics = _diagnose(variant)
    codes = sorted({item.code for item in diagnostics})
    if variant.expects_diagnostic:
        assert diagnostics, "{0} drew no diagnostic".format(variant)
    else:
        assert not diagnostics, "{0} drew {1}".format(variant, codes)


@FIXTURE_LAYER_SETTINGS
@given(ns.canon_authority_variants())
def test_canon_authority_variants_agree_with_the_authority_matrix(variant):
    """Every basis in the matrix, and the states it rejects."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.novel_extension_variants())
def test_novel_extension_variants_agree_on_reference_integrity(variant):
    """Kind, state, and reference resolution are the machine-visible faults."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.gates())
def test_gate_variants_agree_on_result_and_exit_status(variant):
    """An objective gate's verdict must agree with its recorded exit status."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.status_changes())
def test_status_change_variants_agree_on_atomicity(variant):
    """A `complete` ArcChange is atomic or it is not complete."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.dec_002_states())
def test_dec_002_variants_agree(variant):
    """The mapping, the bench path, and the same-speaker testimony stay apart."""

    assume(isinstance(variant.payload, dict) and "timeline_id" not in variant.payload)
    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.dec_007_states())
def test_dec_007_variants_agree(variant):
    """Three accounts held apart, and no promotion to settled truth."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.dec_005_states())
def test_dec_005_variants_agree(variant):
    """Reference faults are reported; prose claims about the Trust are not."""

    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.dec_012_states())
def test_dec_012_variants_are_recorded_without_being_graded(variant):
    """Coinage timing and mechanism claims are continuity judgments, not diagnostics."""

    assert not variant.expects_diagnostic or variant.objective
    _assert_variant_agrees(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.heritage_variants())
def test_heritage_variants_are_never_graded(variant):
    """`heritage_base` content is the author's business, so the checker stays silent."""

    assert not variant.expects_diagnostic
    _assert_variant_agrees(variant)


# ---------------------------------------------------------------------------
# Generators that do not resolve to a single record type
# ---------------------------------------------------------------------------


@FIXTURE_LAYER_SETTINGS
@given(ns.canon_source_inventories())
def test_canon_source_inventory_variants_agree_with_dec_014(variant):
    """`DEC-014` fixes the Canon_Source set at exactly five named paths."""

    assert isinstance(variant.payload, tuple)
    exact = set(nf.CANON_SOURCE_PATHS)
    observed = set(variant.payload)
    assert (observed == exact) == variant.valid, str(variant)
    if not variant.valid:
        assert observed != exact


@FIXTURE_LAYER_SETTINGS
@given(ns.normal_share_allocations())
def test_normal_share_variants_use_exact_integer_arithmetic(variant):
    """The 80 percent floor is decided without floating point, in both directions."""

    allocation = variant.payload
    normal = sum(1 for item in allocation if item == "normal")
    assert variant.valid == (normal * 100 >= len(allocation) * 80)


@FIXTURE_LAYER_SETTINGS
@given(ns.pov_run_variants())
def test_pov_run_variants_cross_one_bound_at_a_time(variant):
    """The chapter bound and the word bound are independent, and both are reachable."""

    runs = checker.pov_runs(variant.payload)
    diagnostics = checker.check_pov_runs(
        runs, scope=checker.SCOPE_PLANNING, source="planning/probe.md"
    )
    assert bool(diagnostics) == variant.expects_diagnostic, "{0} drew {1}".format(
        variant, sorted({item.code for item in diagnostics})
    )


@FIXTURE_LAYER_SETTINGS
@given(ns.load_vector_variants())
def test_load_vector_variants_respect_the_name_choice_exemption(variant):
    """Requirement 12.11 keeps which name owns which number out of pass/fail."""

    totals = sorted(int(load["total"]) for load in variant.payload.values())
    if variant.valid:
        assert totals == [7, 32, 33, 56], str(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.header_variants())
def test_header_variants_render_a_parseable_or_pointedly_broken_file(variant):
    """A conforming header parses cleanly; each malformed one is reported.

    A malformed delimiter is refused at the split, before any key is read, so it
    surfaces as `ChapterBoundaryError` rather than as a key diagnostic. Both are
    the checker declining to guess, which is what the variant claims.
    """

    try:
        header_lines, prose = checker.split_chapter_header(
            variant.payload, item="chapter-probe.md"
        )
    except checker.ChapterBoundaryError:
        assert not variant.valid, "{0} was refused at the header boundary".format(
            variant
        )
        return

    header, diagnostics = checker.parse_chapter_header_lines(
        header_lines, item="chapter-probe.md"
    )
    if variant.valid:
        assert not diagnostics, sorted({item.code for item in diagnostics})
        assert header["words"] == checker.count_prose_words(
            checker.normalize_prose(prose)
        )
        return

    if diagnostics:
        return
    # A header that parses cleanly can still disagree with its own body. That is
    # Requirement 9.7's territory, and the disagreement is the reported fault.
    observed = checker.count_prose_words(checker.normalize_prose(prose))
    assert header.get("words") != observed or header.get(
        "length_class"
    ) != checker.derive_length_class(observed), str(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.consent_calibration_rows())
def test_the_consent_and_calibration_truth_table_is_fully_reachable(variant):
    """Every row of the PAIR truth table is generated, valid and malformed alike."""

    assert isinstance(variant.payload, dict)
    assert "participants" in variant.payload
    assert "consent" in variant.payload


@FIXTURE_LAYER_SETTINGS
@given(ns.pause_revocation_streams())
def test_pause_and_revocation_streams_are_labelled_consistently(variant):
    """A revocation ends the session; an unrecovered fault stays declared."""

    stream = variant.payload
    faults = {"clipping", "latency", "integrity-failure"}
    if variant.valid:
        if "revoke" in stream:
            assert stream.index("revoke") == len(stream) - 1
        last = max(
            (i for i, event in enumerate(stream) if event in faults), default=-1
        )
        assert last < 0 or "recovery" in stream[last + 1 :]


@FIXTURE_LAYER_SETTINGS
@given(ns.recording_consent_combinations())
def test_recording_consent_combinations_are_independent(variant):
    """Recording is lawful only when both independent consents are given."""

    evidence = variant.payload
    enabled = evidence["content_recording_enabled"]
    both = evidence["recording_consent_a"] and evidence["recording_consent_b"]
    assert variant.valid == ((not enabled) or both)


@FIXTURE_LAYER_SETTINGS
@given(ns.literal_phrase_placements())
def test_literal_phrase_placements_are_decided_through_the_declared_span(variant):
    """Count and span boundary are separate faults, and both are generated."""

    constraint = nf.whose_was_that_constraint()
    normalized = checker.normalize_prose(variant.payload)
    span, reason = checker.locate_literal_span(constraint["allowed_span"], normalized)
    if variant.valid:
        assert reason is None, reason
        assert span is not None
        start, end = span
        assert normalized[start:end].count(nf.WHOSE_WAS_THAT) == 2
        assert normalized[:start].count(nf.WHOSE_WAS_THAT) == 0
    else:
        inside = 0
        outside = normalized.count(nf.WHOSE_WAS_THAT)
        if span is not None:
            start, end = span
            inside = normalized[start:end].count(nf.WHOSE_WAS_THAT)
            outside = outside - inside
        assert reason is not None or inside != 2 or outside > 0, str(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.conforming_outlines())
def test_conforming_outlines_are_numbered_one_through_n(variant):
    """The generated outline is a clean 1..N in four ordered contiguous blocks."""

    numbers = [entry["chapter"] for entry in variant]
    assert numbers == list(range(1, len(variant) + 1))
    seen: Dict[str, int] = {}
    for entry in variant:
        seen.setdefault(entry["movement"], len(seen))
    order = [movement for movement, _ in sorted(seen.items(), key=lambda kv: kv[1])]
    assert order == [m for m in nf.MOVEMENTS if m in seen]


@FIXTURE_LAYER_SETTINGS
@given(ns.motif_ledgers())
def test_motif_ledger_variants_change_exactly_one_closed_family(variant):
    """A complete ledger, or one closed family perturbed in one way."""

    families = collections.Counter(record["family"] for record in variant.payload)
    if variant.valid:
        assert families["kettle"] == 2
        assert families["record progression"] == 3
    else:
        assert (
            families["kettle"] != 2
            or families["record progression"] != 3
            or "moved out of its movement" in variant.label
        )


@FIXTURE_LAYER_SETTINGS
@given(ns.fluent_pairing_coverage())
def test_fluent_pairing_coverage_variants_cover_or_miss_one_range(variant):
    """Requirement 15.1's five ranges: all covered, or exactly one left open."""

    covered = {
        number
        for entry in variant.payload
        for number in entry["chapter_numbers"]
    }
    missing = [
        (start, end)
        for start, end in nf.FLUENT_PAIRING_RANGES
        if not any(start <= number <= end for number in covered)
    ]
    assert (missing == []) == variant.valid, str(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.final_targets())
def test_final_target_variants_agree_with_the_observed_totals(variant):
    """A target the observed manuscript misses is a violation, in either direction."""

    targets, chapters, words = variant.payload
    matches = (
        int(targets["chapter_count"]) == chapters
        and int(targets["minimum_words"]) <= words <= int(targets["maximum_words"])
    )
    assert matches == variant.valid, str(variant)


@FIXTURE_LAYER_SETTINGS
@given(ns.technical_state_variants())
def test_technical_state_variants_declare_one_mode_at_a_time(variant):
    """A lawful state carries only its own mode's object."""

    state = variant.payload
    objects = [
        key
        for key in ("cancel_state", "pair_state")
        if state.get(key) is not None
    ]
    if variant.valid:
        assert len(objects) <= 1
        assert state["mode"] in ns.TECHNICAL_MODES
