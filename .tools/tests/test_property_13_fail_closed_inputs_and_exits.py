"""Reserved module for design Property 13.

Property 13: Fail-closed incomplete inputs and exit status

Validates: Requirements 12.9
Related requirements: 11.1, 11.2, 12.10, 12.14, 12.15.

Owning task: 8.22 "Write the principal property test for fail-closed inputs and
exits". Reserved by task 7.1.

The principal test must generate requested scopes with removed, corrupted, and
unreadable inputs over at least 100 examples, tagged `Feature:
the-final-frontier-novel, Property 13: Fail-closed incomplete inputs and exit
status`, and prove the three-way exit mapping: `2` for incomplete or unreadable
input, `1` for one or more objective violations, and `0` only for a complete
readable scope with zero violations.

`test_minimal_checker.py` already covers the exit-1 and exit-2 paths the current
site-exclusion scope implements; task 8.22 generalizes that to every scope once
tasks 7.2-7.6 and 8.8-8.9 exist.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 13: Fail-closed incomplete inputs and exit status"
OWNING_TASK = "8.22"


@pytest.mark.skip(
    reason="Property 13 principal test is reserved for task 8.22 and not implemented yet."
)
def test_fail_closed_incomplete_inputs_and_exit_status():
    """Incomplete input exits 2, violations exit 1, and only clean scopes exit 0."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.22 implements " + PROPERTY + "."
    )
