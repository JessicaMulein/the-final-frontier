"""Versioned exact word-sequence transcript verification."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

from .config import NORMALIZATION_ID
from .errors import InputError
from .util import sha256_text

TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "＇": "'"})


@dataclass(frozen=True)
class VerificationResult:
    normalization: str
    passed: bool
    transcript_is_verbatim_prefix: bool
    coverage_ratio: float
    expected_sha256: str
    transcript_sha256: str
    expected_token_count: int
    transcript_token_count: int
    first_difference: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalized_tokens(value: str, normalization: str = NORMALIZATION_ID) -> tuple[str, ...]:
    if normalization != NORMALIZATION_ID:
        raise InputError(f"Unsupported transcript normalization: {normalization}")
    normalized = unicodedata.normalize("NFC", value).translate(APOSTROPHES).casefold()
    return tuple(TOKEN.findall(normalized))


def compare_transcript(expected: str, transcript: str, normalization: str = NORMALIZATION_ID) -> VerificationResult:
    expected_tokens = normalized_tokens(expected, normalization)
    transcript_tokens = normalized_tokens(transcript, normalization)
    if not expected_tokens:
        raise InputError("Expected spoken text has no verifiable word tokens")
    if not transcript_tokens:
        raise InputError("Nova returned no verifiable FINAL transcript tokens")

    first_difference: dict[str, object] | None = None
    if expected_tokens != transcript_tokens:
        matcher = SequenceMatcher(a=expected_tokens, b=transcript_tokens, autojunk=False)
        opcode = next((item for item in matcher.get_opcodes() if item[0] != "equal"), None)
        if opcode is not None:
            tag, expected_start, expected_end, actual_start, actual_end = opcode
            first_difference = {
                "operation": tag,
                "expected_range": [expected_start, expected_end],
                "transcript_range": [actual_start, actual_end],
                "expected": list(expected_tokens[expected_start:expected_end]),
                "transcript": list(transcript_tokens[actual_start:actual_end]),
                "expected_context": list(expected_tokens[max(0, expected_start - 5) : expected_end + 5]),
                "transcript_context": list(transcript_tokens[max(0, actual_start - 5) : actual_end + 5]),
            }

    return VerificationResult(
        normalization=normalization,
        passed=expected_tokens == transcript_tokens,
        transcript_is_verbatim_prefix=(
            len(transcript_tokens) <= len(expected_tokens)
            and expected_tokens[: len(transcript_tokens)] == transcript_tokens
        ),
        coverage_ratio=round(len(transcript_tokens) / len(expected_tokens), 4),
        expected_sha256=sha256_text(expected),
        transcript_sha256=sha256_text(transcript),
        expected_token_count=len(expected_tokens),
        transcript_token_count=len(transcript_tokens),
        first_difference=first_difference,
    )
