"""Reserved module for design Property 1.

Property 1: Chapter plan and file bijection

Validates: Requirements 11.3
Related requirements: 1.2, 1.3, 9.4, 12.2.

Owning task: 8.10 "Write the principal property test for chapter plan/file
bijection". Reserved by task 7.1 so the property has exactly one principal test
and so an unimplemented property reads as an honest skip instead of as coverage.

The principal test must use Hypothesis with at least 100 generated examples, tag
itself `Feature: the-final-frontier-novel, Property 1: Chapter plan and file
bijection`, build fixtures from `novel_fixtures`, and assert against the global
chapter-plan integrity gate rather than against a fixture helper.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 1: Chapter plan and file bijection"
OWNING_TASK = "8.10"


@pytest.mark.skip(
    reason="Property 1 principal test is reserved for task 8.10 and not implemented yet."
)
def test_chapter_plan_and_file_bijection():
    """Outline sequences are exactly 1..N and map one-to-one onto Chapter_Files."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.10 implements " + PROPERTY + "."
    )
