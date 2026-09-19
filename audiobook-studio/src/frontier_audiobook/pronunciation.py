"""Declared pronunciation lexicon applied between source text and spoken text.

Amazon Nova 2 Sonic is driven by plain text: this workflow sends no SSML, no
phoneme markup, and no pronunciation lexicon to the service. The only way to
change how a word is spoken is to change the characters the model receives.

Respelling a proper noun directly in the manuscript would be unacceptable, so the
respelling belongs in the one place the pipeline already distinguishes: the
transform between *source text* and *spoken text*. ``markdown_to_spoken`` already
makes these differ (it strips emphasis and inline code), and every source snapshot
already records ``normalized_body_sha256`` and ``spoken_sha256`` separately.

A declared lexicon uses that same seam. The manuscript keeps the correct spelling,
the model receives the respelling, and deterministic fidelity verification still
compares the returned transcript against the spoken text. The mapping becomes
explicit, reviewable configuration instead of a typo nobody can explain.

Matching rules are intentionally strict and boring:

* ``written`` matches only on whole words, never inside a longer word.
* Matching is case-sensitive, because these are proper nouns.
* Longer ``written`` forms are tried first, so a short form cannot shadow a
  longer one that contains it.
* Substitution is a single pass over the source, so replacement text is never
  rewritten by another entry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .errors import InputError

_FORBIDDEN = ("\n", "\r", "\t")


def _clean_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{label} must be nonblank text")
    for character in _FORBIDDEN:
        if character in value:
            raise InputError(f"{label} must not contain control whitespace")
    if value != value.strip():
        raise InputError(f"{label} must not have leading or trailing whitespace")
    return value


@dataclass(frozen=True, slots=True)
class PronunciationEntry:
    """One declared mapping from correct spelling to spoken respelling."""

    written: str
    spoken: str
    note: str | None = None

    def __post_init__(self) -> None:
        _clean_text(self.written, "pronunciation written")
        _clean_text(self.spoken, "pronunciation spoken")
        if self.note is not None:
            _clean_text(self.note, "pronunciation note")
        if self.written == self.spoken:
            raise InputError(
                f"pronunciation entry {self.written!r} must change the spoken form"
            )
        if not re.search(r"\w", self.written):
            raise InputError(
                f"pronunciation written form {self.written!r} must contain a word character"
            )

    def as_json(self) -> dict[str, Any]:
        return {"written": self.written, "spoken": self.spoken, "note": self.note}


@dataclass(frozen=True, slots=True)
class PronunciationLexicon:
    """An ordered, duplicate-free set of declared pronunciation entries."""

    entries: tuple[PronunciationEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not all(
            isinstance(item, PronunciationEntry) for item in self.entries
        ):
            raise InputError("pronunciation lexicon entries must be a tuple of entries")
        written = [item.written for item in self.entries]
        if len(set(written)) != len(written):
            raise InputError("pronunciation lexicon contains duplicate written forms")
        object.__setattr__(
            self,
            "entries",
            tuple(sorted(self.entries, key=lambda item: item.written)),
        )

    def __bool__(self) -> bool:
        return bool(self.entries)

    @property
    def _ordered_for_matching(self) -> tuple[PronunciationEntry, ...]:
        # Longest written form first so a short form cannot shadow a longer one.
        return tuple(
            sorted(self.entries, key=lambda item: (-len(item.written), item.written))
        )

    def apply(self, text: str) -> tuple[str, tuple[str, ...]]:
        """Return ``(spoken_text, applied_written_forms)`` in a single pass."""

        if not isinstance(text, str):
            raise InputError("pronunciation lexicon requires text")
        if not self.entries:
            return text, ()

        ordered = self._ordered_for_matching
        by_written = {item.written: item.spoken for item in ordered}
        pattern = re.compile(
            r"(?<!\w)(?:%s)(?!\w)"
            % "|".join(re.escape(item.written) for item in ordered)
        )
        applied: list[str] = []

        def _replace(match: re.Match[str]) -> str:
            found = match.group(0)
            if found not in applied:
                applied.append(found)
            return by_written[found]

        return pattern.sub(_replace, text), tuple(sorted(applied))

    def as_json(self) -> list[dict[str, Any]]:
        return [item.as_json() for item in self.entries]


EMPTY_LEXICON = PronunciationLexicon()


def parse_pronunciation_entries(
    value: Any,
    label: str = "pronunciations",
) -> PronunciationLexicon:
    """Parse an untrusted list of pronunciation tables with exact keys."""

    if not isinstance(value, list):
        raise InputError(f"{label} must be an array of tables")
    entries: list[PronunciationEntry] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise InputError(f"{label}[{index}] must be a table")
        unknown = sorted(set(item) - {"written", "spoken", "note"})
        missing = sorted({"written", "spoken"} - set(item))
        if missing or unknown:
            raise InputError(
                f"{label}[{index}] keys are invalid; missing={missing}, unknown={unknown}"
            )
        entries.append(
            PronunciationEntry(
                written=_clean_text(item["written"], f"{label}[{index}].written"),
                spoken=_clean_text(item["spoken"], f"{label}[{index}].spoken"),
                note=(
                    None
                    if item.get("note") is None
                    else _clean_text(item["note"], f"{label}[{index}].note")
                ),
            )
        )
    return PronunciationLexicon(tuple(entries))


def describe_applied(
    lexicon: PronunciationLexicon,
    applied: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Describe which declared entries were used, for operator-facing output."""

    by_written = {item.written: item for item in lexicon.entries}
    return tuple(
        by_written[written].as_json() for written in applied if written in by_written
    )
