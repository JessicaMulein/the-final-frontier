"""Reserved module for design Property 5.

Property 5: Length classification and limits

Validates: Requirements 2.8
Related requirements: 2.9-2.11, 12.3.

Owning task: 8.14 "Write the principal property test for length classes and
limits". Reserved by task 7.1.

The principal test must cover the `microchapter`/`normal`/`long-outlier` bands,
the Hard_Chapter_Maximum, the nonblank outlier purpose, and the 80 percent
normal-share rule over at least 100 examples, tagged `Feature:
the-final-frontier-novel, Property 5: Length classification and limits`. It must
assert against the checker's derivation, not against
`novel_fixtures.derive_length_class`, which only exists so a fixture can emit a
self-consistent header.
"""

from __future__ import annotations

import pytest

PROPERTY = "Property 5: Length classification and limits"
OWNING_TASK = "8.14"


@pytest.mark.skip(
    reason="Property 5 principal test is reserved for task 8.14 and not implemented yet."
)
def test_length_classification_and_limits():
    """Length_Class bands, the hard maximum, and the normal share all bind."""

    raise AssertionError(
        "Unreachable placeholder. Task 8.14 implements " + PROPERTY + "."
    )
