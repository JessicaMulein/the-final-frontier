"""Principal property test for design Property 15.

Property 15: Finalization requires both independent gates

Validates: Requirements 11.11
Related requirements: 11.10.

Owning task: 8.24. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 15: Finalization requires both
independent gates

What is being proved
--------------------
`final` status requires the Manuscript_Global_Gate *and* the final Editorial_Gate
to both pass. The two are independent in both directions, which is the entire
point of having two of them:

* an objective pass cannot substitute for editorial approval. Every structural
  rule can be satisfied by a manuscript that is not worth reading, and no amount
  of green output is a judgment about the writing;
* editorial approval cannot override an objective violation or an incomplete
  prerequisite. A reader's enthusiasm does not make a broken continuity record
  consistent.

The full truth table of both results is generated, so neither direction can be
satisfied by a check that looks at only one gate. The missing side is reported by
name rather than as one undifferentiated failure, because the remedies have
nothing in common: one is a code-and-records repair, the other is a person
reading the book.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 15: Finalization requires both independent gates"
OWNING_TASK = "8.24"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# The two gates Requirement 11.11 requires, and the verdicts each may record.
OBJECTIVE_GATE = "manuscript-global"
EDITORIAL_GATE = "editorial"
RESULTS: Tuple[str, ...] = ("pass", "revision", "incomplete")

# Exit statuses that agree with each result, so a generated gate is internally
# consistent and the only thing under test is the *combination* of the two.
EXIT_FOR_RESULT: Mapping[str, Optional[int]] = {
    "pass": 0,
    "revision": 1,
    "incomplete": 2,
}


def _gates(
    objective: Optional[str], editorial: Optional[str]
) -> List[Dict[str, Any]]:
    """One GateResult per present gate, each internally consistent."""

    records: List[Dict[str, Any]] = []
    if objective is not None:
        records.append(
            nf.gate_result(
                gate_result_id="GATE-OBJECTIVE-001",
                gate_type=OBJECTIVE_GATE,
                result=objective,
                checker_exit_status=EXIT_FOR_RESULT[objective],
            )
        )
    if editorial is not None:
        records.append(
            nf.editorial_gate_result(
                gate_result_id="GATE-EDITORIAL-001", result=editorial
            )
        )
    return records


def _codes(
    objective: Optional[str], editorial: Optional[str]
) -> Tuple[str, ...]:
    """Finalization diagnostics for one combination of gate results."""

    index = nf.record_index(
        supporting=False, GateResult=_gates(objective, editorial)
    )
    return tuple(
        sorted({item.code for item in checker.check_finalization_gates(index)})
    )


@PROPERTY_SETTINGS
@given(st.sampled_from(RESULTS), st.sampled_from(RESULTS))
def test_only_two_passes_permit_finalization(objective, editorial):
    """Requirement 11.11's whole truth table, both gates present.

    The expected verdict is recomputed from the requirement, so this catches a
    check that accepted one pass as well as one that rejected two.
    """

    codes = _codes(objective, editorial)
    both_passed = objective == "pass" and editorial == "pass"
    assert (codes == ()) == both_passed, (objective, editorial, codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(RESULTS))
def test_an_objective_pass_alone_is_not_enough(objective):
    """An absent editorial gate is a missing judgment, not an implied approval.

    Silence from the editorial side must never read as approval, because nobody
    said anything. That is what makes the gate a gate.
    """

    codes = _codes(objective, None)
    assert codes != (), objective
    assert "FINALIZATION_GATE_MISSING" in codes, codes


@PROPERTY_SETTINGS
@given(st.sampled_from(RESULTS))
def test_an_editorial_pass_alone_is_not_enough(editorial):
    """Editorial approval cannot stand in for a checker that never ran."""

    codes = _codes(None, editorial)
    assert codes != (), editorial
    assert "FINALIZATION_GATE_MISSING" in codes, codes


@PROPERTY_SETTINGS
@given(st.sampled_from(["revision", "incomplete"]))
def test_editorial_approval_cannot_override_an_objective_failure(objective):
    """A reader's approval does not repair a broken record or a missing input.

    Both non-passing objective results are generated, because an *incomplete*
    prerequisite is a different situation from a violation and neither may be
    waived by the editorial side.
    """

    assert _codes(objective, "pass") != (), objective


@PROPERTY_SETTINGS
@given(st.sampled_from(["revision", "incomplete"]))
def test_an_objective_pass_cannot_override_an_editorial_refusal(editorial):
    """Requirement 11.11 in the direction that matters most for this project.

    Every objective rule in this checker can be satisfied by prose no one would
    want to read. A green run is a statement about bookkeeping, and the design
    keeps craft where it belongs: with a person.
    """

    assert _codes("pass", editorial) != (), editorial


@PROPERTY_SETTINGS
@given(st.just(None))
def test_neither_gate_present_is_reported_as_both_missing(_unused):
    """An empty gate log finalizes nothing, and says so about both sides."""

    codes = _codes(None, None)
    assert "FINALIZATION_GATE_MISSING" in codes, codes


@PROPERTY_SETTINGS
@given(ns.gates())
def test_a_gate_record_must_agree_with_its_own_exit_status(variant):
    """Requirement 11.10: a gate that contradicts its checker run proves nothing.

    Independence is only meaningful if each record is honest about what happened,
    so a `pass` recorded next to a failing exit status is itself a violation.
    """

    index = nf.record_index(supporting=False, GateResult=[variant.payload])
    diagnostics = checker.check_gate_results(index)
    codes = sorted({item.code for item in diagnostics})
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert not codes, "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(RESULTS), st.sampled_from(RESULTS))
def test_the_missing_side_is_named_rather_than_merged(objective, editorial):
    """The report distinguishes which gate is absent, because the fixes differ."""

    for present_objective, present_editorial in (
        (objective, None),
        (None, editorial),
    ):
        index = nf.record_index(
            supporting=False,
            GateResult=_gates(present_objective, present_editorial),
        )
        diagnostics = checker.check_finalization_gates(index)
        missing = [
            item
            for item in diagnostics
            if item.code == "FINALIZATION_GATE_MISSING"
        ]
        assert missing, (present_objective, present_editorial)
        absent_gate = EDITORIAL_GATE if present_editorial is None else OBJECTIVE_GATE
        assert any(
            absent_gate in str(item.item) or absent_gate in str(item.expected)
            for item in missing
        ), [(item.item, item.expected) for item in missing]
