"""Focused decision-record and Canon_Authority tests for task 8.25.

Validates: Requirements 6.2-6.19, 7.1-7.18, 12.1-12.15, 14.1-14.4, and
14.10-14.14.

These tests cover the decision records the design fixes by name -- `DEC-002`,
`DEC-005`, `DEC-007`, `DEC-012`, `DEC-014` -- together with the Canon_Authority
matrix that decides which source may establish a binding fact.

What is being proved
--------------------
Two different things, and the distinction is the point of the file.

The first is that the checker rejects records whose *structure* misstates
authority: a lyric fact stripped of its speaker, a first-person account
relabelled as omniscient proof, a ratified note claiming the top authority tier,
a Canon_Source inventory that is not exactly the five `DEC-014` paths.

The second is that the checker stays *silent* on claims no program can settle. A
name's wording and capitalization, whether a described geography contradicts
itself, whether an inquiry reads as genuinely adjudicating -- these are prose
judgments belonging to a human `EditorialFinding`. A test that demanded a
diagnostic for them would be asking the checker to grade craft, which is the one
thing it must never do. Those cases are asserted to draw nothing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pytest

import novel_fixtures as nf

checker = nf.load_checker()

CASE_ZERO = "songs/Case Zero.md"
ONE_TIME_PAD = "songs/One-Time Pad.md"
TESTIMONY_SCOPE = "attributed-testimony"
AUTHORITATIVE_SCOPE = "authoritative-proposition"
RATIFIED_SCOPE = "ratified-proposition"


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def _canon_codes(*facts: Mapping[str, Any]) -> Tuple[str, ...]:
    """Canon_Bible diagnostics for a set of CanonFacts, deduplicated."""

    index = nf.record_index(supporting=False, CanonFact=list(facts))
    return tuple(sorted({item.code for item in checker.check_canon_facts(index)}))


def _inventory_codes(*paths: str) -> Tuple[str, ...]:
    """Canon_Source inventory diagnostics for a declared set of source paths."""

    facts = [
        nf.canon_fact(
            canon_id="CF-INV-{0:03d}".format(number),
            authority_basis="lyric",
            source_material_class="lyric",
            source_path=path,
            source_location="page one",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
        for number, path in enumerate(paths, start=1)
    ]
    index = nf.record_index(supporting=False, CanonFact=facts)
    return tuple(
        sorted({item.code for item in checker.check_canon_source_inventory(index)})
    )


def _extension_codes(*extensions: Mapping[str, Any]) -> Tuple[str, ...]:
    """Novel_Extension diagnostics, with supporting records present to resolve."""

    index = nf.record_index(NovelExtension=list(extensions))
    return tuple(sorted({item.code for item in checker.check_novel_extensions(index)}))


def _reveal_codes(*reveals: Mapping[str, Any]) -> Tuple[str, ...]:
    """Reveal diagnostics for a set of Reveal records."""

    index = nf.record_index(supporting=False, Reveal=list(reveals))
    return tuple(sorted({item.code for item in checker.check_reveals(index)}))


def _timeline_codes(*entries: Mapping[str, Any]) -> Tuple[str, ...]:
    """Mechanism-state diagnostics for a set of TimelineEntries.

    Supporting records are off: mechanism state resolves nothing outside its own
    entry, and the default supporting set carries a TimelineEntry of its own,
    which would add a foreign entry's verdict to every probe here.
    """

    index = nf.record_index(supporting=False, TimelineEntry=list(entries))
    diagnostics: Tuple[Any, ...] = ()
    for record in index.of_type("TimelineEntry"):
        diagnostics = diagnostics + checker.check_technical_state(record, index)
    return tuple(sorted({item.code for item in diagnostics}))


def _lyric_fact(**options: Any) -> Dict[str, Any]:
    """A binding *Case Zero* lyric fact recorded as attributed testimony."""

    values: Dict[str, Any] = {
        "canon_id": "CF-CASE-ZERO-001",
        "authority_basis": "lyric",
        "source_material_class": "lyric",
        "source_path": CASE_ZERO,
        "source_location": "page nine",
        "first_person_testimony": True,
        "truth_scope": TESTIMONY_SCOPE,
    }
    values.update(options)
    return nf.canon_fact(**values)


# ---------------------------------------------------------------------------
# DEC-014: the five Canon_Sources and the authority they carry
# ---------------------------------------------------------------------------


def test_the_five_canon_sources_are_accepted_exactly() -> None:
    """`DEC-014` fixes the Canon_Source set at five files, no more and no fewer."""

    assert _inventory_codes(*nf.CANON_SOURCE_PATHS) == ()


def test_citing_only_some_of_the_five_is_accepted() -> None:
    """Citing four songs is an early Canon_Bible, not a violation.

    The inventory check reports which sources are *cited* and never demands all
    five, because a Canon_Bible built from three songs is a normal intermediate
    state. Requiring five here would make honest partial work fail. The rule that
    *Case Zero* is acknowledged belongs to the Front_Matter, where a partial list
    genuinely is the failure.
    """

    remaining = [path for path in nf.CANON_SOURCE_PATHS if path != CASE_ZERO]
    assert len(remaining) == 4, remaining
    assert _inventory_codes(*remaining) == ()


def test_adding_one_time_pad_is_rejected() -> None:
    """The *One-Time Pad* draft sits outside canon and cannot be readmitted."""

    assert ONE_TIME_PAD not in nf.CANON_SOURCE_PATHS
    assert _inventory_codes(*(tuple(nf.CANON_SOURCE_PATHS) + (ONE_TIME_PAD,))) != ()


def test_a_lyric_fact_from_the_excluded_song_is_rejected() -> None:
    """*One-Time Pad* gets its own code, because it is excluded rather than unknown.

    The distinction matters when reading a report: an unknown path is probably a
    typo, while a citation of the excluded draft is an attempt to reopen a
    decision.
    """

    codes = _canon_codes(_lyric_fact(source_path=ONE_TIME_PAD))
    assert "CANON_SOURCE_EXCLUDED" in codes, codes


def test_a_lyric_fact_from_an_unlisted_song_is_rejected() -> None:
    """Canon_Lyric authority comes only from the five listed paths."""

    codes = _canon_codes(_lyric_fact(source_path="songs/Not A Canon Source.md"))
    assert "CANON_SOURCE_PATH_UNKNOWN" in codes, codes


def test_attributed_same_speaker_lyric_testimony_is_accepted() -> None:
    """A lyric fact keeping speaker, attribution, and limitation is binding as testimony."""

    assert _canon_codes(_lyric_fact()) == ()


@pytest.mark.parametrize(
    "field", ("speaker", "attribution", "epistemic_limitation")
)
def test_testimony_stripped_of_its_metadata_is_rejected(field: str) -> None:
    """Requirement 6.17: first-person testimony keeps its attribution metadata.

    Each field is blanked separately, because losing any one of the three is
    enough to turn an attributed account into a free-floating assertion.
    """

    codes = _canon_codes(_lyric_fact(overrides={field: ""}))
    assert "CANON_TESTIMONY_ATTRIBUTION_MISSING" in codes, (field, codes)


def test_testimony_used_as_omniscient_causal_proof_is_rejected() -> None:
    """A first-person account binds what the speaker reports, not what caused it."""

    codes = _canon_codes(_lyric_fact(truth_scope=AUTHORITATIVE_SCOPE))
    assert "CANON_TESTIMONY_TRUTH_SCOPE" in codes, codes


def test_a_truth_scope_outside_the_three_is_rejected() -> None:
    """There is no `omniscient` truth scope for the checker to grant."""

    codes = _canon_codes(_lyric_fact(truth_scope="omniscient"))
    assert "CANON_TRUTH_SCOPE_UNKNOWN" in codes, codes


def test_a_demoted_case_zero_lyric_is_rejected() -> None:
    """Lyric authority cannot be filed under an advisory material class.

    Recording binding lyric as a production note would let the same text be
    treated as non-story metadata whenever that reading is convenient.
    """

    codes = _canon_codes(_lyric_fact(source_material_class="production-note"))
    assert "CANON_SOURCE_MATERIAL_CLASS_MISMATCH" in codes, codes


@pytest.mark.parametrize(
    "material_class",
    (
        "production-note",
        "style-prompt",
        "exclude-prompt",
        "generation-workflow",
        "credits",
        "rights-metadata",
    ),
)
def test_unratified_advisory_metadata_cannot_bind(material_class: str) -> None:
    """Requirement 6.17: advisory metadata cannot be promoted into continuity.

    Every advisory class is exercised, because the prohibition is on the tier and
    not on any one document: credits and a style prompt are equally unable to
    establish a fact on their own.
    """

    codes = _canon_codes(
        nf.canon_fact(
            canon_id="CF-ADVISORY-001",
            authority_basis="lyric",
            source_material_class=material_class,
            source_path=CASE_ZERO,
            source_location="credits",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
    )
    assert "CANON_ADVISORY_MATERIAL_BINDING" in codes, (material_class, codes)


def test_a_ratified_note_names_its_adopter() -> None:
    """Requirement 6.17: a ratified note identifies the decision that ratified it."""

    ratified = nf.canon_fact(
        canon_id="CF-NOTE-001",
        authority_basis="ratified-note",
        source_material_class="credits",
        source_path=CASE_ZERO,
        source_location="credits",
        truth_scope=RATIFIED_SCOPE,
    )
    assert _canon_codes(ratified) == ()

    orphaned = dict(ratified)
    orphaned["adopted_by"] = None
    codes = _canon_codes(orphaned)
    assert "CANON_ADOPTION_MALFORMED" in codes, codes


def test_a_ratified_note_cannot_claim_the_top_authority_tier() -> None:
    """A note's authority is borrowed from its adopter, so it is not authoritative.

    Without this the advisory prohibition has a way around it: ratify a rights
    footer, then relabel it `authoritative-proposition` and it outranks the
    Novel_Extensions it was never allowed to defeat.
    """

    codes = _canon_codes(
        nf.canon_fact(
            canon_id="CF-NOTE-002",
            authority_basis="ratified-note",
            source_material_class="rights-metadata",
            source_path=CASE_ZERO,
            source_location="rights footer",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
    )
    assert "CANON_RATIFIED_NOTE_TRUTH_SCOPE" in codes, codes


def test_an_author_decision_does_not_carry_an_adoption() -> None:
    """Adoption is what a note needs; a decision is already its own authority."""

    codes = _canon_codes(
        nf.canon_fact(
            canon_id="CF-DECISION-001",
            truth_scope=AUTHORITATIVE_SCOPE,
            adopted_by={
                "authority_type": "author-decision",
                "authority_id": "DEC-014",
                "source_path": "planning/decisions.md",
                "source_location": "DEC-014",
            },
        )
    )
    assert "CANON_ADOPTION_UNEXPECTED" in codes, codes


@pytest.mark.parametrize(
    "basis,material_class,source_path,source_location",
    (
        ("author-decision", "author-decision", "planning/decisions.md", "DEC-014"),
        ("requirement", "requirement", "requirements.md", "Requirement 6.17"),
    ),
)
def test_self_authorizing_bases_are_accepted(
    basis: str, material_class: str, source_path: str, source_location: str
) -> None:
    """Author decisions and approved requirements need no external ratification."""

    assert (
        _canon_codes(
            nf.canon_fact(
                canon_id="CF-SELF-001",
                authority_basis=basis,
                source_material_class=material_class,
                source_path=source_path,
                source_location=source_location,
                truth_scope=AUTHORITATIVE_SCOPE,
            )
        )
        == ()
    )


def test_an_authority_basis_and_material_class_must_agree() -> None:
    """A decision filed as lyric misstates where its authority comes from."""

    codes = _canon_codes(
        nf.canon_fact(
            canon_id="CF-MISMATCH-001",
            authority_basis="author-decision",
            source_material_class="lyric",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
    )
    assert "CANON_SOURCE_MATERIAL_CLASS_MISMATCH" in codes, codes


# ---------------------------------------------------------------------------
# DEC-002: the receive-only December, and the later bench path
# ---------------------------------------------------------------------------


def _december_interval(**state_options: Any) -> Dict[str, Any]:
    """The December interval: reception only, with no transmit stage."""

    values: Dict[str, Any] = {
        "mode": "RECEIVE",
        "source_side_continuity": "continuous",
        "apparatus_mode": "receive-only",
        "transmit_stage_present": False,
        "person_specific_address_state": "locked",
    }
    values.update(state_options)
    return nf.timeline_entry(
        timeline_id="TL-DEC-002-DECEMBER",
        chronology_kind="interval",
        state=nf.technical_state(**values),
    )


def test_the_december_apparatus_is_accepted_as_receive_only() -> None:
    """`DEC-002`: December is an explicitly receive-only interval."""

    assert _timeline_codes(_december_interval()) == ()


def test_a_december_transmit_stage_is_rejected() -> None:
    """A receive-only interval cannot also carry a transmit stage.

    This is the specific confusion `DEC-002` exists to prevent: reading the
    December material as evidence that transmission had already happened.
    """

    assert _timeline_codes(_december_interval(transmit_stage_present=True)) != ()


def test_the_later_bench_path_is_a_distinct_pair_handshake() -> None:
    """The bench transmit path is its own event, over the same locked address."""

    bench = nf.timeline_entry(
        timeline_id="TL-DEC-002-BENCH",
        chronology_kind="point",
        state=nf.technical_state(
            mode="PAIR",
            apparatus_mode="bench-transmit",
            transmit_stage_present=True,
            person_specific_address_state="locked",
            pair_state=nf.pair_state(),
            pairing_evidence=nf.pairing_evidence(),
        ),
    )
    assert _timeline_codes(bench) == ()
    # Both may be held at once: they are separate entries, not one contradiction.
    assert _timeline_codes(_december_interval(), bench) == ()


def test_page_nine_cannot_prove_december_transmission() -> None:
    """A lyric page is testimony about December, never omniscient proof of it.

    The mechanism claim would have to come from a decision or a requirement. The
    checker enforces that by refusing the promotion, not by reading the page.
    """

    codes = _canon_codes(
        _lyric_fact(
            canon_id="CF-PAGE-NINE-001",
            source_location="page nine",
            statement="December carried a transmission.",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
    )
    assert "CANON_TESTIMONY_TRUTH_SCOPE" in codes, codes


def test_collapsing_the_mechanism_into_lyric_authority_is_rejected() -> None:
    """The mechanism is fixed by decisions; lyric cannot carry it alone.

    A lyric fact may state what a speaker said about the apparatus. Recording the
    apparatus rule *itself* as authoritative lyric is the collapse the design
    forbids, and it surfaces as the same testimony-scope violation.
    """

    codes = _canon_codes(
        _lyric_fact(
            canon_id="CF-MECHANISM-001",
            statement="The apparatus was bidirectional from the first winter.",
            truth_scope=AUTHORITATIVE_SCOPE,
        )
    )
    assert codes != ()


# ---------------------------------------------------------------------------
# DEC-007: distribution with both origin accounts unresolved
# ---------------------------------------------------------------------------


def test_both_origin_accounts_stay_unresolved() -> None:
    """`DEC-007`: the distribution record binds while its origin stays open.

    An unresolved reveal carries no owner and no reader release window, because
    scheduling a release would be a decision the design has not made.
    """

    accounts = [
        nf.reveal(
            reveal_id="REV-DEC-007-{0:03d}".format(number),
            fact_id="FACT-DEC-007-{0:03d}".format(number),
            truth_status="unresolved",
        )
        for number in (1, 2)
    ]
    assert _reveal_codes(*accounts) == ()


@pytest.mark.parametrize(
    "field,value", (("reveal_owner", "CHAR-001"), ("reader_release_chapter", 70))
)
def test_an_unresolved_account_cannot_be_scheduled(field: str, value: Any) -> None:
    """A causal-linkage record has no reveal owner and no release window."""

    codes = _reveal_codes(
        nf.reveal(
            reveal_id="REV-DEC-007-SCHEDULED",
            fact_id="FACT-DEC-007-SCHEDULED",
            truth_status="unresolved",
            **{field: value}
        )
    )
    assert "REVEAL_UNRESOLVED_RELEASE_SCHEDULED" in codes, (field, codes)


def test_a_truth_status_outside_the_fixed_three_is_rejected() -> None:
    """`confirmed`, `character-belief`, `unresolved` -- there is no `verified`."""

    codes = _reveal_codes(
        nf.reveal(
            reveal_id="REV-BAD-STATUS",
            fact_id="FACT-BAD-STATUS",
            truth_status="verified",
        )
    )
    assert "REVEAL_TRUTH_STATUS_UNKNOWN" in codes, codes


def test_provenance_is_never_recorded_as_objective_truth() -> None:
    """A refused provenance confirmation stays refused.

    `confirmed` is available for facts the story settles. Applying it to the
    provenance question would close a question the design keeps open, so the
    record that stands is `unresolved` with no scheduled release.
    """

    open_question = nf.reveal(
        reveal_id="REV-PROVENANCE",
        fact_id="FACT-PROVENANCE",
        truth_status="unresolved",
    )
    assert _reveal_codes(open_question) == ()
    scheduled = nf.reveal(
        reveal_id="REV-PROVENANCE",
        fact_id="FACT-PROVENANCE",
        truth_status="unresolved",
        reader_release_chapter=128,
    )
    assert _reveal_codes(scheduled) != ()


# ---------------------------------------------------------------------------
# DEC-005 and DEC-012: extension records, and the restraint around them
# ---------------------------------------------------------------------------


def test_an_approved_extension_with_a_resolvable_authority_is_accepted() -> None:
    """A Novel_Extension names the decision it rests on."""

    assert _extension_codes(nf.novel_extension(extension_id="EXT-TRUST-001")) == ()


def test_an_extension_without_an_authority_reference_is_rejected() -> None:
    """An extension with no authority is an assertion, not an extension."""

    codes = _extension_codes(
        nf.novel_extension(extension_id="EXT-TRUST-002", authority_ref=None)
    )
    assert "EXTENSION_AUTHORITY_REFERENCE_MISSING" in codes, codes


def test_a_retired_extension_names_the_change_that_retired_it() -> None:
    """Retirement is an event with a record, not a quiet deletion."""

    codes = _extension_codes(
        nf.novel_extension(extension_id="EXT-TRUST-003", state="retired")
    )
    assert "EXTENSION_SUPERSEDING_CHANGE_MISSING" in codes, codes

    assert (
        _extension_codes(
            nf.novel_extension(
                extension_id="EXT-TRUST-004",
                state="retired",
                superseding_arc_change_id="AC-FIXTURE-001",
            )
        )
        == ()
    )


@pytest.mark.parametrize("state", ("provisional", "approved", "retired"))
def test_the_three_extension_states_are_accepted(state: str) -> None:
    """`provisional`, `approved`, `retired` -- and nothing else."""

    options: Dict[str, Any] = {"extension_id": "EXT-STATE-001", "state": state}
    if state == "retired":
        options["superseding_arc_change_id"] = "AC-FIXTURE-001"
    assert _extension_codes(nf.novel_extension(**options)) == ()


def test_a_state_outside_the_three_is_rejected() -> None:
    """`superseded` is not a state the design defines."""

    codes = _extension_codes(
        nf.novel_extension(extension_id="EXT-STATE-002", state="superseded")
    )
    assert "EXTENSION_STATE_UNKNOWN" in codes, codes


def test_an_extension_kind_outside_the_vocabulary_is_rejected() -> None:
    """The kinds are a closed list, so a plausible-looking coinage is rejected."""

    codes = _extension_codes(
        nf.novel_extension(
            extension_id="EXT-KIND-001", extension_kind="mechanism-limit"
        )
    )
    assert "EXTENSION_KIND_UNKNOWN" in codes, codes


def test_the_heritage_base_stays_unspecified() -> None:
    """`DEC-012`: the heritage base is unspecified by the author.

    The checker has no schema field for a heritage base, and that absence is the
    enforcement: there is nothing for a filled base to be written into. Inferring
    linguistic, geographic, religious, ethnic, or political particulars from a
    name is a reading, and a reading is an `EditorialFinding`.
    """

    extension = nf.character_name_extension(
        character_id="CHAR-005", selected_name="Fixture Five"
    )
    assert "heritage_base" not in extension, sorted(extension)
    assert _extension_codes(extension) == ()


@pytest.mark.parametrize(
    "selected_name",
    ("Nia", "nia", "NIA", "Nia Okonkwo", "Níà", "  Nia  "),
)
def test_name_wording_and_capitalization_draw_no_diagnostic(
    selected_name: str,
) -> None:
    """Requirement 12.11: a name variant with a stable ID is not a pass/fail matter.

    Every variant here keeps the same `CHAR-005` identity. Which spelling reads
    best is a craft question; the checker's only interest is that the identifier
    still resolves. If any of these drew a diagnostic the checker would be
    choosing names, which Requirement 12.11 reserves for the author.
    """

    extension = nf.character_name_extension(
        character_id="CHAR-005", selected_name=selected_name
    )
    assert _extension_codes(extension) == ()


def test_a_name_extension_still_needs_a_resolvable_identity() -> None:
    """Restraint about wording is not indifference about identity.

    The wording is the author's. The `CHAR-` reference is bookkeeping, and
    bookkeeping is exactly what the checker is for.
    """

    extension = nf.character_name_extension(
        character_id="CHAR-005", selected_name="Fixture Five", authority_ref=None
    )
    assert _extension_codes(extension) != ()


# ---------------------------------------------------------------------------
# Restraint: prose-level DEC claims the checker cannot see
# ---------------------------------------------------------------------------


def test_prose_level_decision_claims_draw_no_diagnostic() -> None:
    """Structurally valid extensions stay silent whatever their prose asserts.

    Each `fact` below states something the design rejects: a contradictory
    geography, a fully open adjudicating inquiry, a hidden one-time release model,
    provenance as objective truth. None of it is machine-checkable -- the records
    are well formed and their references resolve, so the checker has nothing to
    report. Catching these is a human reading task, and recording that reading is
    what an `EditorialFinding` is for.
    """

    claims = (
        "The county sits both inside and outside the same boundary.",
        "The inquiry adjudicates every holding it reviews.",
        "The release model is hidden and happens exactly once.",
        "The provenance is established as objective fact.",
        "The coinage predates the Discovery it is named for.",
    )
    extensions = [
        nf.novel_extension(
            extension_id="EXT-PROSE-{0:03d}".format(number), fact=claim
        )
        for number, claim in enumerate(claims, start=1)
    ]
    assert _extension_codes(*extensions) == ()


def test_the_checker_reports_no_diagnostic_for_the_plan_of_record() -> None:
    """The default record set is clean, so any diagnostic above is the injected one.

    Without this the rejection tests are weaker than they look: a probe that
    always reports something would pass them for the wrong reason.
    """

    index, diagnostics = nf.record_index_with_diagnostics()
    assert diagnostics == (), [item.code for item in diagnostics]
    assert checker.check_canon_facts(index) == ()
    assert checker.check_novel_extensions(index) == ()
    assert checker.check_reveals(index) == ()
