"""Reserved module for design Property 4.

Property 4: Prose word-count round trip

Validates: Requirements 9.7
Related requirements: 10.3, 12.3.

Owning task: 8.13 "Write the principal property test for prose word-count round
trips". Reserved by task 7.1.

The principal test must generate empty, Unicode, punctuation-only, mixed
line-ending, and whitespace-run bodies over at least 100 examples, tag itself
`Feature: the-final-frontier-novel, Property 4: Prose word-count round trip`,
and compare the checker's observed count against
`len(normalized_prose_body.split())` computed in the test. It must not compare
the checker against `novel_fixtures.count_prose_words`, which is the same
fixture-side restatement and would make the assertion circular.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 4: Prose word-count round trip"
OWNING_TASK = "8.13"


@pytest.mark.skip(
    reason="Property 4 principal test is reserved for task 8.13 and not implemented yet."
)
def test_prose_word_count_round_trip():
    """Observed Prose_Word count excludes header tokens and matches the split length."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.13 implements " + PROPERTY + "."
    )
