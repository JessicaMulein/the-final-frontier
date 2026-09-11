"""Reserved module for design Property 14.

Property 14: Manuscript source exclusion

Validates: Requirements 9.3
Related requirements: 9.2, 11.9, 12.8.

Owning task: 8.23 "Write the principal property test for manuscript source
exclusion". Reserved by task 7.1.

This is the one property whose subject already exists: the
Manuscript_Exclusion_Contract reference collector in `check_novel.py`, covered by
example in `test_site_exclusion.py` and `test_minimal_checker.py`. The generated
principal test is still owed. Task 8.23 must generate workspace trees containing
arbitrary Markdown at or below the resolved manuscript root and arbitrary valid
song folders outside it, over at least 100 examples, tagged `Feature:
the-final-frontier-novel, Property 14: Manuscript source exclusion`, and assert
against the contract's reference implementation, because Site_Build is external
to this workspace. Passing it proves local isolation only, never external
adoption.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 14: Manuscript source exclusion"
OWNING_TASK = "8.23"


@pytest.mark.skip(
    reason="Property 14 principal test is reserved for task 8.23 and not implemented yet."
)
def test_manuscript_source_exclusion():
    """No manuscript path is ever collected, and eligible song sources survive."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.23 implements " + PROPERTY + "."
    )
