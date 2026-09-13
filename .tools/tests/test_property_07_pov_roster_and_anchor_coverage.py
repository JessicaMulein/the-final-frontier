"""Principal property test for design Property 7.

Property 7: Human POV roster and Anchor coverage

Validates: Requirements 11.7
Related requirements: 4.1, 4.2, 4.8-4.10, 8.8, 15.2, 15.3.

Owning task: 8.16. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 7: Human POV roster and Anchor
coverage

What is being proved
--------------------
* the roster holds three to five human POVProfiles (4.1, 11.7);
* every profile's `entity_type` is `human`, so no Foreign_Signal, adversary,
  archive, simulation, or group-mind viewpoint enters the roster (4.2, 8.8);
* exactly one profile is the Anchor, and that Anchor holds chapters in all four
  movements (4.8, 4.9);
* the provisional per-POV load vector is the 56/32/33/7 multiset (15.3).

Two negative claims matter as much as the positive ones.

Coverage is a whole-book fact, so it is only evaluated when the caller supplies
the observed per-POV movement map. A batch legitimately contains a single
movement, and reporting an Anchor as uncovered there would make a local gate fail
for something it cannot see — the separation Property 12 protects.

Name choice and capitalization are excluded from pass or fail by Requirement
12.11, so the load vector is asserted as a multiset of totals rather than as an
assignment of numbers to named characters. Non-viewpoint Character IDs from the
registry must not count against the roster either.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 7: Human POV roster and Anchor coverage"
OWNING_TASK = "8.16"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

ROSTER_MINIMUM = 3
ROSTER_MAXIMUM = 5
NON_HUMAN_ENTITY_TYPES: Tuple[str, ...] = (
    "foreign-signal",
    "adversary",
    "archive",
    "simulation",
    "group-mind",
    "institution",
)


def _profiles(
    count: int,
    *,
    anchors: Optional[Sequence[int]] = None,
    loads: Optional[Mapping[int, Mapping[str, int]]] = None,
) -> List[Dict[str, Any]]:
    """A roster of `count` human profiles, one of them the Anchor by default."""

    anchor_positions = frozenset(anchors if anchors is not None else (0,))
    built: List[Dict[str, Any]] = []
    for position in range(count):
        built.append(
            nf.pov_profile(
                character_id="CHAR-{0:03d}".format(position + 1),
                pov_id="POV-GEN-{0:03d}".format(position + 1),
                selected_name="Fixture {0}".format(position + 1),
                anchor=position in anchor_positions,
                voice_brief_id="VOICE-GEN-{0:03d}".format(position + 1),
                provisional_load=(loads or {}).get(position),
            )
        )
    return built


def _codes(
    profiles: Sequence[Mapping[str, Any]],
    *,
    chapter_movements: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    """Roster diagnostics through the checker's own gate."""

    index = nf.record_index(supporting=False, POVProfile=list(profiles))
    diagnostics = checker.check_pov_roster(
        index, chapter_movements=chapter_movements
    )
    return tuple(sorted({item.code for item in diagnostics}))


def _full_coverage(profiles: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Every profile holding a chapter in every movement it declares."""

    return {
        str(profile["pov_id"]): frozenset(profile["movement_coverage"])
        for profile in profiles
    }


# Requirement 4.1 sets the roster *size* range and Requirement 15.3 pins the
# current plan's *load vector*. They are separate rules over the same records, so
# a generated roster of three or five profiles satisfies the first and cannot
# satisfy the second. Each assertion below therefore names the rule it is about
# rather than demanding total silence, which would conflate the two.
LOAD_VECTOR_CODES = frozenset(
    {
        "POV_PROVISIONAL_LOAD_MALFORMED",
        "POV_PROVISIONAL_LOAD_TOTAL",
        "POV_PROVISIONAL_LOAD_VECTOR",
    }
)


def _roster_codes(
    profiles: Sequence[Mapping[str, Any]],
    *,
    chapter_movements: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    """Roster diagnostics with the load-vector rule set aside."""

    return tuple(
        code
        for code in _codes(profiles, chapter_movements=chapter_movements)
        if code not in LOAD_VECTOR_CODES
    )


@PROPERTY_SETTINGS
@given(st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM))
def test_a_roster_of_three_to_five_humans_is_accepted(count):
    """Requirements 4.1 and 11.7: three, four, or five human viewpoints."""

    profiles = _profiles(count)
    assert _roster_codes(profiles, chapter_movements=_full_coverage(profiles)) == ()


def test_the_plan_of_record_roster_is_completely_clean():
    """The design's own four-POV roster satisfies the size *and* vector rules.

    This is the one case where nothing is set aside, so it pins down that the two
    rules are jointly satisfiable and that the fixture realizes the actual plan.
    """

    profiles = [
        nf.pov_profile(
            character_id=nf.MANUSCRIPT_POV_CHARACTERS[pov_id],
            pov_id=pov_id,
            selected_name="Fixture {0}".format(pov_id),
            anchor=pov_id == nf.MANUSCRIPT_ANCHOR_POV,
            voice_brief_id="VOICE-{0}".format(pov_id),
            movement_coverage=[
                movement
                for movement in nf.MOVEMENTS
                if int(load.get(movement, 0)) > 0
            ],
            provisional_load=load,
        )
        for pov_id, load in nf.MANUSCRIPT_POV_LOAD.items()
    ]
    assert _codes(profiles, chapter_movements=_full_coverage(profiles)) == ()


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=12))
def test_a_roster_outside_three_to_five_is_reported(count):
    """The bounds are inclusive on both ends, so 2 and 6 fail and 3 and 5 pass."""

    profiles = _profiles(count)
    codes = _roster_codes(profiles, chapter_movements=_full_coverage(profiles))
    inside = ROSTER_MINIMUM <= count <= ROSTER_MAXIMUM
    assert ("POV_ROSTER_SIZE" in codes) == (not inside), (count, codes)


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM),
    st.sampled_from(list(NON_HUMAN_ENTITY_TYPES)),
    st.integers(min_value=0, max_value=ROSTER_MAXIMUM - 1),
)
def test_any_non_human_viewpoint_is_refused(count, entity_type, position):
    """Requirements 4.2 and 8.8: the roster is human viewpoints only.

    A Foreign_Signal, adversary, archive, simulation, or group-mind viewpoint is
    refused wherever it sits in the roster, not only in the first slot.
    """

    profiles = _profiles(count)
    index = position % count
    profiles[index] = dict(profiles[index], entity_type=entity_type)
    codes = _roster_codes(profiles, chapter_movements=_full_coverage(profiles))
    assert "POV_ENTITY_TYPE" in codes, (entity_type, index, codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM))
def test_a_roster_with_no_anchor_is_reported(count):
    """Requirement 4.8: exactly one Anchor, so zero is not a valid roster."""

    profiles = _profiles(count, anchors=())
    codes = _roster_codes(profiles, chapter_movements=_full_coverage(profiles))
    assert "POV_ANCHOR_COUNT" in codes, codes


@PROPERTY_SETTINGS
@given(st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM))
def test_a_roster_with_two_anchors_is_reported(count):
    """Requirement 4.8: exactly one Anchor, so two is not a valid roster either."""

    profiles = _profiles(count, anchors=(0, 1))
    codes = _roster_codes(profiles, chapter_movements=_full_coverage(profiles))
    assert "POV_ANCHOR_COUNT" in codes, codes


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM),
    st.sampled_from(list(nf.MOVEMENTS)),
)
def test_an_anchor_missing_a_movement_is_reported(count, absent):
    """Requirement 4.9: the Anchor holds chapters in all four movements."""

    profiles = _profiles(count)
    coverage = _full_coverage(profiles)
    anchor_id = str(profiles[0]["pov_id"])
    coverage[anchor_id] = frozenset(
        movement for movement in nf.MOVEMENTS if movement != absent
    )
    profiles[0] = dict(profiles[0], movement_coverage=sorted(coverage[anchor_id]))
    codes = _roster_codes(profiles, chapter_movements=coverage)
    assert "ANCHOR_MOVEMENT_COVERAGE" in codes, (absent, codes)


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM),
    st.sampled_from(list(nf.MOVEMENTS)),
)
def test_coverage_is_not_judged_without_the_whole_book_view(count, absent):
    """Requirement 4.9 is a whole-book fact, so a partial view stays silent.

    A batch containing one movement would otherwise report its own Anchor as
    uncovered, which is a local gate failing for a global reason.
    """

    profiles = _profiles(count)
    profiles[0] = dict(
        profiles[0],
        movement_coverage=[m for m in nf.MOVEMENTS if m != absent],
    )
    codes = _roster_codes(profiles, chapter_movements=None)
    assert "ANCHOR_MOVEMENT_COVERAGE" not in codes, codes
    assert "POV_MOVEMENT_COVERAGE_DISAGREEMENT" not in codes, codes


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=ROSTER_MINIMUM, max_value=ROSTER_MAXIMUM),
    st.sampled_from(list(nf.MOVEMENTS)),
)
def test_declared_coverage_must_match_the_observed_chapters(count, extra):
    """A profile claiming a movement it holds no chapter in is a disagreement.

    Declared coverage is a claim about the manuscript; when the manuscript is all
    there, the claim is checkable, and an unbacked one is reported.
    """

    profiles = _profiles(count)
    coverage = _full_coverage(profiles)
    target = str(profiles[-1]["pov_id"])
    coverage[target] = frozenset(
        movement for movement in nf.MOVEMENTS if movement != extra
    )
    codes = _roster_codes(profiles, chapter_movements=coverage)
    assert "POV_MOVEMENT_COVERAGE_DISAGREEMENT" in codes, (extra, codes)


# ---------------------------------------------------------------------------
# The provisional load vector
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.load_vector_variants())
def test_the_provisional_load_vector_is_a_multiset_not_an_assignment(variant):
    """Requirement 15.3 fixes 56/32/33/7; Requirement 12.11 frees the names.

    Permuting the totals across POV_IDs must stay a nonviolation, because which
    selected name carries which number is the author's choice and not a
    checkable fact.
    """

    profiles = [
        nf.pov_profile(
            character_id="CHAR-{0:03d}".format(position + 1),
            pov_id=pov_id,
            selected_name="Fixture {0}".format(position + 1),
            anchor=position == 0,
            voice_brief_id="VOICE-GEN-{0:03d}".format(position + 1),
            movement_coverage=[
                movement
                for movement in nf.MOVEMENTS
                if int(load.get(movement, 0)) > 0
            ],
            provisional_load=load,
        )
        for position, (pov_id, load) in enumerate(variant.payload.items())
    ]
    codes = _codes(profiles, chapter_movements=_full_coverage(profiles))
    vector_codes = {
        code for code in codes if code.startswith("POV_PROVISIONAL_LOAD")
    }
    if variant.valid:
        assert vector_codes == set(), "{0} drew {1}".format(variant, sorted(codes))
    else:
        assert vector_codes, "{0} drew {1}".format(variant, sorted(codes))


@PROPERTY_SETTINGS
@given(ns.name_variants())
def test_a_selected_name_spelling_is_never_a_violation(variant):
    """Requirement 12.11: name choice and capitalization are outside pass/fail."""

    profiles = _profiles(ROSTER_MINIMUM)
    profiles[0] = dict(
        profiles[0],
        selected_name=variant.payload["selected_name"],
        aliases=list(variant.payload["aliases"]),
    )
    assert _roster_codes(profiles, chapter_movements=_full_coverage(profiles)) == ()
