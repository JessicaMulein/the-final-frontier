"""Principal property test for design Property 4.

Property 4: Prose word-count round trip

Validates: Requirements 9.7
Related requirements: 10.3, 12.3.

Owning task: 8.13. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 4: Prose word-count round trip

What is being proved
--------------------
The observed Prose_Word count of a body is exactly
`len(normalized_prose_body.split())`, where normalization is Unicode NFC plus LF
line endings and nothing else. The expected value is computed here, in the test,
straight from that definition.

It is deliberately *not* compared against `novel_fixtures.count_prose_words`.
That helper is a fixture-side restatement of the same rule, so comparing the two
would only prove two copies of one idea agree, which is how a counting bug
survives a green suite. The generated bodies include the cases where a naive
implementation drifts: empty, whitespace-only, punctuation-only, CRLF and CR line
endings, runs of blank lines, non-breaking spaces, combining marks that NFC
composes, and text that changes *length* but not word count under normalization.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 4: Prose word-count round trip"
OWNING_TASK = "8.13"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# Bodies chosen to break a naive count. Each entry is raw text, exactly as it
# would sit in a Chapter_File before normalization.
AWKWARD_BODIES: Tuple[str, ...] = (
    "",
    "\n",
    "   \n\t\n  \n",
    "...\n",
    "--- ... !?\n",
    "one\r\ntwo\r\nthree\r\n",
    "one\rtwo\rthree\r",
    "one\n\n\n\n\ntwo\n",
    "one \t  two \t three\n",
    "  leading and trailing  \n",
    "caf\u00e9 na\u00efve\n",
    "cafe\u0301 nai\u0308ve\n",
    "\u00a0one\u00a0two\u00a0\n",
    "one\u2014two\n",
    "\u201cquoted\u201d words\n",
    "a\n",
    "\u4e00 \u4e8c \u4e09\n",
    "word" + "\n" * 40 + "word\n",
    "one two\u2028three\n",
    "hyphen-ated compound-word\n",
)


def _expected(raw: str) -> int:
    """The rule itself: split the normalized body on whitespace and count.

    This is the specification restated in one line, with no shared code path
    into the checker, which is the whole point of the property.
    """

    normalized = unicodedata.normalize("NFC", raw).replace("\r\n", "\n").replace(
        "\r", "\n"
    )
    return len(normalized.split())


@PROPERTY_SETTINGS
@given(st.sampled_from(AWKWARD_BODIES))
def test_the_awkward_bodies_round_trip(raw):
    """Empty, punctuation-only, mixed line endings, and Unicode all count exactly."""

    observed = checker.count_prose_words(checker.normalize_prose(raw))
    assert observed == _expected(raw), repr(raw)


@PROPERTY_SETTINGS
@given(st.text(max_size=400))
def test_arbitrary_text_round_trips(raw):
    """Requirement 9.7 holds for any text, not only for prose-shaped text."""

    observed = checker.count_prose_words(checker.normalize_prose(raw))
    assert observed == _expected(raw), repr(raw)


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs", "Zs", "Zl", "Zp")),
            min_size=1,
            max_size=8,
        ),
        min_size=0,
        max_size=60,
    ),
    st.sampled_from(["\n", "\r\n", "\r", " \n", "\n\n"]),
)
def test_the_separator_never_changes_the_count(words, separator):
    """Normalization folds line endings, so CRLF and CR count like LF.

    A body that differs from another only in its line endings must produce the
    same count, because the two are the same prose. This is the invariant that
    catches a counter reading raw bytes instead of normalized text.
    """

    raw = separator.join(words)
    observed = checker.count_prose_words(checker.normalize_prose(raw))
    assert observed == len(words)
    assert observed == _expected(raw)


@PROPERTY_SETTINGS
@given(ns.prose_word_counts(minimum=1, maximum=2500))
def test_a_generated_body_of_n_words_is_counted_as_n(words):
    """The fixture builds a body of a requested size; the checker must agree.

    The claim being checked is the checker's, not the fixture's: the expected
    value is recomputed from the normalized text rather than taken from the
    number that was requested.
    """

    body = nf.prose_of_length(words)
    observed = checker.count_prose_words(checker.normalize_prose(body))
    assert observed == _expected(body)
    assert observed == words


@PROPERTY_SETTINGS
@given(ns.prose_word_counts(minimum=2, maximum=2500))
def test_a_header_declaring_the_wrong_count_is_reported(words):
    """Requirement 9.7: the declared `words` value must equal the observed count.

    The lie is one word *low* rather than one high, so the declared value stays
    inside the Hard_Chapter_Maximum at every drawn size and the only thing wrong
    with the header is the disagreement being tested.
    """

    body = nf.prose_of_length(words)
    truthful = nf.chapter_header(prose=body)
    lying = nf.chapter_header(prose=body, words=words - 1)

    assert _length_codes(truthful, body) == ()
    assert _length_codes(lying, body) != ()


def _length_codes(header: Any, body: str) -> Tuple[str, ...]:
    """Run one header and body through the checker's own length gate.

    Parsed the same way a real Chapter_File is, so the declared-versus-observed
    comparison is the one the gate performs rather than one this test arranges.
    """

    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, body),
        relative_path=nf.chapter_relative_path("discovery_part", 1, "probe"),
    )
    report = checker.chapter_length_report(document)
    diagnostics = tuple(document.diagnostics) + checker.check_chapter_length(report)
    return tuple(sorted({item.code for item in diagnostics}))
