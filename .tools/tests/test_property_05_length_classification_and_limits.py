"""Principal property test for design Property 5.

Property 5: Length classification and limits

Validates: Requirements 2.8
Related requirements: 2.9-2.11, 12.3.

Owning task: 8.14. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 5: Length classification and limits

What is being proved
--------------------
Four separate rules, all decided from the observed Prose_Word count:

* the three bands, `microchapter` below 700, `normal` at 700 through 1,600, and
  `long-outlier` at 1,601 through the Hard_Chapter_Maximum;
* the Hard_Chapter_Maximum itself, above which no class applies at all;
* the nonblank `outlier_purpose` an outlier chapter must carry;
* the 80 percent normal share over the whole book, in exact integer arithmetic.

The expected band is computed here from the design's table, not read back from
`novel_fixtures.derive_length_class`. That helper exists only so a fixture can
emit a self-consistent header, and asserting the checker against it would compare
two restatements of one rule instead of testing either.

The generated counts include every band boundary. An off-by-one at 699/700 or
1600/1601 is exactly the kind of error a uniformly random count almost never
finds, so those edges are drawn deliberately.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 5: Length classification and limits"
OWNING_TASK = "8.14"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

HARD_CHAPTER_MAXIMUM = 2500


def _expected_class(words: int) -> Optional[str]:
    """The design's Length_Class table, restated.

    `None` above the Hard_Chapter_Maximum, because the design assigns no class
    there rather than stretching `long-outlier` to cover it.
    """

    if words > HARD_CHAPTER_MAXIMUM:
        return None
    if words < 700:
        return "microchapter"
    if words <= 1600:
        return "normal"
    return "long-outlier"


@PROPERTY_SETTINGS
@given(st.integers(min_value=0, max_value=4000))
def test_the_derived_class_matches_the_design_table(words):
    """Requirement 2.9 through 2.11: one band per count, and none past the maximum."""

    assert checker.derive_length_class(words) == _expected_class(words), words


@PROPERTY_SETTINGS
@given(ns.band_boundary_word_counts())
def test_the_band_boundaries_land_on_the_right_side(words):
    """The edges where an off-by-one hides: 699/700, 1600/1601, and the maximum."""

    assert checker.derive_length_class(words) == _expected_class(words), words


@PROPERTY_SETTINGS
@given(ns.length_classes().flatmap(lambda name: st.tuples(st.just(name), ns.words_in_length_class(name))))
def test_a_header_declaring_the_matching_class_is_accepted(pair):
    """A body of N words with the class the table assigns to N draws no diagnostic."""

    length_class, words = pair
    body = nf.prose_of_length(words)
    codes = _length_codes(nf.chapter_header(prose=body, length_class=length_class), body)
    if length_class == _expected_class(words):
        assert codes == (), (length_class, words, codes)
    else:
        assert codes != (), (length_class, words)


@PROPERTY_SETTINGS
@given(ns.length_classes(), ns.length_classes())
def test_a_header_declaring_a_mismatched_class_is_reported(declared, actual):
    """Requirement 12.3: the declared class must equal the derived one."""

    words = ns.LENGTH_CLASS_BANDS[actual][0]
    body = nf.prose_of_length(words)
    codes = _length_codes(nf.chapter_header(prose=body, length_class=declared), body)
    if declared == actual:
        assert codes == (), codes
    else:
        assert codes != (), (declared, actual)


@PROPERTY_SETTINGS
@given(
    st.integers(
        min_value=HARD_CHAPTER_MAXIMUM + 1, max_value=HARD_CHAPTER_MAXIMUM + 400
    ),
    ns.length_classes(),
)
def test_a_body_past_the_hard_maximum_is_always_reported(words, declared):
    """Requirement 2.11: above the maximum there is no valid class to declare.

    Whichever class the header names, the file is still too long, so the
    diagnostic cannot be dodged by relabelling. The header is assembled directly
    rather than through `chapter_header`, because that builder refuses to derive a
    class past the maximum and would raise before the checker ever saw the file.
    """

    body = nf.prose_of_length(words)
    header = {
        "movement": "discovery_part",
        "chapter": 1,
        "pov_id": "POV-MARA",
        "timeline_id": "TL-FIXTURE-001",
        "motif_events": [],
        "hook": "A synthetic fixture hook line.",
        "words": words,
        "length_class": declared,
        "status": "draft",
    }
    assert _length_codes(header, body) != (), declared


@PROPERTY_SETTINGS
@given(ns.length_classes(), st.sampled_from([None, "", "   ", "\n", "\t"]))
def test_an_outlier_without_a_nonblank_purpose_is_reported(length_class, blank):
    """Requirement 2.10: an outlier declares why, and whitespace is not a reason."""

    words = ns.LENGTH_CLASS_BANDS[length_class][0]
    body = nf.prose_of_length(words)
    header = nf.chapter_header(prose=body, length_class=length_class)
    entry = nf.arc_entry(
        chapter=1,
        movement="discovery_part",
        slug="probe",
        estimated_words=words,
        estimated_length_class=length_class,
        outlier_purpose=blank,
    )
    codes = _length_codes(header, body, arc_entry=entry)
    if length_class in ("microchapter", "long-outlier"):
        assert codes != (), (length_class, repr(blank))
    elif blank is None:
        assert codes == (), (length_class, repr(blank), codes)
    else:
        # A `normal` chapter carrying a purpose at all is the mirror-image fault:
        # the field asserts an outlier the length does not support.
        assert codes != (), (length_class, repr(blank))


@PROPERTY_SETTINGS
@given(ns.length_classes())
def test_a_normal_chapter_carrying_an_outlier_purpose_is_reported(length_class):
    """Requirement 2.10 runs both ways: only an outlier may explain itself."""

    words = ns.LENGTH_CLASS_BANDS[length_class][0]
    body = nf.prose_of_length(words)
    header = nf.chapter_header(prose=body, length_class=length_class)
    entry = nf.arc_entry(
        chapter=1,
        movement="discovery_part",
        slug="probe",
        estimated_words=words,
        estimated_length_class=length_class,
        outlier_purpose="A stated reason for an unusual length.",
    )
    codes = _length_codes(header, body, arc_entry=entry)
    assert (codes == ()) == (length_class != "normal"), (length_class, codes)


@PROPERTY_SETTINGS
@given(ns.normal_share_allocations())
def test_the_normal_share_floor_is_exact_integer_arithmetic(variant):
    """Requirement 2.8: at least 80 percent of final chapters are `normal`.

    The denominator is every final chapter including the outliers, and the
    comparison must not move on a floating-point rounding, so 79/100 fails and
    80/100 passes.
    """

    allocation = variant.payload
    results = tuple(
        _final_chapter_result(index + 1, length_class)
        for index, length_class in enumerate(allocation)
    )
    codes = {item.code for item in checker.check_normal_share(results)}
    if variant.valid:
        assert "NORMAL_SHARE" not in codes, (variant.label, sorted(codes))
    else:
        assert "NORMAL_SHARE" in codes, (variant.label, sorted(codes))


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=200))
def test_the_eighty_percent_boundary_is_decided_without_rounding(total):
    """The exact tipping point: `ceil(0.8 * total)` normal chapters is enough.

    Computed with integer arithmetic here too, so the test does not import the
    rounding behavior it is trying to pin down.
    """

    threshold = -((-80 * total) // 100)
    for normal in (threshold - 1, threshold):
        if normal < 0:
            continue
        allocation = ["normal"] * normal + ["microchapter"] * (total - normal)
        results = tuple(
            _final_chapter_result(index + 1, length_class)
            for index, length_class in enumerate(allocation)
        )
        codes = {item.code for item in checker.check_normal_share(results)}
        assert ("NORMAL_SHARE" in codes) == (normal < threshold), (
            total,
            normal,
            threshold,
            sorted(codes),
        )


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def _length_codes(header: Any, body: str, *, arc_entry: Any = None) -> Tuple[str, ...]:
    """One header and body through the checker's own length gate."""

    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, body),
        relative_path=nf.chapter_relative_path("discovery_part", 1, "probe"),
    )
    entry = None
    if arc_entry is not None:
        entries = _arc_entries([arc_entry])
        entry = entries[0] if entries else None
    report = checker.chapter_length_report(document)
    diagnostics = tuple(document.diagnostics) + checker.check_chapter_length(
        report, arc_entry=entry
    )
    return tuple(sorted({item.code for item in diagnostics}))


def _arc_entries(payloads: Sequence[Any]) -> Tuple[Any, ...]:
    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", payload) for payload in payloads),
    )
    entries, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    return entries


def _final_chapter_result(chapter: int, length_class: str) -> Any:
    """A `final` Chapter_File of the given class, as the share rule sees it.

    Built by parsing a real Chapter_File so the observed class is derived by the
    checker, not asserted by the test. A share computed from *declared* classes
    would let a mislabelled chapter shift the whole-book denominator.
    """

    words = ns.LENGTH_CLASS_BANDS[length_class][0]
    body = nf.prose_of_length(words)
    header = nf.chapter_header(
        chapter=chapter, prose=body, length_class=length_class, status="final"
    )
    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, body),
        relative_path=nf.chapter_relative_path(
            "discovery_part", chapter, "chapter-{0:03d}".format(chapter)
        ),
    )
    return checker.ChapterCheckResult(
        relative_path=document.relative_path,
        document=document,
        length_report=checker.chapter_length_report(document),
        arc_entry=None,
        diagnostics=(),
    )
