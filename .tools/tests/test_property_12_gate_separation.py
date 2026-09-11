"""Reserved module for design Property 12.

Property 12: Chapter-local and manuscript-global gate separation

Validates: Requirements 10.9
Related requirements: 10.1-10.5.

Owning task: 8.21 "Write the principal property test for local/global gate
separation". Reserved by task 7.1.

The principal test must generate one locally valid chapter plus arbitrary global
mutations over at least 100 examples, tagged `Feature:
the-final-frontier-novel, Property 12: Chapter-local and manuscript-global gate
separation`, and prove that Final_Targets, unrelated chapters, whole-book POV
distribution, cross-manuscript motif totals, movement length relations, and
final-ending records never change the Chapter_Local_Gate result, while any local
defect always fails it.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 12: Chapter-local and manuscript-global gate separation"
OWNING_TASK = "8.21"


@pytest.mark.skip(
    reason="Property 12 principal test is reserved for task 8.21 and not implemented yet."
)
def test_chapter_local_and_manuscript_global_gate_separation():
    """Global state never moves a local gate result, and local defects always do."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.21 implements " + PROPERTY + "."
    )
